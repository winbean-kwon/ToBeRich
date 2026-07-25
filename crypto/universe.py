"""
Binance USDT 마켓 유니버스 선정.

KOSPI 파이프라인의 `cluster_assignments.csv`(757종목 고정 유니버스)에 대응하는
개념이지만, 코인은 상장/상폐가 잦고 거래대금 순위도 자주 바뀌므로 고정 CSV
대신 매번 거래대금 기준으로 동적 산출한다.
"""

from __future__ import annotations

import ccxt

QUOTE_CCY = "USDT"
EXCLUDE_BASE_SUBSTRINGS = ("UP", "DOWN", "BULL", "BEAR")  # 레버리지 토큰 제외
EXCLUDE_STABLE_BASES = {"USDC", "BUSD", "TUSD", "DAI", "FDUSD", "USDP", "EUR"}


def get_top_usdt_symbols(n: int = 50, exchange: ccxt.Exchange | None = None) -> list[str]:
    """24시간 거래대금(quoteVolume) 기준 상위 N개 USDT 현물 심볼 반환. 예: ["BTC/USDT", ...]"""
    ex = exchange or ccxt.binance({"enableRateLimit": True})
    markets = ex.load_markets()
    tickers = ex.fetch_tickers()

    candidates = []
    for symbol, market in markets.items():
        if not market.get("spot") or market.get("quote") != QUOTE_CCY:
            continue
        base = market["base"]
        if base in EXCLUDE_STABLE_BASES:
            continue
        if any(s in base for s in EXCLUDE_BASE_SUBSTRINGS):
            continue
        ticker = tickers.get(symbol)
        if not ticker or ticker.get("quoteVolume") is None:
            continue
        candidates.append((symbol, ticker["quoteVolume"]))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return [symbol for symbol, _ in candidates[:n]]


if __name__ == "__main__":
    for sym in get_top_usdt_symbols(50):
        print(sym)
