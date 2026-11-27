# 사전 등록 — Margin Trader 탐색 재현의 데이터 열 오류 정정 재실행 (2026-11-27)

> 상태: 실행 전. 발견: F4·F7x Margin Trader 실행에서 FinRL 0.3.6 `YahooDownloader.fetch_data`가 열 이름을 위치로 붙이는데, 최신 yfinance는 열을 알파벳순(Adj Close, Close, High, Low, Open, Volume)으로 돌려준다. 그 결과 `close`(가격으로 쓰는 열)에 시가(raw Open)가, open/high/low에 각각 Adj Close/Close/High가 들어갔다(F7x data.csv, AAPL·MSFT·JPM 3,604일 전부 같은 패턴; OHLC 점검 2026-11-27). 다른 재현 데이터는 정상이었다. 우리 shim(`replication/funnel_f4_yf_shim.py`)의 결함이다(원 코드가 가정한 구버전 열 순서를 복원하지 않았다).

## 바꾸는 것(이것만)
- shim이 반환 열을 이름으로 구버전 순서 `[Open, High, Low, Close, Adj Close, Volume]`로 다시 정렬한다. FinRL 0.3.6 코드·Margin Trader 코드·설정·시드(0–4)·조건 P·기간·판정 규칙(`notes/funnel_f7x_margintrader_prereg.md`)은 그대로.
- 관문: 실행 전에 새 data.csv에서 AAPL 2009-01-02의 close가 실제 Adj Close와 같고(상대 차이 < 1e-6), high ≥ max(open, close)·low ≤ min(open, close) 위반 행이 0이어야 한다.

## 보고
- 같은 판정 규칙으로 다시 판정하고, 정정 전 결과와 나란히 보고한다. 6.13·7.5의 Margin Trader 문장은 정정 결과로 바꾸고 정정 사실을 적는다(정정 전 수치는 저장소 기록에만).
- 같은 비용 등가중 비교(`notes/ew_comparison2_prereg.md` (1))도 정정 데이터로 다시 계산한다.
- 실행 위치: 맥(기존 py310 환경 `~/f4mac` 계열) 또는 서버(F7x 환경). 서버는 C: 2GB 하한, 다른 실행과 겹치지 않게 순차로.
