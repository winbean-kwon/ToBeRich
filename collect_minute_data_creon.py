"""
대신증권 크레온(CYBOS) Plus API — 5분봉 히스토리 백필 스크립트.

⚠️ 실행 환경: Windows 32bit Python 전용 (COM 기반). Mac에서는 실행 불가 —
   Parallels(Windows VM) 또는 클라우드 Windows 인스턴스에서 실행할 것.
⚠️ 사전 준비: 대신증권 계좌 개설 + 크레온 Plus 설치/로그인 상태에서 실행.
⚠️ 필드 인덱스(SetInputValue/GetDataValue 순서)는 크레온 Plus 개발가이드
   (HTS 내 "PLUS 개발가이드" 메뉴)와 반드시 대조 후 사용할 것. 아래 값은
   공개된 CpSysDib.StockChart 예제 관례를 따른 초안이며, 버전에 따라
   달라질 수 있다.

대상: cluster_assignments.csv 기준 종목코드(757개, kospi_valid.parquet와
동일 유니버스) × 5분봉 × 2021-01-01 ~ 오늘.

출력: data/minute_ohlcv_raw/{ticker}.parquet (종목당 1개, 이어받기 가능)
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

if sys.platform != "win32":
    raise RuntimeError(
        "크레온 Plus는 Windows COM 기반입니다. Windows 환경에서 실행하세요."
    )

import win32com.client  # noqa: E402

ROOT = Path(__file__).resolve().parent
CLUSTER_CSV = ROOT / "cluster_assignments.csv"
OUT_DIR = ROOT / "data" / "minute_ohlcv_raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TICK_INTERVAL_MIN = 5  # 분봉 간격 (5분봉)
START_DATE = "20210101"
END_DATE = datetime.today().strftime("%Y%m%d")
CHUNK_DAYS = 90  # 요청 1회당 조회 기간 (제한 회피용 분할)
REQUEST_SLEEP_SEC = 0.25  # 초당 요청 제한 대응 (크레온 통상 15~20건/초)

# StockChart 출력 필드 인덱스 (요청구분='2', 필드=(0,1,2,3,4,5,8))
# 0:날짜 1:시간 2:시가 3:고가 4:저가 5:종가 8:거래량 — 반드시 개발가이드 대조
FIELD_ORDER = ["date", "time", "open", "high", "low", "close", "volume"]


def connect_creon() -> None:
    cybos = win32com.client.Dispatch("CpUtil.CpCybos")
    if cybos.IsConnect:
        print("크레온 연결 확인됨")
        return
    raise RuntimeError(
        "크레온 Plus에 로그인되어 있지 않습니다. HTS/영웅문Plus를 먼저 실행하세요."
    )


def load_tickers() -> list[str]:
    df = pd.read_csv(CLUSTER_CSV, dtype={"종목코드": str})
    codes = df["종목코드"].str.zfill(6).unique().tolist()
    return [f"A{c}" for c in codes]  # 크레온은 종목코드 앞에 'A' 접두 필요


def fetch_minute_chart(
    obj_chart, ticker: str, start_yyyymmdd: str, end_yyyymmdd: str
) -> pd.DataFrame:
    """기간요청(요청구분='1')으로 5분봉 조회. 한 번에 CHUNK_DAYS 만큼."""
    obj_chart.SetInputValue(0, ticker)
    obj_chart.SetInputValue(1, ord("1"))  # 1:기간요청
    obj_chart.SetInputValue(2, int(end_yyyymmdd))
    obj_chart.SetInputValue(3, int(start_yyyymmdd))
    obj_chart.SetInputValue(5, (0, 1, 2, 3, 4, 5, 8))
    obj_chart.SetInputValue(6, ord("m"))  # m: 분봉
    obj_chart.SetInputValue(7, TICK_INTERVAL_MIN)
    obj_chart.SetInputValue(9, ord("1"))  # 수정주가 반영

    obj_chart.BlockRequest()

    rq_status = obj_chart.GetDibStatus()
    if rq_status != 0:
        raise RuntimeError(f"조회 실패({ticker}): status={rq_status}, msg={obj_chart.GetDibMsg1()}")

    n = obj_chart.GetHeaderValue(3)  # 수신 데이터 개수
    rows = []
    for i in range(n):
        rows.append({field: obj_chart.GetDataValue(j, i) for j, field in enumerate(FIELD_ORDER)})
    return pd.DataFrame(rows)


def daterange_chunks(start: str, end: str, chunk_days: int):
    start_dt = datetime.strptime(start, "%Y%m%d")
    end_dt = datetime.strptime(end, "%Y%m%d")
    cur = start_dt
    while cur <= end_dt:
        chunk_end = min(cur + timedelta(days=chunk_days), end_dt)
        yield cur.strftime("%Y%m%d"), chunk_end.strftime("%Y%m%d")
        cur = chunk_end + timedelta(days=1)


def backfill_ticker(obj_chart, ticker: str) -> None:
    out_path = OUT_DIR / f"{ticker[1:]}.parquet"
    if out_path.exists():
        print(f"  스킵 (이미 존재): {ticker}")
        return

    chunks = []
    for chunk_start, chunk_end in daterange_chunks(START_DATE, END_DATE, CHUNK_DAYS):
        df = fetch_minute_chart(obj_chart, ticker, chunk_start, chunk_end)
        if not df.empty:
            chunks.append(df)
        time.sleep(REQUEST_SLEEP_SEC)

    if not chunks:
        print(f"  데이터 없음: {ticker}")
        return

    full = pd.concat(chunks, ignore_index=True).drop_duplicates(subset=["date", "time"])
    full["ticker"] = ticker[1:]
    full.to_parquet(out_path, index=False)
    print(f"  저장 완료: {ticker} ({len(full):,}행)")


def main():
    connect_creon()
    obj_chart = win32com.client.Dispatch("CpSysDib.StockChart")
    tickers = load_tickers()
    print(f"대상 종목: {len(tickers)}개 | 기간: {START_DATE} ~ {END_DATE} | {TICK_INTERVAL_MIN}분봉")

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}")
        try:
            backfill_ticker(obj_chart, ticker)
        except Exception as e:
            print(f"  오류({ticker}): {e} — 다음 종목으로 계속")


if __name__ == "__main__":
    main()
