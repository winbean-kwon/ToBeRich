"""
Binance 5분봉 히스토리 백필 스크립트.

크레온(collect_minute_data_creon.py)과 달리 Windows/COM 의존성이 없다 — Mac에서
바로 실행 가능. Binance 공개 시세 API는 API 키 없이도 OHLCV 히스토리 조회가
된다 (place_order 등 주문 관련 기능만 키가 필요).

⚠️ 사전 준비: `pip install ccxt pandas pyarrow`

대상: universe.get_top_usdt_symbols() 기준 거래대금 상위 N개 USDT 현물 심볼.
      선정된 유니버스는 재현성을 위해 data/universe.csv로 저장한다.

출력: data/minute_ohlcv_raw/{BASE}{QUOTE}.parquet (심볼당 1개, 이어받기 가능)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt
import pandas as pd

from crypto.universe import get_top_usdt_symbols

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "data" / "minute_ohlcv_raw"
UNIVERSE_CSV = ROOT / "data" / "universe.csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEFRAME = "5m"
UNIVERSE_SIZE = 50
START_DATE = "2021-01-01"  # 상장일이 이후인 심볼은 상장일부터 자연스럽게 수집됨
LIMIT_PER_REQUEST = 1000  # Binance klines 1회 최대 개수


def load_universe(exchange: ccxt.Exchange) -> list[str]:
    if UNIVERSE_CSV.exists():
        df = pd.read_csv(UNIVERSE_CSV)
        print(f"기존 유니버스 재사용: {UNIVERSE_CSV} ({len(df)}개)")
        return df["symbol"].tolist()

    symbols = get_top_usdt_symbols(UNIVERSE_SIZE, exchange=exchange)
    pd.DataFrame({"symbol": symbols}).to_csv(UNIVERSE_CSV, index=False)
    print(f"신규 유니버스 저장: {UNIVERSE_CSV} ({len(symbols)}개)")
    return symbols


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
            break  # 안전장치: 진행 안 되면 중단
        cursor = last_ts + 1
        if len(batch) < LIMIT_PER_REQUEST:
            break  # 최신까지 다 받음
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
    print(f"  저장 완료: {symbol} ({len(df):,}행)")


def main():
    exchange = ccxt.binance({"enableRateLimit": True})
    since_ms = int(datetime.strptime(START_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)

    symbols = load_universe(exchange)
    print(f"대상 심볼: {len(symbols)}개 | {TIMEFRAME}봉 | {START_DATE} ~ 현재")

    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {symbol}")
        try:
            backfill_symbol(exchange, symbol, since_ms)
        except ccxt.BaseError as e:
            print(f"  오류({symbol}): {e} — 다음 심볼로 계속")
        time.sleep(exchange.rateLimit / 1000)


if __name__ == "__main__":
    main()
