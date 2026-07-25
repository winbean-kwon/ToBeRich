"""
5분봉 원본 OHLCV → 전처리 + 기술지표 20개 피처 생성.

KOSPI 파이프라인(`kospi_valid.parquet`)의 20개 피처 구성을 5분봉에 그대로
이식한다. 윈도우 파라미터(20, 60, 12, 26, 14)는 "일" 대신 "봉" 단위로
해석한다 — 피처 차원 20을 유지해 기존 백본(Chronos+MTGNN) 입력 계약과
호환되게 하기 위함.

KOSPI 피처명 ↔ 크립토 피처명 매핑 (순서 동일):
  Adj_Close → close      | Return_1d → Return_1b
  Volatility_20d → Volatility_20b | 나머지는 동일

전처리:
  1. timestamp(ms) → UTC datetime, 5분 그리드로 reindex (거래소 장애 갭 보정)
     - close는 ffill, open/high/low는 보정된 close로 채움, volume은 0
  2. 히스토리 6개월(180일 = 51,840봉) 미만 심볼 제외
  3. 타겟: RetTarget_6b(30분 뒤 수익률), Target_6b(방향, 0/1)
  4. 워밍업 구간(SMA_60 NaN)과 마지막 6봉(타겟 NaN) 제거

출력: data/features_5m/{SYMBOL}.parquet (심볼별) + data/features_5m_summary.csv
"""

from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "minute_ohlcv_raw")
OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "features_5m")
SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "data", "features_5m_summary.csv")

BAR = "5min"
MIN_BARS = 180 * 288  # 6개월 (하루 288봉)
TARGET_HORIZON = 6  # 6봉 = 30분 (실거래 루프 리밸런싱 주기와 일치)

FEATURE_COLS = [
    "close", "open", "high", "low", "volume",
    "SMA_20", "SMA_60", "EMA_12", "EMA_26",
    "MACD", "MACD_signal", "MACD_hist", "RSI_14",
    "BB_upper", "BB_lower", "BB_width", "Volume_ratio",
    "Return_1b", "Volatility_20b", "ATR_14",
]


def load_and_regularize(path: str) -> pd.DataFrame:
    """원본 parquet을 읽어 완전한 5분 그리드로 정합화한다."""
    df = pd.read_parquet(path)
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.drop_duplicates(subset="datetime").set_index("datetime").sort_index()

    full_index = pd.date_range(df.index[0], df.index[-1], freq=BAR, tz="UTC")
    df = df.reindex(full_index)

    df["close"] = df["close"].ffill()
    for col in ("open", "high", "low"):
        df[col] = df[col].fillna(df["close"])
    df["volume"] = df["volume"].fillna(0.0)
    df["symbol"] = df["symbol"].ffill().bfill()
    return df.drop(columns=["timestamp"])


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """KOSPI 파이프라인과 동일한 구성의 기술지표 20개 + 타겟을 계산한다."""
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]

    df["SMA_20"] = c.rolling(20).mean()
    df["SMA_60"] = c.rolling(60).mean()
    df["EMA_12"] = c.ewm(span=12, adjust=False).mean()
    df["EMA_26"] = c.ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI_14"] = (100 - 100 / (1 + rs)).fillna(100.0)

    bb_mid = df["SMA_20"]
    bb_std = c.rolling(20).std()
    df["BB_upper"] = bb_mid + 2 * bb_std
    df["BB_lower"] = bb_mid - 2 * bb_std
    df["BB_width"] = (df["BB_upper"] - df["BB_lower"]) / bb_mid

    vol_sma = v.rolling(20).mean()
    df["Volume_ratio"] = (v / vol_sma.replace(0, np.nan)).fillna(0.0)

    df["Return_1b"] = c.pct_change()
    df["Volatility_20b"] = df["Return_1b"].rolling(20).std()

    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    df["ATR_14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()

    df["RetTarget_6b"] = c.shift(-TARGET_HORIZON) / c - 1
    df["Target_6b"] = (df["RetTarget_6b"] > 0).astype("int8")
    return df


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.parquet")))
    print(f"원본 파일 {len(files)}개 | 최소 봉수 기준 {MIN_BARS:,} (180일)")

    summary = []
    for path in files:
        name = os.path.basename(path).replace(".parquet", "")
        raw = pd.read_parquet(path, columns=["timestamp"])
        if len(raw) < MIN_BARS:
            print(f"  [스킵] {name}: {len(raw):,}봉 < 기준 (히스토리 부족)")
            summary.append({"symbol": name, "status": "skipped_short_history", "rows": len(raw)})
            continue

        df = load_and_regularize(path)
        n_gap = int((df["volume"] == 0).sum())
        df = add_features(df)

        # 워밍업(SMA_60 NaN) + 타겟 NaN 구간 제거
        df = df.dropna(subset=["SMA_60", "Volatility_20b", "RetTarget_6b"])
        df = df.reset_index().rename(columns={"index": "datetime"})

        out_path = os.path.join(OUT_DIR, f"{name}.parquet")
        df.to_parquet(out_path, index=False)
        summary.append({
            "symbol": name, "status": "ok", "rows": len(df),
            "start": df["datetime"].iloc[0], "end": df["datetime"].iloc[-1],
            "gap_bars_filled": n_gap,
        })
        print(f"  [완료] {name}: {len(df):,}봉 ({df['datetime'].iloc[0].date()} ~ {df['datetime'].iloc[-1].date()}, 갭보정 {n_gap}봉)")

    sdf = pd.DataFrame(summary)
    sdf.to_csv(SUMMARY_PATH, index=False)
    ok = sdf[sdf["status"] == "ok"]
    print(f"\n총 {len(ok)}개 심볼, {ok['rows'].sum():,}봉 → {OUT_DIR}")
    print(f"요약: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
