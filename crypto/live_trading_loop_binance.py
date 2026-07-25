"""
실거래 루프 (Binance 버전) — decision interval마다 목표 비중을 산출해 브로커에 주문을 낸다.

live_trading_loop.py(KIS/KOSPI)와의 차이:
  - 코인 시장은 24/7이므로 장 시간 게이트가 없다.
  - 주문 수량이 float(소수점 단위 매매 가능).
  - PolicyAdapter는 아직 EqualWeightPolicy만 있다 — 분봉 피처/임베딩 파이프라인이
    코인 유니버스로 재구축되기 전까지는 브로커 연동 자체만 검증하는 용도.

⚠️ 기본값은 --dry-run(주문 미실행, 로그만 출력)이다. 실제 주문을 내려면 --live
   플래그를 명시해야 하고, 그때도 BINANCE_LIVE_MODE가 "real"이 아니면 테스트넷
   계좌로만 나간다 (broker/binance_client.py 참고).
"""

from __future__ import annotations

import argparse
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from crypto.broker.base import BrokerClient, OrderSide
from crypto.broker.binance_client import BinanceBrokerClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("live_trading_loop_binance")


@dataclass
class RiskConfig:
    max_weight_per_symbol: float = 0.3
    daily_loss_limit_pct: float = 0.03  # 이 이상 손실 시 당일 거래 중단


@dataclass
class LoopConfig:
    symbols: list[str]
    decision_interval_sec: int = 1800  # 30분
    dry_run: bool = True
    risk: RiskConfig = field(default_factory=RiskConfig)


class PolicyAdapter(ABC):
    """목표 비중 산출 정책 인터페이스."""

    @abstractmethod
    def target_weights(self, symbols: list[str], broker: BrokerClient) -> dict[str, float]:
        """심볼별 목표 비중 (합계 1.0 이하) 반환."""


class EqualWeightPolicy(PolicyAdapter):
    """브로커 연동 자체를 검증하기 위한 더미 정책 — 등가중 배분."""

    def target_weights(self, symbols: list[str], broker: BrokerClient) -> dict[str, float]:
        w = 1.0 / len(symbols)
        return {s: w for s in symbols}


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


def rebalance_step(
    broker: BrokerClient, policy: PolicyAdapter, config: LoopConfig, breaker: CircuitBreaker
) -> None:
    if not breaker.check(broker):
        return

    targets = policy.target_weights(config.symbols, broker)
    for symbol, w in targets.items():
        if w > config.risk.max_weight_per_symbol:
            log.warning("심볼 %s 목표비중 %.2f%% → 상한 %.2f%%로 제한", symbol, w * 100, config.risk.max_weight_per_symbol * 100)
            targets[symbol] = config.risk.max_weight_per_symbol

    equity = broker.get_cash_balance() + sum(
        p.quantity * p.current_price for p in broker.get_positions()
    )
    positions = {p.symbol: p for p in broker.get_positions()}

    for symbol, target_w in targets.items():
        price = broker.get_current_price(symbol)
        target_value = equity * target_w
        current_qty = positions.get(symbol).quantity if symbol in positions else 0.0
        target_qty = target_value / price
        diff = target_qty - current_qty

        if abs(diff) * price < 1.0:  # 명목가 1 USDT 미만 리밸런싱은 스킵 (수수료 대비 무의미)
            continue

        side = OrderSide.BUY if diff > 0 else OrderSide.SELL
        qty = abs(diff)

        if config.dry_run:
            log.info("[DRY-RUN] %s %s %.6f (현재 %.6f → 목표 %.6f)", side.value, symbol, qty, current_qty, target_qty)
            continue

        result = broker.place_order(symbol, side, qty)
        log.info(
            "주문 %s: %s %s %.6f → %s (%s)",
            "성공" if result.accepted else "실패",
            symbol,
            side.value,
            qty,
            result.order_id,
            result.message,
        )


def run(config: LoopConfig, broker: BrokerClient, policy: PolicyAdapter) -> None:
    log.info(
        "실거래 루프 시작 | mode=%s | dry_run=%s | interval=%ds | symbols=%d",
        "실계좌" if broker.is_live else "테스트넷",
        config.dry_run,
        config.decision_interval_sec,
        len(config.symbols),
    )
    breaker = CircuitBreaker(config.risk.daily_loss_limit_pct)
    last_date = None

    while True:
        now = datetime.now()
        if last_date != now.date():
            breaker.reset_for_new_day()
            last_date = now.date()

        try:
            rebalance_step(broker, policy, config, breaker)
        except Exception:
            log.exception("리밸런싱 스텝 중 오류 발생 — 다음 스텝까지 대기")

        time.sleep(config.decision_interval_sec)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="실제 주문 실행 (기본은 dry-run)")
    parser.add_argument("--interval", type=int, default=1800, help="리밸런싱 간격(초)")
    parser.add_argument(
        "--symbols", nargs="+", required=True, help="대상 심볼 목록 (예: BTC/USDT ETH/USDT, 테스트 시 소수만 지정 권장)"
    )
    args = parser.parse_args()

    broker = BinanceBrokerClient()
    policy = EqualWeightPolicy()  # TODO: 코인 유니버스용 분봉 피처/임베딩/PPO 파이프라인 완료 후 교체
    config = LoopConfig(
        symbols=args.symbols, decision_interval_sec=args.interval, dry_run=not args.live
    )
    run(config, broker, policy)


if __name__ == "__main__":
    main()
