"""
Binance REST 클라이언트 (ccxt 래퍼).

⚠️ 실행 전 필수 확인:
  - `pip install ccxt` 필요.
  - 기본값은 테스트넷(Binance Spot Testnet, https://testnet.binance.vision)이다.
    실계좌로 전환하려면 BINANCE_LIVE_MODE=real 을 명시해야 한다.
  - 테스트넷 API 키는 실계좌 키와 별개로 위 사이트에서 GitHub 로그인 후 발급.
  - 주문 수량은 심볼별 최소 단위(stepSize)/최소 명목가(minNotional) 제약이 있다.
    place_order는 ccxt의 amount_to_precision으로 stepSize만 보정하며, minNotional
    미만 주문은 거래소에서 거부될 수 있으니 실거래 전 심볼별 필터를 재확인할 것.

환경변수:
  BINANCE_API_KEY, BINANCE_API_SECRET : Binance(또는 테스트넷) 발급 키
  BINANCE_LIVE_MODE                   : "real"이면 실계좌, 그 외(기본값)는 테스트넷
"""

from __future__ import annotations

import os
from pathlib import Path

import ccxt
from dotenv import load_dotenv

from crypto.broker.base import BrokerClient, OrderResult, OrderSide, Position

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

QUOTE_CCY = "USDT"


class BinanceBrokerClient(BrokerClient):
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        live: bool | None = None,
    ):
        self._live = (
            live if live is not None else os.environ.get("BINANCE_LIVE_MODE") == "real"
        )

        self._exchange = ccxt.binance(
            {
                "apiKey": api_key or os.environ.get("BINANCE_API_KEY", ""),
                "secret": api_secret or os.environ.get("BINANCE_API_SECRET", ""),
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }
        )
        if not self._live:
            self._exchange.set_sandbox_mode(True)
            print("[BinanceBrokerClient] 테스트넷 모드로 초기화됨")
        else:
            print(
                "[BinanceBrokerClient] ⚠️ 실계좌 모드로 초기화됨 — 실제 주문이 실계좌에 반영됩니다."
            )

    @property
    def is_live(self) -> bool:
        return self._live

    # ── 시세 조회 ─────────────────────────────────────────────────────

    def get_current_price(self, symbol: str) -> float:
        ticker = self._exchange.fetch_ticker(symbol)
        return float(ticker["last"])

    def get_minute_bars(self, symbol: str, n_bars: int = 30) -> list[dict]:
        ohlcv = self._exchange.fetch_ohlcv(symbol, timeframe="5m", limit=n_bars)
        return [
            {
                "time": row[0],
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5],
            }
            for row in ohlcv
        ]

    # ── 잔고/포지션 ───────────────────────────────────────────────────

    def get_positions(self) -> list[Position]:
        balance = self._exchange.fetch_balance()
        positions = []
        for asset, amounts in balance.get("total", {}).items():
            if asset == QUOTE_CCY or not amounts:
                continue
            symbol = f"{asset}/{QUOTE_CCY}"
            try:
                price = self.get_current_price(symbol)
            except (ccxt.BadSymbol, ccxt.ExchangeError, TypeError, KeyError):
                # USDT로 직거래 안 되거나(BadSymbol) 시세가 없는(테스트넷 더스트/가짜 토큰 등
                # ticker['last']가 None인 경우 TypeError) 자산은 스킵
                continue
            if price is None:
                continue
            positions.append(
                Position(
                    symbol=symbol,
                    quantity=float(amounts),
                    avg_price=price,  # ccxt 잔고 응답에는 평단가가 없어 현재가로 대체
                    current_price=price,
                )
            )
        return positions

    def get_cash_balance(self) -> float:
        balance = self._exchange.fetch_balance()
        return float(balance.get("free", {}).get(QUOTE_CCY, 0.0))

    # ── 주문 ─────────────────────────────────────────────────────────

    def place_order(self, symbol: str, side: OrderSide, quantity: float) -> OrderResult:
        if quantity <= 0:
            raise ValueError("quantity는 양수여야 합니다")

        amount = float(self._exchange.amount_to_precision(symbol, quantity))
        try:
            order = self._exchange.create_order(
                symbol=symbol,
                type="market",
                side=side.value,
                amount=amount,
            )
            return OrderResult(
                symbol=symbol,
                side=side,
                quantity=amount,
                order_id=str(order.get("id", "")),
                accepted=True,
                message=order.get("status", ""),
            )
        except ccxt.BaseError as e:
            return OrderResult(
                symbol=symbol,
                side=side,
                quantity=amount,
                order_id="",
                accepted=False,
                message=str(e),
            )
