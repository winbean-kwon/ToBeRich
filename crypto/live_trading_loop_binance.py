"""
실거래 루프 (Binance 버전) — decision interval마다 목표 비중을 산출해 브로커에 주문을 낸다.

live_trading_loop.py(KIS/KOSPI)와의 차이:
  - 코인 시장은 24/7이므로 장 시간 게이트가 없다.
  - 주문 수량이 float(소수점 단위 매매 가능).
  - 기본 정책은 crypto/inference/policy_v4.py의 V4PolicyAdapter(β=-30 PPO 풀 에이전트 단독 +
    추론 스무딩 — DQN 라우터는 §15 검증에서 상수함수로 확인돼 제거함, §16에서 β=30→β=-30으로
    교체). 브로커 연동만 검증하고 싶으면 --policy equal로 EqualWeightPolicy를 쓴다.

⚠️ 기본값은 --dry-run(주문 미실행, 로그만 출력)이다. 실제 주문을 내려면 --live
   플래그를 명시해야 하고, 그때도 BINANCE_LIVE_MODE가 "real"이 아니면 테스트넷
   계좌로만 나간다 (broker/binance_client.py 참고).
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from crypto.broker.base import BrokerClient, OrderSide
from crypto.broker.binance_client import BinanceBrokerClient
from crypto.policy_base import EqualWeightPolicy, PolicyAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("live_trading_loop_binance")

FROZEN_UNIVERSE_PATH = Path(__file__).resolve().parent / "data" / "live_universe.json"


def load_frozen_universe() -> list[str]:
    """v4 정책이 학습된 고정 44종목 유니버스를 반환한다.

    universe.py의 get_top_usdt_symbols()는 호출 시점마다 실시간 거래대금으로
    재랭킹하므로 학습 유니버스(features_5m/*.parquet 44종목)와 어긋날 수 있다 —
    라이브 정책 실행에는 반드시 이 고정 리스트를 써야 한다.
    """
    return json.loads(FROZEN_UNIVERSE_PATH.read_text())


@dataclass
class RiskConfig:
    max_weight_per_symbol: float = 0.3
    daily_loss_limit_pct: float = 0.03  # 이 이상 손실 시 당일 거래 중단
    max_capital_usdt: float | None = None  # 계좌 실제 잔고가 더 크더라도 이 금액까지만 운용


@dataclass
class LoopConfig:
    symbols: list[str]
    decision_interval_sec: int = 1800  # 30분
    dry_run: bool = True
    risk: RiskConfig = field(default_factory=RiskConfig)


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
        if self.day_start_equity is None or self.day_start_equity <= 0:
            # 잔고 0(자금 미입금/전량 인출 상태)이면 손실률 자체가 정의되지 않으므로
            # 갱신만 하고 통과시킨다 — 이후 입금돼 equity > 0이 되는 시점부터 추적 시작.
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
    if config.risk.max_capital_usdt is not None and equity > config.risk.max_capital_usdt:
        log.info(
            "실제 잔고 %.2f USDT 중 %.2f USDT만 운용 (--max-capital 제한)",
            equity, config.risk.max_capital_usdt,
        )
        equity = config.risk.max_capital_usdt
    positions = {p.symbol: p for p in broker.get_positions()}

    for symbol, target_w in targets.items():
        try:
            price = broker.get_current_price(symbol)
        except Exception:
            log.warning("심볼 %s 시세 조회 실패 — 이번 사이클 리밸런싱 스킵(상장폐지/거래정지 가능성)", symbol)
            continue
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
        "--symbols", nargs="+", default=None,
        help="대상 심볼 목록 (예: BTC/USDT ETH/USDT). 생략하면 v4 학습에 쓰인 고정 44종목 유니버스를 사용",
    )
    parser.add_argument(
        "--policy", choices=["v4", "equal"], default="v4",
        help="v4=실제 HRL 정책(기본), equal=브로커 연동만 검증하는 더미 등가중 정책",
    )
    parser.add_argument(
        "--model-dir", default=str(Path(__file__).resolve().parent / "models"),
        help="crypto_hybrid_best.pt / crypto_hrl_pool_v4 / crypto_hrl_router_v4.zip이 있는 디렉터리",
    )
    parser.add_argument(
        "--max-capital", type=float, default=None,
        help="계좌 실제 잔고가 더 크더라도 이 금액(USDT)까지만 운용 (소액 검증용 안전장치)",
    )
    parser.add_argument("--daily-loss-limit", type=float, default=0.03, help="서킷브레이커 발동 일일 손실률")
    args = parser.parse_args()

    symbols = args.symbols or load_frozen_universe()

    broker = BinanceBrokerClient()
    if args.policy == "equal":
        policy: PolicyAdapter = EqualWeightPolicy()
    else:
        from crypto.inference.policy_v4 import V4PolicyAdapter

        policy = V4PolicyAdapter(model_dir=args.model_dir, symbols=symbols)

    config = LoopConfig(
        symbols=symbols,
        decision_interval_sec=args.interval,
        dry_run=not args.live,
        risk=RiskConfig(daily_loss_limit_pct=args.daily_loss_limit, max_capital_usdt=args.max_capital),
    )
    run(config, broker, policy)


if __name__ == "__main__":
    main()
