"""
point-in-time 유니버스 보강용 임시 백필 스크립트.

2021-01-01 CMC 스냅샷 top-20 중 바이낸스에서 여전히 active인데(DOT/THETA/XTZ)
기존 universe.csv(오늘 기준 동적 선정) 50종목 풀에는 없어서 빠졌던 3종목만
collect_minute_data_binance.py와 동일한 로직으로 추가 백필한다.
universe.csv는 건드리지 않는다 — 기존 44/50종목 트랙과 완전히 분리된 보강.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "data" / "minute_ohlcv_raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "5m"
START_DATE = "2021-01-01"
LIMIT_PER_REQUEST = 1000

EXTRA_SYMBOLS = ["DOT/USDT", "THETA/USDT", "XTZ/USDT"]


def fetch_symbol_history(exchange: ccxt.Exchange, symbol: str, since_ms: int) -> pd.DataFrame:
    now_ms = exchange.milliseconds()
    rows = []
    cursor = since_ms

    while cursor < now_ms:
        batch = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, since=cursor, limit=LIMIT_PER_REQUEST)
        if not batch:
            break
        rows.extend(batch)
        last_ts = batch[-1][0]
        if last_ts <= cursor:
            break
        cursor = last_ts + 1
        if len(batch) < LIMIT_PER_REQUEST:
            break
        time.sleep(exchange.rateLimit / 1000)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset=["timestamp"])
    df["symbol"] = symbol
    return df


def backfill_symbol(exchange: ccxt.Exchange, symbol: str, since_ms: int) -> None:
    out_path = OUT_DIR / f"{symbol.replace('/', '')}.parquet"
    if out_path.exists():
        print(f"  스킵 (이미 존재): {symbol}")
        return

    df = fetch_symbol_history(exchange, symbol, since_ms)
    if df.empty:
        print(f"  데이터 없음: {symbol}")
        return

    df.to_parquet(out_path, index=False)
    print(f"  저장 완료: {symbol} ({len(df):,}행, {df['timestamp'].min()}~{df['timestamp'].max()})")


def main():
    exchange = ccxt.binance({"enableRateLimit": True})
    since_ms = int(datetime.strptime(START_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

    print(f"대상 심볼: {EXTRA_SYMBOLS} | {TIMEFRAME}봉 | {START_DATE} ~ 현재")
    for i, symbol in enumerate(EXTRA_SYMBOLS, 1):
        print(f"[{i}/{len(EXTRA_SYMBOLS)}] {symbol}")
        try:
            backfill_symbol(exchange, symbol, since_ms)
        except ccxt.BaseError as e:
            print(f"  오류({symbol}): {e} — 다음 심볼로 계속")
        time.sleep(exchange.rateLimit / 1000)


if __name__ == "__main__":
    main()
