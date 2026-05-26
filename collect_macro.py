"""
거시경제 보조 변수 수집 스크립트
- VIX              : yfinance ^VIX (미국 변동성지수, 일별)
- VKOSPI           : pykrx 1005 (한국 변동성지수, 일별)
- USD/KRW 환율      : yfinance USDKRW=X (일별)
- 한국 CPI          : FRED CPALTT01KRM657N (소비자물가지수 index, 월별)
- 한국 IP           : FRED KORPROMANMISMEI (제조업 생산지수, 월별)
- 한국 기준금리      : FRED IRSTCB01KRM156N (%, 월별)
- 한국 단기시장금리  : FRED IRSTCI01KRM156N (CD/인터뱅크 3개월물, 월별)
- 한국 장기시장금리  : FRED IRLTLT01KRM156N (국고채 10년물, 월별)

저장: data/macro_econ.parquet
월별 데이터는 forward-fill 로 일별로 reindex

필수 패키지:
  pip install yfinance pandas-datareader pykrx
"""

import os
import warnings
import datetime
import logging
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

START_DATE = "2020-01-01"
END_DATE = datetime.date.today().strftime("%Y-%m-%d")
OUT_PATH = "data/macro_econ.parquet"


# ── 1. yfinance: VIX, USD/KRW ────────────────────────────────────────────────
def collect_yfinance() -> dict[str, pd.DataFrame]:
    import yfinance as yf

    symbols = {
        "VIX":    "^VIX",       # 미국 변동성지수
        "USDKRW": "USDKRW=X",   # 원달러 환율 (1 USD = N KRW)
    }

    frames = {}
    for name, sym in symbols.items():
        try:
            raw = yf.download(sym, start=START_DATE, end=END_DATE,
                              progress=False, auto_adjust=False)
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = [col[0] for col in raw.columns]
            df = raw.reset_index()[["Date", "Close"]].rename(columns={"Close": name})
            df["Date"] = pd.to_datetime(df["Date"])
            frames[name] = df.set_index("Date")
            log.info(f"  [yfinance] {name} ({sym}): {len(df)}행")
        except Exception as e:
            log.warning(f"  [yfinance] {name} ({sym}) 실패: {e}")

    return frames


# ── 2. FRED: CPI, IP, 기준금리, 시장금리 ─────────────────────────────────────
def collect_fred() -> dict[str, pd.DataFrame]:
    """
    FRED 시리즈 (월별 → 일별 forward-fill 후 병합)

    CPALTT01KRM657N : 한국 CPI 지수 (2015=100, 월별)
    KORPROMANMISMEI : 한국 제조업 생산지수 IP proxy (2015=100, 월별)
    IRSTCB01KRM156N : 한국 기준금리 % p.a. (월별)
    IRSTCI01KRM156N : 한국 단기금리 — CD/인터뱅크 3개월물 (월별)
    IRLTLT01KRM156N : 한국 장기금리 — 국고채 10년물 (월별)
    """
    try:
        import pandas_datareader.data as web
    except ImportError:
        log.error("pandas_datareader 미설치: pip install pandas-datareader")
        return {}

    series = {
        "CPI_KR":        "CPALTT01KRM657N",
        "IP_KR":         "KORPROMANMISMEI",
        "BASE_RATE_KR":  "IRSTCB01KRM156N",
        "CD_RATE_KR":    "IRSTCI01KRM156N",
        "BOND_10Y_KR":   "IRLTLT01KRM156N",
    }

    frames = {}
    for name, fred_id in series.items():
        try:
            df = web.DataReader(fred_id, "fred", START_DATE, END_DATE)
            df.index = pd.to_datetime(df.index)
            df.index.name = "Date"
            df.columns = [name]
            frames[name] = df
            log.info(f"  [FRED] {name} ({fred_id}): {len(df)}행")
        except Exception as e:
            log.warning(f"  [FRED] {name} ({fred_id}) 실패: {e}")

    return frames


# ── 3. pykrx: VKOSPI ─────────────────────────────────────────────────────────
def collect_vkospi() -> dict[str, pd.DataFrame]:
    """
    KRX 지수 코드 1005 = VKOSPI (한국 변동성지수)
    pykrx 로 일별 종가 수집
    """
    try:
        from pykrx import stock
    except ImportError:
        log.error("pykrx 미설치: pip install pykrx")
        return {}

    start_str = START_DATE.replace("-", "")
    end_str = END_DATE.replace("-", "")

    try:
        df = stock.get_index_ohlcv(start_str, end_str, "1005")
        if df.empty:
            log.warning("  [pykrx] VKOSPI (1005): 데이터 없음")
            return {}
        df = df[["종가"]].rename(columns={"종가": "VKOSPI"})
        df.index = pd.to_datetime(df.index)
        df.index.name = "Date"
        log.info(f"  [pykrx] VKOSPI: {len(df)}행")
        return {"VKOSPI": df}
    except Exception as e:
        log.warning(f"  [pykrx] VKOSPI 실패: {e}")
        return {}


# ── 병합 + forward-fill ───────────────────────────────────────────────────────
def merge_and_ffill(daily_frames: dict, monthly_frames: dict) -> pd.DataFrame:
    """
    일별 기준 날짜 인덱스 생성 후
    월별 데이터는 forward-fill 로 업샘플링하여 병합
    """
    date_range = pd.date_range(start=START_DATE, end=END_DATE, freq="B")  # 영업일

    base = pd.DataFrame(index=date_range)
    base.index.name = "Date"

    # 일별 데이터 병합
    for name, df in daily_frames.items():
        base = base.join(df.rename(columns={df.columns[0]: name}), how="left")

    # 월별 데이터 → reindex + ffill
    for name, df in monthly_frames.items():
        col = df.reindex(date_range, method="ffill")
        base[name] = col[name]

    return base


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs("data", exist_ok=True)
    log.info(f"거시경제 데이터 수집 시작: {START_DATE} ~ {END_DATE}")

    log.info("\n── yfinance (일별) ──")
    yf_frames = collect_yfinance()

    log.info("\n── FRED (월별) ──")
    fred_frames = collect_fred()

    log.info("\n── pykrx VKOSPI (일별) ──")
    vkospi_frames = collect_vkospi()

    # 일별 / 월별 분리
    daily = {**yf_frames, **vkospi_frames}
    monthly = fred_frames

    log.info("\n── 병합 및 forward-fill ──")
    macro = merge_and_ffill(daily, monthly)

    log.info(f"\n최종 컬럼: {list(macro.columns)}")
    log.info(f"행수: {len(macro)}, 결측률:\n{macro.isna().mean().round(3).to_string()}")

    macro.to_parquet(OUT_PATH)
    log.info(f"\n→ 저장 완료: {OUT_PATH}")


if __name__ == "__main__":
    main()
