"""
브로커 실행 어댑터 공통 인터페이스.

live_trading_loop.py는 이 인터페이스에만 의존한다.
KIS 외 다른 브로커로 교체할 때는 이 클래스를 상속하는 새 구현체만 추가하면 된다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Position:
    ticker: str
    quantity: int
    avg_price: float
    current_price: float


@dataclass
class OrderResult:
    ticker: str
    side: OrderSide
    quantity: int
    order_id: str
    accepted: bool
    message: str = ""


class BrokerClient(ABC):
    """실계좌/모의투자 브로커 실행 어댑터 추상 인터페이스."""

    @abstractmethod
    def get_current_price(self, ticker: str) -> float:
        """종목 현재가 조회."""

    @abstractmethod
    def get_minute_bars(self, ticker: str, n_bars: int = 30) -> list[dict]:
        """최근 N개 분봉 조회. 각 항목: {time, open, high, low, close, volume}."""

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """현재 보유 종목/수량/평단가 조회."""

    @abstractmethod
    def get_cash_balance(self) -> float:
        """주문 가능 현금 조회."""

    @abstractmethod
    def place_order(self, ticker: str, side: OrderSide, quantity: int) -> OrderResult:
        """시장가 주문 실행. quantity는 항상 양수."""

    @property
    @abstractmethod
    def is_live(self) -> bool:
        """실전투자 모드 여부. False면 모의투자."""
