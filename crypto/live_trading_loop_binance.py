"""
실거래 루프 (Binance 버전) — decision interval마다 목표 비중을 산출해 브로커에 주문을 낸다.

live_trading_loop.py(KIS/KOSPI)와의 차이:
  - 코인 시장은 24/7이므로 장 시간 게이트가 없다.
  - 주문 수량이 float(소수점 단위 매매 가능).
  - 기본 정책은 crypto/inference/policy_v4.py의 V4PolicyAdapter(β=30 재학습 PPO 풀 에이전트 단독 +
    추론 스무딩 — DQN 라우터는 §15 검증에서 상수함수로 확인돼 제거함, §16에서 β=30→β=-30으로 교체했다가
    회계 수정 후 재학습(2026-10-08)으로 다시 β=30). 브로커 연동만 검증하고 싶으면 --policy equal로 EqualWeightPolicy를 쓴다.

⚠️ 기본값은 --dry-run(주문 미실행, 로그만 출력)이다. 실제 주문을 내려면 --live
   플래그를 명시해야 하고, 그때도 BINANCE_LIVE_MODE가 "real"이 아니면 테스트넷
   계좌로만 나간다 (broker/binance_client.py 참고).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from crypto.broker.base import BrokerClient, OrderSide, managed_equity
from crypto.broker.binance_client import BinanceBrokerClient
from crypto.live_monitor import Monitor, MonitorLogHandler, serve_dashboard
from crypto.policy_base import EqualWeightPolicy, PolicyAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("live_trading_loop_binance")

CRYPTO_DIR = Path(__file__).resolve().parent
FROZEN_UNIVERSE_PATH = CRYPTO_DIR / "data" / "live_universe.json"
STATE_PATH = CRYPTO_DIR / "live_state.json"  # 서킷브레이커 당일 기준점 (재시작해도 유지되도록)
LOCK_PATH = CRYPTO_DIR / "live_trading.lock"
LEDGER_PATH = CRYPTO_DIR / "live_ledger.csv"  # 사이클별 기록 (대시보드·사후 분석용)
POLICY_STATE_PATH = CRYPTO_DIR / "policy_state.json"  # 정책 스무딩 상태 (재시작해도 이어지도록)
EVENTS_PATH = CRYPTO_DIR / "live_events.jsonl"  # WARNING 이상 로그 (재시작해도 대시보드에 남도록)


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


MIN_REBALANCE_USDT = 1.0  # 거래소 최소 명목가보다 작더라도 이 미만 리밸런싱은 스킵 (수수료 대비 무의미)
# 거래소 NOTIONAL 필터는 직전 5분 평균가로 판정하고 수량은 stepSize로 절사되므로, 최소금액에 딱 맞춘
# 주문은 last 가격 기준으로 통과해 보여도 거부될 수 있다 — 최소금액보다 이만큼 여유를 둔다.
NOTIONAL_MARGIN = 1.05
# 주문은 시장가 대신 최우선호가 ±MAX_SLIPPAGE에 지정가 IOC로 낸다 — 얇은 호가(저유동 알트)에서 시장가가
# 호가를 훑고 올라가는 것을 막고, 못 채운 잔량은 취소돼 다음 사이클에 다시 시도된다.
MAX_SLIPPAGE = 0.005
MAX_SPREAD = 0.01  # 매수-매도 호가 차이가 이보다 넓으면 그 사이클엔 그 종목을 거래하지 않는다
MAX_CONSECUTIVE_FAILURES = 3  # 연속 실패가 이만큼 쌓이면 CRITICAL로 남긴다 (키 만료·IP 차단 등 스스로 안 풀리는 장애)
BUY_CASH_BUFFER = 0.995  # 수수료(BNB 차감 미사용 시)·가격 변동으로 잔고 부족이 나지 않도록 남겨두는 여유
CANDLE_CLOSE_DELAY_SEC = 15  # 정각 경계 직후 거래소에 직전 5분봉이 확정 반영될 때까지 기다리는 시간
# 종목당 목표금액(상위 종목 중앙값)이 최소주문금액의 이 배수보다 작으면, 정책의 작은 비중 변화가 대부분
# 주문으로 이어지지 못해 백테스트와 다른 전략이 된다
SMALL_POSITION_MULTIPLE = 3

_warned_untradable: set[str] = set()


class CircuitBreaker:
    """일일 손실 한도 도달 시 신규 주문을 막는다."""

    def __init__(self, limit_pct: float, state_path: Path | None = None):
        self.limit_pct = limit_pct
        self.state_path = state_path  # None이면 상태를 저장하지 않음(dry-run이 실계좌 상태를 덮어쓰지 않도록)
        self.day: str | None = None
        self.day_start_equity: float | None = None
        self.day_start_ms: int | None = None  # 기준점을 잡은 시각 — 이후 입출금을 손익에서 빼는 기준
        self.tripped = False
        self.last_pnl_pct: float | None = None

    def start_day(self, day: str) -> None:
        """날짜가 바뀌면 기준점을 리셋한다. 같은 날 재시작이면 저장된 기준점·발동 상태를 복원한다.

        메모리에만 두면 손실 후 크래시→재시작(감시 배치/systemd가 10초 만에 다시 띄움)될 때마다
        기준점이 손실 후 잔고로 다시 잡혀 일일 손실 한도가 사실상 무력화된다.
        """
        if self.day == day:
            return
        self.day, self.day_start_equity, self.day_start_ms, self.tripped = day, None, None, False
        self.last_pnl_pct = None
        if self.state_path is not None and self.state_path.exists():
            try:
                state = json.loads(self.state_path.read_text())
            except (OSError, ValueError):
                log.warning("서킷브레이커 상태 파일을 읽지 못함 — 새로 시작")
                return
            if state.get("day") == day:
                self.day_start_equity = state.get("day_start_equity")
                self.day_start_ms = state.get("day_start_ms")
                self.tripped = bool(state.get("tripped"))
                log.info("서킷브레이커 상태 복원 | 기준 %.2f USDT | 발동=%s", self.day_start_equity or 0.0, self.tripped)

    def _save(self) -> None:
        if self.state_path is None:
            return
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({
            "day": self.day, "day_start_equity": self.day_start_equity,
            "day_start_ms": self.day_start_ms, "tripped": self.tripped,
        }))
        os.replace(tmp, self.state_path)

    def check(self, equity: float, max_capital: float | None = None, net_transfers: float = 0.0) -> bool:
        """net_transfers: 기준점 이후 입금-출금 순액. 이걸 빼야 출금을 손실로, 입금을 수익으로 오인하지 않는다."""
        if self.day_start_equity is None or self.day_start_equity <= 0:
            # 잔고 0(자금 미입금/전량 인출 상태)이면 손실률 자체가 정의되지 않으므로
            # 갱신만 하고 통과시킨다 — 이후 입금돼 equity > 0이 되는 시점부터 추적 시작.
            self.day_start_equity = equity
            self.day_start_ms = int(time.time() * 1000)
            self._save()
            return True
        # --max-capital로 일부만 운용 중이면 손실률의 분모도 실제 운용 금액이어야 한다 —
        # 전체 잔고로 나누면 운용분이 한도의 몇 배를 잃어도 서킷브레이커가 안 걸린다.
        base = self.day_start_equity if max_capital is None else min(self.day_start_equity, max_capital)
        drawdown = (equity - net_transfers - self.day_start_equity) / base
        self.last_pnl_pct = drawdown
        if self.tripped:
            # 당일 한 번 발동하면 손실이 일부 회복돼도 그날은 계속 중단한다(재시작 후에도 동일)
            return False
        if drawdown <= -self.limit_pct:
            log.error(
                "🛑 서킷브레이커 발동: 당일 손실 %.2f%% (한도 %.2f%%, 입출금 %.2f USDT 제외) — 신규 주문 중단",
                -drawdown * 100, self.limit_pct * 100, net_transfers,
            )
            self.tripped = True
            self._save()
            return False
        return True


def _place(
    broker: BrokerClient, symbol: str, side: OrderSide, qty: float, limit_price: float,
    current_qty: float, target_qty: float, dry_run: bool,
) -> float:
    """주문을 내고 체결 수량을 반환한다(dry-run은 전량 체결로 가정, 체결 수량을 모르면 주문 수량)."""
    if dry_run:
        log.info("[DRY-RUN] %s %s %.6f @≤%.6g (현재 %.6f → 목표 %.6f)", side.value, symbol, qty, limit_price, current_qty, target_qty)
        return qty
    result = broker.place_order(symbol, side, qty, limit_price=limit_price)
    filled = (result.filled if result.filled is not None else result.quantity) if result.accepted else 0.0
    (log.info if result.accepted else log.warning)(
        "주문 %s: %s %s %.6f @≤%.6g → 체결 %.6f, %s (%s)",
        "접수" if result.accepted else "실패", symbol, side.value, qty, limit_price, filled,
        result.order_id, result.message,
    )
    return filled


def rebalance_step(
    broker: BrokerClient, policy: PolicyAdapter, config: LoopConfig, breaker: CircuitBreaker,
    monitor=None,
) -> dict:
    """한 사이클을 실행하고 사이클 기록(ledger 행)을 반환한다."""
    positions = {p.symbol: p for p in broker.get_positions()}
    cash = broker.get_cash_balance()
    prices = {s: p.current_price for s, p in positions.items()}
    full_equity = managed_equity(cash, positions, config.symbols)
    equity = managed_equity(cash, positions, config.symbols, config.risk.max_capital_usdt)
    row = {"time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "equity": round(equity, 4)}

    def update(**kw):
        if monitor is not None:
            monitor.update(**kw)

    net = 0.0
    if breaker.day_start_ms is not None:
        try:
            net = broker.get_net_transfers(breaker.day_start_ms, prices)
        except Exception:
            log.warning("입출금 내역 조회 실패 — 이번 사이클은 입출금 보정 없이 손실률 계산", exc_info=True)
    ok = breaker.check(full_equity, config.risk.max_capital_usdt, net)
    update(breaker_tripped=breaker.tripped, day_pnl_pct=breaker.last_pnl_pct)
    if not ok:
        return {**row, "note": "서킷브레이커 발동 — 주문 중단"}

    untradable = [s for s in config.symbols if not broker.is_tradable(s)]
    update(untradable=untradable, untradable_ratio=len(untradable) / len(config.symbols))
    for symbol in untradable:
        if symbol not in _warned_untradable:
            log.warning("심볼 %s 거래 불가 상태(거래정지/상장폐지) — 정책 선택·주문 대상에서 제외", symbol)
            _warned_untradable.add(symbol)

    if not config.dry_run:
        held = [s for s in config.symbols if s in positions and s not in untradable]
        since_ms = int((time.time() - 1.5 * config.decision_interval_sec) * 1000)
        try:
            others = broker.find_other_bot_orders(held, since_ms)
        except Exception:
            log.warning("다른 봇 주문 확인 실패 — 이번 사이클은 확인 없이 진행", exc_info=True)
            others = []
        update(other_bot_orders=others[:10])
        if others:
            log.critical(
                "🚨 이 컴퓨터가 아닌 봇의 주문 %d건 감지 — 다른 컴퓨터에서 같은 계좌로 봇이 돌고 있을 가능성. "
                "중복 주문 방지를 위해 이번 사이클 주문 중단. 예: %s", len(others), others[0],
            )
            return {**row, "note": "다른 봇 주문 감지 — 주문 중단"}

    targets = policy.target_weights(config.symbols, broker)
    for symbol, w in targets.items():
        if w > config.risk.max_weight_per_symbol:
            log.warning("심볼 %s 목표비중 %.2f%% → 상한 %.2f%%로 제한", symbol, w * 100, config.risk.max_weight_per_symbol * 100)
            targets[symbol] = config.risk.max_weight_per_symbol
    row["rho"] = round(policy.last_rho, 4) if getattr(policy, "last_rho", None) is not None else ""
    if config.risk.max_capital_usdt is not None and equity >= config.risk.max_capital_usdt:
        log.info("%.2f USDT만 운용 (--max-capital 제한)", equity)

    # 사이클 끝의 종목별 보유 평가액 — 주문이 체결된 만큼만 갱신해 목표와의 괴리(백테스트와의 차이)를 잰다
    final_value = {s: positions[s].quantity * positions[s].current_price if s in positions else 0.0 for s in config.symbols}
    sells, buys = [], []
    min_notional = 5.0
    for symbol, target_w in targets.items():
        if symbol in untradable:
            continue
        try:
            quote = broker.get_quote(symbol)
        except Exception:
            log.warning("심볼 %s 시세 조회 실패 — 이번 사이클 리밸런싱 스킵(상장폐지/거래정지 가능성)", symbol)
            continue
        price = quote.last
        current_qty = positions[symbol].quantity if symbol in positions else 0.0
        final_value[symbol] = current_qty * price
        target_value = equity * target_w
        diff_value = target_value - current_qty * price
        # 거래소 최소 명목가(대부분 5 USDT) 미만 주문은 어차피 거부되므로 미리 거른다 —
        # 안 거르면 소액 운용 시 매 사이클 거의 모든 주문이 거부 로그만 남긴다.
        min_notional = broker.get_min_notional(symbol)
        min_value = max(MIN_REBALANCE_USDT, min_notional * NOTIONAL_MARGIN)
        if abs(diff_value) < min_value:
            continue
        if quote.spread > MAX_SPREAD:
            log.warning("심볼 %s 호가 스프레드 %.2f%% > %.2f%% — 유동성 부족으로 이번 사이클 거래 보류", symbol, quote.spread * 100, MAX_SPREAD * 100)
            continue
        if diff_value < 0:
            qty = -diff_value / price
            if target_value < min_value:
                # 목표가 사실상 0이면 남은 잔량이 최소 명목가 미만 더스트가 돼 다시는 팔 수 없게 되므로 전량 매도
                qty = current_qty
            sells.append((symbol, qty, quote.bid * (1 - MAX_SLIPPAGE), price, current_qty, target_value / price))
        else:
            buys.append((symbol, diff_value, quote.ask * (1 + MAX_SLIPPAGE), price, current_qty, target_value / price, min_value))

    n_orders = n_filled = 0
    # 매도를 먼저 내서 현금을 확보한 뒤 매수한다 — 심볼 순서대로 섞어 내면 매도 대금이 들어오기 전에
    # 매수가 잔고 부족으로 거부될 수 있다.
    for symbol, qty, limit, price, current_qty, target_qty in sells:
        filled = _place(broker, symbol, OrderSide.SELL, qty, limit, current_qty, target_qty, config.dry_run)
        n_orders += 1
        n_filled += filled > 0
        final_value[symbol] -= filled * price
        if config.dry_run:
            cash += filled * price

    available = cash if config.dry_run or not sells else broker.get_cash_balance()
    available *= BUY_CASH_BUFFER
    for symbol, needed, limit, price, current_qty, target_qty, min_value in buys:
        # 지정가 매수는 수량×지정가만큼 현금을 묶으므로 가용 현금 한도도 지정가 기준으로 본다
        qty = min(needed / price, available / limit)
        if qty * price < min_value:
            log.info("심볼 %s 매수 스킵 — 가용 현금 부족 (필요 %.2f, 가용 %.2f USDT)", symbol, needed, available)
            continue
        filled = _place(broker, symbol, OrderSide.BUY, qty, limit, current_qty, target_qty, config.dry_run)
        n_orders += 1
        n_filled += filled > 0
        final_value[symbol] += filled * price
        available -= filled * limit

    target_exposure = sum(targets.values())
    actual_exposure = sum(final_value.values()) / equity if equity > 0 else 0.0
    gap = sum(abs(targets.get(s, 0.0) * equity - v) for s, v in final_value.items()) if equity > 0 else 0.0
    tracking_gap = gap / equity if equity > 0 else 0.0
    top_values = sorted((w * equity for w in targets.values()), reverse=True)[: getattr(policy, "top_k", 10)]
    median_target = top_values[len(top_values) // 2] if top_values else 0.0
    small = (
        f"종목당 목표금액(상위 종목 중앙값) {median_target:.2f} USDT — 최소주문금액 {min_notional:.0f} USDT의 "
        f"{SMALL_POSITION_MULTIPLE}배 미만이라 정책의 비중 변화 대부분이 주문되지 못함. 운용금을 늘릴 것"
        if 0 < median_target < SMALL_POSITION_MULTIPLE * min_notional else ""
    )
    update(tracking_gap=tracking_gap, small_capital_warning=small)
    log.info(
        "사이클 완료 | 운용자산 %.2f USDT | 위험자산 비중 목표 %.1f%% · 실제 %.1f%% | 괴리 %.1f%% | 주문 %d건(체결 %d)",
        equity, target_exposure * 100, actual_exposure * 100, tracking_gap * 100, n_orders, n_filled,
    )
    return {
        **row,
        "target_exposure": round(target_exposure, 5),
        "actual_exposure": round(actual_exposure, 5),
        "tracking_gap": round(tracking_gap, 5),
        "skipped_usdt": round(gap, 4),
        "orders": n_orders,
        "filled_orders": n_filled,
    }


def seconds_until_next_slot(interval_sec: int, offset_sec: float = CANDLE_CLOSE_DELAY_SEC) -> float:
    """다음 interval 경계(UTC 기준 정각/30분 등) + offset까지 남은 초.

    단순히 sleep(interval)을 하면 매 사이클 추론 시간(수십 초)만큼 결정 시점이 계속 밀려 학습 때의
    30분봉 경계와 어긋난다 — 벽시계 경계에 맞춰 깨어나도록 한다.
    """
    now = time.time()
    return (now // interval_sec + 1) * interval_sec + offset_sec - now


def acquire_single_instance_lock(path: Path = LOCK_PATH):
    """같은 컴퓨터에서 실거래 프로세스가 둘 이상 뜨지 않게 OS 파일 잠금을 건다.

    둘이 동시에 돌면 같은 계좌에 같은 리밸런싱 주문이 두 번 나간다. 반환된 파일 객체를 프로세스가
    끝날 때까지 들고 있어야 잠금이 유지된다(프로세스가 죽으면 OS가 자동 해제). 다른 컴퓨터에서
    도는 프로세스는 find_other_bot_orders로 감지한다.
    """
    f = open(path, "a+")
    try:
        if os.name == "nt":
            import msvcrt

            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        raise SystemExit(f"이미 다른 실거래 프로세스가 실행 중입니다({path}) — 중복 주문 방지를 위해 종료")
    return f


def code_version() -> str:
    """어떤 브랜치·커밋의 코드가 도는지 — 배포 서버가 엉뚱한 브랜치(예: 옛 정책이 남은 main)를 돌리고
    있어도 로그·대시보드만 보고 알아챌 수 있도록."""
    try:
        def git(*a):
            return subprocess.run(["git", *a], cwd=CRYPTO_DIR, capture_output=True, text=True, timeout=5).stdout.strip()
        dirty = " (커밋 안 된 수정 있음)" if git("status", "--porcelain", "--untracked-files=no") else ""
        return f"브랜치 {git('rev-parse', '--abbrev-ref', 'HEAD')} | 커밋 {git('rev-parse', '--short', 'HEAD')}{dirty}"
    except (OSError, subprocess.SubprocessError):
        return "코드 버전 확인 불가(git 없음)"


def run(config: LoopConfig, broker: BrokerClient, policy: PolicyAdapter, monitor=None, log_handler=None) -> None:
    log.info(
        "실거래 루프 시작 | mode=%s | dry_run=%s | interval=%ds | symbols=%d",
        "실계좌" if broker.is_live else "테스트넷",
        config.dry_run,
        config.decision_interval_sec,
        len(config.symbols),
    )
    breaker = CircuitBreaker(config.risk.daily_loss_limit_pct, state_path=None if config.dry_run else STATE_PATH)
    failures = 0

    while True:
        breaker.start_day(datetime.now().date().isoformat())
        if log_handler is not None:
            log_handler.cycle_warnings = 0

        try:
            row = rebalance_step(broker, policy, config, breaker, monitor)
            failures = 0
        except Exception:
            failures += 1
            log.exception("리밸런싱 스텝 중 오류 발생 (연속 %d회) — 다음 스텝까지 대기", failures)
            if failures >= MAX_CONSECUTIVE_FAILURES:
                log.critical(
                    "🚨 %d사이클 연속 실패 — API 키 만료/IP 변경(-2015), 네트워크, 모델 파일 문제 등 저절로 "
                    "안 풀리는 장애일 가능성이 높음. 로그 확인 필요", failures,
                )
            row = {"time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "note": f"오류(연속 {failures}회)"}

        if monitor is not None:
            monitor.update(
                consecutive_failures=failures,
                last_cycle_warnings=log_handler.cycle_warnings if log_handler is not None else 0,
            )
            monitor.record_cycle(row)

        time.sleep(seconds_until_next_slot(config.decision_interval_sec))


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
    parser.add_argument("--dashboard-host", default="127.0.0.1", help="대시보드 바인드 주소 (외부 공개 시 DASHBOARD_TOKEN 필요)")
    parser.add_argument("--dashboard-port", type=int, default=8787, help="대시보드 포트")
    parser.add_argument("--no-dashboard", action="store_true", help="대시보드 끄기")
    args = parser.parse_args()

    symbols = args.symbols or load_frozen_universe()

    lock = acquire_single_instance_lock() if args.live else None  # noqa: F841 — 프로세스 수명 동안 잠금 유지
    version = code_version()
    log.info("코드 버전 | %s", version)

    monitor = log_handler = None
    if not args.no_dashboard:
        # dry-run 기록이 실계좌 기록에 섞이지 않도록 파일 저장은 --live일 때만
        monitor = Monitor(
            ledger_path=LEDGER_PATH if args.live else None,
            events_path=EVENTS_PATH if args.live else None,
            interval_sec=args.interval,
        )
        log_handler = MonitorLogHandler(monitor)
        logging.getLogger().addHandler(log_handler)
        serve_dashboard(monitor, args.dashboard_host, args.dashboard_port)

    broker = BinanceBrokerClient()
    key_warnings = broker.check_api_key_safety()
    for w in key_warnings:
        log.warning("⚠️ API 키 점검: %s", w)
    if args.policy == "equal":
        policy: PolicyAdapter = EqualWeightPolicy()
    else:
        from crypto.inference.policy_v4 import V4PolicyAdapter

        policy = V4PolicyAdapter(
            model_dir=args.model_dir, symbols=symbols, max_capital=args.max_capital,
            state_path=POLICY_STATE_PATH if args.live else None,  # dry-run이 실계좌 스무딩 상태를 덮어쓰지 않도록
        )

    if monitor is not None:
        monitor.update(
            mode=("실계좌" if broker.is_live else "테스트넷") + ("" if args.live else " · DRY-RUN(주문 안 냄)"),
            code_version=version,
            model_info=getattr(policy, "model_info", args.policy),
            max_capital=args.max_capital,
            api_key_warnings=key_warnings,
        )

    config = LoopConfig(
        symbols=symbols,
        decision_interval_sec=args.interval,
        dry_run=not args.live,
        risk=RiskConfig(daily_loss_limit_pct=args.daily_loss_limit, max_capital_usdt=args.max_capital),
    )
    run(config, broker, policy, monitor, log_handler)


if __name__ == "__main__":
    main()
