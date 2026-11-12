# 허용 수정 1(v3 2.3): yfinance 구버전 API 의미 복원. FinRL 0.3.6 YahooDownloader는
# yf.download(ticker, start, end, proxy=...)가 단일 레벨 컬럼(Open High Low Close Adj Close Volume)을 준다고 가정한다.
import yfinance as yf
_orig = yf.download
def download(*args, **kw):
    kw.pop('proxy', None)
    kw.setdefault('auto_adjust', False)      # 구버전 기본값: Adj Close 열 포함, 가격 미조정
    kw.setdefault('progress', False)
    df = _orig(*args, **kw)
    if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    return df
yf.download = download
