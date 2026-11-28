# shim v2(notes/margintrader_fix_prereg.md): funnel_f4_yf_shim.py와 같고, 열 순서 정정 한 가지만 추가.
# 최신 yfinance는 열을 알파벳순(Adj Close, Close, High, Low, Open, Volume)으로 돌려주는데, FinRL 0.3.6
# YahooDownloader.fetch_data는 열 이름을 위치로 붙인다(open, high, low, close, adjcp, volume). 그래서 평탄화 뒤
# 이름으로 구버전 순서 [Open, High, Low, Close, Adj Close, Volume]로 다시 정렬한다(그 밖의 열은 뒤에 둔다).
# 원 shim(funnel_f4_yf_shim.py)은 정정 전 F4·F7x 실행 기록으로 그대로 둔다.
import yfinance as yf
_orig = yf.download
_OLD_ORDER = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
def download(*args, **kw):
    kw.pop('proxy', None)
    kw.setdefault('auto_adjust', False)      # 구버전 기본값: Adj Close 열 포함, 가격 미조정
    kw.setdefault('progress', False)
    df = _orig(*args, **kw)
    if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    cols = list(df.columns)
    if len(df) > 0:
        assert all(c in cols for c in _OLD_ORDER), cols
    head = [c for c in _OLD_ORDER if c in cols]
    df = df[head + [c for c in cols if c not in head]]
    return df
yf.download = download
