"""
암호화폐 브로커 실행 어댑터 공통 인터페이스.

기존 broker/base.py(KIS용)와 거의 동일하지만 두 가지가 다르다:
  - quantity가 float (코인은 소수점 단위 주문 가능, 국내주식처럼 정수 주(株) 아님)
  - ticker 대신 symbol (ccxt 통일 표기, 예: "BTC/USDT")

live_trading_loop_binance.py는 이 인터페이스에만 의존한다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Position:
    symbol: str
    quantity: float
    avg_price: float
    current_price: float


@dataclass
class OrderResult:
    symbol: str
    side: OrderSide
    quantity: float
    order_id: str
    accepted: bool
    message: str = ""


class BrokerClient(ABC):
    """실계좌/테스트넷 암호화폐 거래소 실행 어댑터 추상 인터페이스."""

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        """심볼 현재가 조회 (예: "BTC/USDT")."""

    @abstractmethod
    def get_minute_bars(self, symbol: str, n_bars: int = 30) -> list[dict]:
        """최근 N개 분봉 조회. 각 항목: {time, open, high, low, close, volume}."""

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """현재 보유 심볼/수량/평단가 조회."""

    @abstractmethod
    def get_cash_balance(self) -> float:
        """주문 가능 현금(기준통화, USDT) 조회."""

    @abstractmethod
    def place_order(self, symbol: str, side: OrderSide, quantity: float) -> OrderResult:
        """시장가 주문 실행. quantity는 항상 양수."""

    @abstractmethod
    def get_min_notional(self, symbol: str) -> float:
        """심볼별 최소 주문 금액(기준통화). 이 미만 주문은 거래소가 거부한다."""

    @property
    @abstractmethod
    def is_live(self) -> bool:
        """실계좌 모드 여부. False면 테스트넷."""

    def is_tradable(self, symbol: str) -> bool:
        """현재 주문 가능한 심볼인지 (거래정지/상장폐지면 False)."""
        return True


def managed_equity(
    cash: float, positions: dict[str, Position], symbols: list[str], max_capital: float | None = None
) -> float:
    """정책이 운용하는 자산 규모 = USDT 현금 + 유니버스 심볼 보유분 평가액 (max_capital로 상한).

    유니버스 밖 보유 코인은 정책이 사고팔지 않으므로 포함하면 안 된다 — 포함하면 그만큼의
    가치를 유니버스에 배분하려고 실제로는 없는 현금으로 매수를 시도하게 된다.
    루프의 주문 계산과 정책의 prev_weights 초기화가 반드시 같은 정의를 써야 한다.
    """
    equity = cash + sum(
        positions[s].quantity * positions[s].current_price for s in symbols if s in positions
    )
    if max_capital is not None:
        equity = min(equity, max_capital)
    return equity
