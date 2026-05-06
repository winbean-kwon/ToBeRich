"""
코스피/코스닥 전 종목 OHLCV + 수정종가 수집 스크립트
- 종목 리스트: KRX 웹사이트 직접 조회
- 가격 데이터: yfinance
- 저장: kospi_ohlcv.csv, kosdaq_ohlcv.csv
"""

import io
import time
import datetime
import pandas as pd
import yfinance as yf
import requests


def get_ticker_list_krx(market: str) -> pd.DataFrame:
    """KRX 웹사이트에서 코스피/코스닥 종목 리스트 직접 가져오기"""
    # 코스피: STK, 코스닥: KSQ
    market_code = "STK" if market == "KOSPI" else "KSQ"
    url = "http://kind.krx.co.kr/corpgeneral/corpList.do"
    params = {
        "method": "download",
        "searchType": "13",
        "marketType": market_code,
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, params=params, headers=headers)
    resp.encoding = "euc-kr"
    df = pd.read_html(io.StringIO(resp.text), header=0)[0]
    # 종목코드를 6자리 문자열로 변환
    df["종목코드"] = df["종목코드"].apply(lambda x: f"{x:06d}")
    return df[["종목코드", "회사명"]].rename(columns={"종목코드": "ticker", "회사명": "name"})


def get_ticker_list(market: str) -> pd.DataFrame:
    """종목 리스트 가져오기 (KRX 직접 조회)"""
    try:
        # pykrx 시도 (최근 5 영업일 순회)
        from pykrx import stock as pykrx_stock
        for i in range(10):
            date = (datetime.date.today() - datetime.timedelta(days=i)).strftime("%Y%m%d")
            tickers = pykrx_stock.get_market_ticker_list(date, market=market)
            if tickers:
                names = [pykrx_stock.get_market_ticker_name(t) for t in tickers]
                print(f"  (pykrx 사용, 기준일: {date})")
                return pd.DataFrame({"ticker": tickers, "name": names})
    except Exception as e:
        print(f"  pykrx 실패: {e}")

    # 백업: KRX 웹사이트 직접 조회
    print("  (KRX 웹사이트 직접 조회)")
    return get_ticker_list_krx(market)


def fetch_ohlcv(ticker_code: str, market_suffix: str, period: str = "1y") -> pd.DataFrame | None:
    """yfinance로 OHLCV + 수정종가 수집. 한국 종목은 .KS(코스피) / .KQ(코스닥) 접미사 사용."""
    symbol = f"{ticker_code}{market_suffix}"
    try:
        data = yf.download(symbol, period=period, progress=False, auto_adjust=False)
        if data.empty:
            return None
        data = data.reset_index()
        # yfinance MultiIndex columns 처리
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] if col[1] == "" else col[0] for col in data.columns]
        return data
    except Exception as e:
        print(f"  [ERROR] {symbol}: {e}")
        return None


def collect_market(market: str, suffix: str, output_file: str):
    """특정 시장 전 종목 수집 후 CSV 저장"""
    print(f"\n{'='*60}")
    print(f" {market} 종목 리스트 조회 중...")
    print(f"{'='*60}")

    ticker_df = get_ticker_list(market)
    total = len(ticker_df)
    print(f" 총 {total}개 종목 발견\n")

    all_data = []
    success, fail = 0, 0

    for idx, row in ticker_df.iterrows():
        code, name = row["ticker"], row["name"]
        print(f" [{idx+1}/{total}] {name}({code}) 수집 중...", end="")

        df = fetch_ohlcv(code, suffix)
        if df is not None and not df.empty:
            df.insert(0, "종목코드", code)
            df.insert(1, "종목명", name)
            all_data.append(df)
            success += 1
            print(f" OK ({len(df)}일)")
        else:
            fail += 1
            print(" SKIP (데이터 없음)")

        # API 부하 방지
        if (idx + 1) % 50 == 0:
            print(f"  ... {idx+1}/{total} 완료, 잠시 대기 중...")
            time.sleep(2)
        else:
            time.sleep(0.3)

    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        result.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"\n [완료] {output_file} 저장 ({success}종목 성공, {fail}종목 실패)")
    else:
        print(f"\n [경고] 수집된 데이터가 없습니다.")


if __name__ == "__main__":
    print("=" * 60)
    print(" 코스피/코스닥 전 종목 OHLCV 수집기 (최근 1년)")
    print("=" * 60)

    collect_market("KOSPI", ".KS", "kospi_ohlcv.csv")
    collect_market("KOSDAQ", ".KQ", "kosdaq_ohlcv.csv")

    print("\n 모든 수집 완료!")
