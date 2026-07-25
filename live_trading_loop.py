"""
실거래 루프 — decision interval마다 목표 비중을 산출해 브로커에 주문을 낸다.

⚠️ 기본값은 --dry-run(주문 미실행, 로그만 출력)이다. 실제 주문을 내려면
   --live 플래그를 명시해야 하고, 그때도 KIS_LIVE_MODE가 "real"이 아니면
   모의투자 계좌로만 나간다 (broker/kis_client.py 참고).

⚠️ PPOPolicyAdapter는 분봉 임베딩 파이프라인(Phase 2-4: minute_features_colab.ipynb
   → hybrid_model_minute_colab.ipynb → rl_trading_minute_colab.ipynb)이 끝나야
   실제로 쓸 수 있다. 그 전까지는 EqualWeightPolicy로 브로커 연동 자체만 검증할 것.

Colab이 아닌 상시 프로세스로 구동한다 (Mac launchd/cron 또는 별도 서버).
"""

from __future__ import annotations

import argparse
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, time as dtime

from broker.base import BrokerClient, OrderSide
from broker.kis_client import KISBrokerClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("live_trading_loop")

MARKET_OPEN = dtime(9, 0)
MARKET_CLOSE_FOR_ENTRIES = dtime(15, 20)  # 마감 직전 신규 진입 중단


@dataclass
class RiskConfig:
    max_weight_per_ticker: float = 0.3
    daily_loss_limit_pct: float = 0.03  # 이 이상 손실 시 당일 거래 중단


@dataclass
class LoopConfig:
    tickers: list[str]
    decision_interval_sec: int = 1800  # 30분 (분봉 5분 × 6봉)
    dry_run: bool = True
    risk: RiskConfig = field(default_factory=RiskConfig)


class PolicyAdapter(ABC):
    """목표 비중 산출 정책 인터페이스."""

    @abstractmethod
    def target_weights(self, tickers: list[str], broker: BrokerClient) -> dict[str, float]:
        """티커별 목표 비중 (합계 1.0 이하) 반환."""


class EqualWeightPolicy(PolicyAdapter):
    """브로커 연동 자체를 검증하기 위한 더미 정책 — 등가중 배분."""

    def target_weights(self, tickers: list[str], broker: BrokerClient) -> dict[str, float]:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}


class PPOPolicyAdapter(PolicyAdapter):
    """
    학습된 분봉 PPO 정책으로 목표 비중 산출.

    TODO(Phase 3-4 완료 후 구현):
      1. broker.get_minute_bars()로 최근 봉 수집
      2. minute_features_colab.ipynb와 동일한 기술지표 계산
      3. hybrid_model_minute_colab.ipynb에서 학습한 Chronos+MTGNN으로 임베딩 추출
      4. models/ppo_portfolio_minute.zip 로드 후 state 구성 → action 예측
      5. action(클러스터 비중) → 클러스터 내 종목 비중으로 환산
    """

    def __init__(self, model_path: str, cluster_csv_path: str):
        raise NotImplementedError(
            "분봉 임베딩 파이프라인이 아직 없습니다. Phase 2-4 노트북 완료 후 구현하세요."
        )

    def target_weights(self, tickers: list[str], broker: BrokerClient) -> dict[str, float]:
        raise NotImplementedError


class CircuitBreaker:
    """일일 손실 한도 도달 시 신규 주문을 막는다."""

    def __init__(self, limit_pct: float):
        self.limit_pct = limit_pct
        self.day_start_equity: float | None = None
        self.tripped = False

    def check(self, broker: BrokerClient) -> bool:
        equity = broker.get_cash_balance() + sum(
            p.quantity * p.current_price for p in broker.get_positions()
        )
        if self.day_start_equity is None:
            self.day_start_equity = equity
            return True
        drawdown = (equity - self.day_start_equity) / self.day_start_equity
        if drawdown <= -self.limit_pct:
            if not self.tripped:
                log.error(
                    "🛑 서킷브레이커 발동: 당일 손실 %.2f%% (한도 %.2f%%) — 신규 주문 중단",
                    -drawdown * 100,
                    self.limit_pct * 100,
                )
            self.tripped = True
            return False
        return True

    def reset_for_new_day(self):
        self.day_start_equity = None
        self.tripped = False


def is_market_open(now: datetime) -> bool:
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE_FOR_ENTRIES


def rebalance_step(
    broker: BrokerClient, policy: PolicyAdapter, config: LoopConfig, breaker: CircuitBreaker
) -> None:
    if not breaker.check(broker):
        return

    targets = policy.target_weights(config.tickers, broker)
    for ticker, w in targets.items():
        if w > config.risk.max_weight_per_ticker:
            log.warning("종목 %s 목표비중 %.2f%% → 상한 %.2f%%로 제한", ticker, w * 100, config.risk.max_weight_per_ticker * 100)
            targets[ticker] = config.risk.max_weight_per_ticker

    equity = broker.get_cash_balance() + sum(
        p.quantity * p.current_price for p in broker.get_positions()
    )
    positions = {p.ticker: p for p in broker.get_positions()}

    for ticker, target_w in targets.items():
        price = broker.get_current_price(ticker)
        target_value = equity * target_w
        current_qty = positions.get(ticker).quantity if ticker in positions else 0
        target_qty = int(target_value // price)
        diff = target_qty - current_qty

        if diff == 0:
            continue

        side = OrderSide.BUY if diff > 0 else OrderSide.SELL
        qty = abs(diff)

        if config.dry_run:
            log.info("[DRY-RUN] %s %s %d주 (현재 %d → 목표 %d)", side.value, ticker, qty, current_qty, target_qty)
            continue

        result = broker.place_order(ticker, side, qty)
        log.info(
            "주문 %s: %s %s %d주 → %s (%s)",
            "성공" if result.accepted else "실패",
            ticker,
            side.value,
            qty,
            result.order_id,
            result.message,
        )


def run(config: LoopConfig, broker: BrokerClient, policy: PolicyAdapter) -> None:
    log.info(
        "실거래 루프 시작 | mode=%s | dry_run=%s | interval=%ds | tickers=%d",
        "실전" if broker.is_live else "모의투자",
        config.dry_run,
        config.decision_interval_sec,
        len(config.tickers),
    )
    breaker = CircuitBreaker(config.risk.daily_loss_limit_pct)
    last_date = None

    while True:
        now = datetime.now()
        if last_date != now.date():
            breaker.reset_for_new_day()
            last_date = now.date()

        if is_market_open(now):
            try:
                rebalance_step(broker, policy, config, breaker)
            except Exception:
                log.exception("리밸런싱 스텝 중 오류 발생 — 다음 스텝까지 대기")
        else:
            log.info("장 시간 외 대기 중 (%s)", now.strftime("%H:%M:%S"))

        time.sleep(config.decision_interval_sec)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="실제 주문 실행 (기본은 dry-run)")
    parser.add_argument("--interval", type=int, default=1800, help="리밸런싱 간격(초)")
    parser.add_argument(
        "--tickers", nargs="+", required=True, help="대상 종목코드 목록 (테스트 시 소수만 지정 권장)"
    )
    args = parser.parse_args()

    broker = KISBrokerClient()
    policy = EqualWeightPolicy()  # TODO: Phase 3-4 완료 후 PPOPolicyAdapter로 교체
    config = LoopConfig(
        tickers=args.tickers, decision_interval_sec=args.interval, dry_run=not args.live
    )
    run(config, broker, policy)


if __name__ == "__main__":
    main()
