"""
KOSPI 시계열 데이터 수집 스크립트
- 종목 리스트: kospi_stock_codes.csv
- 가격 데이터: yfinance (OHLCV + 수정종가)
- 기술적 지표: SMA, EMA, MACD, RSI, 거래 회전율, 볼린저 밴드
- 보조 변수: 국채 금리(^KTB10Y), BTC, ETH (시장 레벨)
- 저장: data/stocks/<종목코드>.parquet, data/market_aux.parquet
"""

import os
import time
import logging
import datetime
import warnings
import pandas as pd
import numpy as np
import yfinance as yf

warnings.filterwarnings("ignore")

# ── 설정 ──────────────────────────────────────────────────────────────────────
START_DATE = "2020-01-01"
END_DATE = datetime.date.today().strftime("%Y-%m-%d")
MARKET_SUFFIX = ".KS"           # 코스피
DELAY_BETWEEN = 0.4             # 요청 간 대기(초)
BATCH_SIZE = 50                 # 배치 후 추가 대기
BATCH_DELAY = 3.0
INPUT_CSV = "kospi_stock_codes.csv"
OUT_DIR = "data/stocks"
LOG_FILE = "data/collect_log.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/collect.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ── 기술적 지표 계산 ───────────────────────────────────────────────────────────
def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # SMA
    for w in [5, 10, 20, 60, 120]:
        df[f"SMA_{w}"] = close.rolling(w).mean()

    # EMA
    for w in [12, 26]:
        df[f"EMA_{w}"] = close.ewm(span=w, adjust=False).mean()

    # MACD
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    # RSI(14)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI_14"] = 100 - (100 / (1 + rs))

    # 볼린저 밴드 (20일)
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    df["BB_upper"] = bb_mid + 2 * bb_std
    df["BB_lower"] = bb_mid - 2 * bb_std
    df["BB_width"] = (df["BB_upper"] - df["BB_lower"]) / bb_mid

    # 거래 회전율 (Volume / 상장주식수 불명 → 거래대금 proxy)
    df["Volume_MA5"] = volume.rolling(5).mean()
    df["Volume_MA20"] = volume.rolling(20).mean()
    df["Volume_ratio"] = volume / df["Volume_MA20"]

    # 일간 수익률
    df["Return_1d"] = close.pct_change()
    df["Return_5d"] = close.pct_change(5)
    df["Return_20d"] = close.pct_change(20)

    # 변동성 (20일 rolling std of returns)
    df["Volatility_20d"] = df["Return_1d"].rolling(20).std()

    # ATR (Average True Range, 14일)
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    df["ATR_14"] = tr.rolling(14).mean()

    return df


# ── 단일 종목 다운로드 ─────────────────────────────────────────────────────────
def download_stock(code: str, name: str, suffix: str = MARKET_SUFFIX) -> pd.DataFrame | None:
    symbol = f"{code}{suffix}"
    try:
        raw = yf.download(
            symbol,
            start=START_DATE,
            end=END_DATE,
            progress=False,
            auto_adjust=False,
        )
        if raw.empty:
            return None

        # MultiIndex 컬럼 처리
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [col[0] for col in raw.columns]

        raw = raw.reset_index()
        raw.columns = raw.columns.str.strip()

        # 필수 컬럼 확인
        needed = {"Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"}
        if not needed.issubset(raw.columns):
            return None

        raw.insert(0, "종목코드", code)
        raw.insert(1, "종목명", name)
        raw = raw.rename(columns={"Adj Close": "Adj_Close"})

        raw = add_technical_indicators(raw)
        return raw

    except Exception as e:
        log.warning(f"  [ERROR] {symbol}: {e}")
        return None


# ── 보조 시장 변수 수집 ────────────────────────────────────────────────────────
def collect_market_aux():
    """국채 금리(^TNX proxy), BTC-USD, ETH-USD 수집"""
    symbols = {
        "BTC_USD": "BTC-USD",
        "ETH_USD": "ETH-USD",
        "US10Y": "^TNX",       # 미국 10년물 (한국 10년물 yfinance 미지원)
        "KOSPI_INDEX": "^KS11",
    }
    frames = {}
    for name, sym in symbols.items():
        try:
            df = yf.download(sym, start=START_DATE, end=END_DATE,
                             progress=False, auto_adjust=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            df = df.reset_index()[["Date", "Close"]].rename(columns={"Close": name})
            frames[name] = df.set_index("Date")
            log.info(f"  보조 변수 [{name}] 수집 완료: {len(df)}행")
        except Exception as e:
            log.warning(f"  보조 변수 [{name}] 실패: {e}")

    if frames:
        aux = pd.concat(frames.values(), axis=1).reset_index()
        os.makedirs("data", exist_ok=True)
        aux.to_parquet("data/market_aux.parquet", index=False)
        log.info("  → data/market_aux.parquet 저장 완료")
    return frames


# ── 메인 ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # 종목 리스트 로드
    stocks = pd.read_csv(INPUT_CSV, dtype=str)
    # 숫자 6자리 코드만 사용 (특수 코드 제외)
    stocks = stocks[stocks["종목코드"].str.match(r"^\d{6}$")].reset_index(drop=True)
    total = len(stocks)
    log.info(f"수집 대상: {total}개 종목 | 기간: {START_DATE} ~ {END_DATE}")

    # 이미 수집된 종목 스킵
    already_done = {
        f.replace(".parquet", "")
        for f in os.listdir(OUT_DIR) if f.endswith(".parquet")
    }
    log.info(f"이미 수집된 종목: {len(already_done)}개 → 스킵")

    results = []
    success, fail, skip = 0, 0, len(already_done)

    for i, row in stocks.iterrows():
        code = row["종목코드"]
        name = row["회사명"]
        sector = row.get("업종", "")

        if code in already_done:
            continue

        log.info(f"[{i+1}/{total}] {name}({code}) 수집 중...")
        df = download_stock(code, name)

        if df is not None and not df.empty:
            df["업종"] = sector
            out_path = os.path.join(OUT_DIR, f"{code}.parquet")
            df.to_parquet(out_path, index=False)
            success += 1
            results.append({"종목코드": code, "종목명": name, "상태": "OK",
                            "행수": len(df), "시작일": str(df["Date"].min()),
                            "종료일": str(df["Date"].max())})
            log.info(f"  → OK ({len(df)}일, {df['Date'].min().date()} ~ {df['Date'].max().date()})")
        else:
            fail += 1
            results.append({"종목코드": code, "종목명": name, "상태": "FAIL", "행수": 0})
            log.warning(f"  → SKIP (데이터 없음)")

        # API 부하 방지
        if (i + 1) % BATCH_SIZE == 0:
            log.info(f"  ── 배치 완료 ({i+1}/{total}), {BATCH_DELAY}초 대기 ──")
            time.sleep(BATCH_DELAY)
        else:
            time.sleep(DELAY_BETWEEN)

    # 수집 결과 로그
    log_df = pd.DataFrame(results)
    log_df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

    log.info("\n" + "=" * 60)
    log.info(f" 수집 완료: 성공 {success} | 실패 {fail} | 스킵 {skip}")
    log.info(f" 결과 로그 → {LOG_FILE}")

    # 보조 시장 변수 수집
    log.info("\n── 보조 시장 변수 수집 ──")
    collect_market_aux()

    # 전체 병합 파일 생성 (메모리 허용 시)
    log.info("\n── 전체 병합 parquet 생성 중... ──")
    try:
        all_files = [
            pd.read_parquet(os.path.join(OUT_DIR, f))
            for f in os.listdir(OUT_DIR) if f.endswith(".parquet")
        ]
        combined = pd.concat(all_files, ignore_index=True)
        combined.to_parquet("data/kospi_all.parquet", index=False)
        log.info(f" → data/kospi_all.parquet 저장 완료 ({len(combined):,}행, {combined['종목코드'].nunique()}종목)")
    except MemoryError:
        log.warning(" 메모리 부족으로 전체 병합 생략 (개별 parquet 파일 사용)")


if __name__ == "__main__":
    main()
