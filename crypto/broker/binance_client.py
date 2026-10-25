"""
Binance REST 클라이언트 (ccxt 래퍼).

⚠️ 실행 전 필수 확인:
  - `pip install ccxt` 필요.
  - 기본값은 테스트넷(Binance Spot Testnet, https://testnet.binance.vision)이다.
    실계좌로 전환하려면 BINANCE_LIVE_MODE=real 을 명시해야 한다.
  - 테스트넷 API 키는 실계좌 키와 별개로 위 사이트에서 GitHub 로그인 후 발급.
  - 주문 수량은 심볼별 최소 단위(stepSize)/최소 명목가(minNotional, 대부분 5 USDT) 제약이 있다.
    place_order는 amount_to_precision으로 stepSize를 보정하고, 최소 명목가는
    get_min_notional()로 노출해 루프가 미달 주문을 미리 거른다.

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
                # 서버-로컬 시간차를 load_markets 때 측정해 서명 타임스탬프를 보정한다(-1021 방지).
                # recvWindow는 기본값(10초)을 유지한다 — 늘려도 "미래" 타임스탬프 거부(-1021)는 안 풀리고
                # (2026-07-31 실측), 네트워크 지연된 시장가 주문이 최대 그만큼 늦게 체결될 여지만 커진다.
                "options": {"defaultType": "spot", "adjustForTimeDifference": True},
            }
        )
        if not self._live:
            self._exchange.set_sandbox_mode(True)
            print("[BinanceBrokerClient] 테스트넷 모드로 초기화됨")
        else:
            print(
                "[BinanceBrokerClient] ⚠️ 실계좌 모드로 초기화됨 — 실제 주문이 실계좌에 반영됩니다."
            )
        # amount_to_precision·get_min_notional·is_tradable이 마켓 메타데이터를 쓰므로 미리 로드
        self._exchange.load_markets()

    @property
    def is_live(self) -> bool:
        return self._live

    def _signed_call(self, fn, *args, **kwargs):
        """서명 필요한 호출 공통 래퍼.

        adjustForTimeDifference는 프로세스 시작 시 딱 한 번만 서버-로컬 시간차를 측정해
        캐싱한다 — 이 봇처럼 프로세스가 재시작 없이 몇 시간씩 떠 있으면 그 사이 로컬 시계가
        드리프트해 캐시된 오프셋이 틀어지고 -1021(InvalidNonce)이 반복 발생할 수 있다.
        InvalidNonce가 나면 시간차를 재측정해 한 번 재시도한다. -1021은 거래소가 요청을 처리하기
        전에 거부한 것이라 주문을 재시도해도 이중 체결되지 않는다.
        """
        try:
            return fn(*args, **kwargs)
        except ccxt.InvalidNonce:
            self._exchange.load_time_difference()
            return fn(*args, **kwargs)

    def check_api_key_safety(self) -> list[str]:
        """API 키 권한 점검 — 위험한 설정이면 경고 문구 목록을 반환한다(조회 실패 시 그 사실도 경고).

        이 봇에 필요한 권한은 현물 거래뿐이다. 출금 권한이 켜져 있거나 IP 제한이 없으면 키가 유출됐을 때
        계좌 자산을 그대로 빼갈 수 있다. 테스트넷에는 이 엔드포인트가 없으므로 실계좌에서만 점검한다.
        """
        if not self._live:
            return []
        try:
            r = self._signed_call(self._exchange.sapi_get_account_apirestrictions)
        except ccxt.BaseError as e:
            return [f"API 키 권한 조회 실패({e}) — 바이낸스 API Management에서 직접 확인할 것"]
        warnings = []
        if r.get("enableWithdrawals"):
            warnings.append("API 키에 출금 권한이 켜져 있음 — 끌 것(이 봇은 출금이 필요 없음)")
        if not r.get("ipRestrict"):
            warnings.append("API 키에 IP 제한이 없음 — 서버 공인 IP로 제한할 것")
        if r.get("enableFutures") or r.get("enableMargin"):
            warnings.append("API 키에 선물/마진 권한이 켜져 있음 — 현물 거래만 남길 것")
        return warnings

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
        balance = self._signed_call(self._exchange.fetch_balance)
        holdings = {
            f"{asset}/{QUOTE_CCY}": float(amounts)
            for asset, amounts in balance.get("total", {}).items()
            if asset != QUOTE_CCY and amounts
        }
        # USDT로 직거래 안 되는 자산은 제외하고, 시세는 한 번의 fetch_tickers로 모아 조회
        # (자산마다 fetch_ticker를 부르면 더스트가 많은 실계좌에서 사이클당 요청 수가 크게 늘어남)
        symbols = [s for s in holdings if s in self._exchange.markets]
        tickers = self._exchange.fetch_tickers(symbols) if symbols else {}
        positions = []
        for symbol in symbols:
            price = (tickers.get(symbol) or {}).get("last")
            if price is None:
                # 시세가 없는 자산(테스트넷 더스트/가짜 토큰, 거래정지 등)은 스킵
                continue
            price = float(price)
            positions.append(
                Position(
                    symbol=symbol,
                    quantity=holdings[symbol],
                    avg_price=price,  # ccxt 잔고 응답에는 평단가가 없어 현재가로 대체
                    current_price=price,
                )
            )
        return positions

    def get_cash_balance(self) -> float:
        balance = self._signed_call(self._exchange.fetch_balance)
        return float(balance.get("free", {}).get(QUOTE_CCY, 0.0))

    # ── 마켓 제약 ─────────────────────────────────────────────────────

    def is_tradable(self, symbol: str) -> bool:
        market = self._exchange.markets.get(symbol)
        return bool(market and market.get("active"))

    def get_min_notional(self, symbol: str) -> float:
        """심볼별 최소 주문 금액(USDT). 이 미만 주문은 거래소가 NOTIONAL 필터로 거부한다.

        markets.get을 쓴다 — market()은 모르는 심볼에 BadSymbol을 던져 사이클 전체를 중단시킨다.
        """
        market = self._exchange.markets.get(symbol) or {}
        min_cost = (market.get("limits", {}).get("cost") or {}).get("min")
        return float(min_cost) if min_cost else 5.0

    # ── 주문 ─────────────────────────────────────────────────────────

    def place_order(self, symbol: str, side: OrderSide, quantity: float) -> OrderResult:
        if quantity <= 0:
            raise ValueError("quantity는 양수여야 합니다")

        amount = quantity
        try:
            # stepSize 미만이면 InvalidOrder를 던지므로 try 안에서 보정해야 한 심볼의 실패가
            # 사이클 전체(나머지 심볼 주문)를 중단시키지 않는다
            amount = float(self._exchange.amount_to_precision(symbol, quantity))
            order = self._signed_call(
                self._exchange.create_order,
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
