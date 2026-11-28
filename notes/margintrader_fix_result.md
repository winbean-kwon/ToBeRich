# Margin Trader 정정 재실행 — 결과: 관문 2 실패로 실행 중단 (2026-11-28)

> 사전 등록 `notes/margintrader_fix_prereg.md`(f885113). shim v2·실행기 `replication/funnel_f4_yf_shim_v2.py`, `replication/margintrader_fix_run.py`(dae5526).
> 관문 계산 `replication/margintrader_fix/gate.py`, 결과 `gate.json`, 데이터 기록 `data_info.json`.

## 1. 한 것
- 서버 WSL(F7x 환경 `~/f4work/mt/py310`: Python 3.10.12, FinRL 0.3.6, yfinance 0.2.65)에서 실행기의 데이터 받기 단계만 돌렸다(조건 H, 시드 0, 271초, rc 0). 그 실행의 성과 산출물(results/·모델·stdout)은 열지 않고 지웠다.
- 새 `data.csv`: sha256 980ecf8c…d0, 100,912행, 28종목(F7x와 행·종목 수 같음).
- 시드 실행(P·H 0–4)은 **하지 않았다.** 관문이 실패했기 때문이다.

## 2. 사전 판정(관문)
| 관문 | 기준 | 값 | 결과 |
|---|---|---|---|
| 1 | AAPL 2009-01-02 `close` = 실제 Adj Close, 상대 차이 < 1e-6 | 2.712238073 대 2.712236881(맥 yfinance 0.2.66, auto_adjust=False), 상대 차이 4.4e-7 | 통과 |
| 2 | env가 쓰는 프레임(`datasets/data.csv` = FeatureEngineer 뒤 저장본, 학습·시험·거래 분할은 이 파일의 부분집합) 전 행에서 high ≥ max(open, close), low ≤ min(open, close) 위반 0 | high 위반 0, **low 위반 98,794 / 100,912** | **실패** |

사전 등록과 지시대로 실험 1은 여기서 멈춘다.

## 3. 해석
- 열 순서 정정 자체는 된 것으로 보인다(판정 아님, 진단): AAPL 2009-01-02의 open/high/low가 Yahoo 원값 Open/High/Low와 정확히 같고(상대 차이 0), 전 행에서 high ≥ open ≥ low 위반이 0이며, close가 Adj Close와 같다. F7x 데이터의 어긋남(close에 시가, open에 Adj Close)은 없어졌다.
- 관문 2의 위반은 모두 `close < low`형이다(`close > high` 0행). FinRL 0.3.6 `YahooDownloader.fetch_data`(yahoodownloader.py 70행)는 `close`를 수정 종가(adjcp)로 바꾸고 open/high/low는 수정하지 않은 값으로 둔다. 배당·분할 누적 조정 계수가 하루 가격 폭보다 크면 수정 종가가 미수정 저가보다 낮아진다. 종목별 위반 행이 대부분 3,604일 전부에 가깝다(데이터 끝 무렵만 예외).
- 따라서 관문 2는 열 순서가 맞는 FinRL 프레임이면 거의 항상 실패하도록 쓰여 있었다. 관문 설계의 오류이고(수정 종가·미수정 OHL 혼합을 고려하지 않음), 데이터 열 오류의 증거는 아니다. 그래도 사전 판정은 "실패"이며 사후에 기준을 바꿔 통과로 읽지 않는다.
- 덧붙임: 같은 혼합 때문에 high·low를 쓰는 지표(cci_30, dx_30)는 수정 종가와 미수정 고가·저가를 섞어 계산된다. 이는 FinRL 코드의 성질이고 저자 실행에도 같이 있었을 것이다(구버전 yfinance 기준).

## 4. 다음(사용자 결정 사항)
- 재실행하려면 **실행 전에** 관문 2를 개정해 커밋해야 한다. 후보: (a) AAPL 2009-01-02 open/high/low가 원값 Open/High/Low와 같음(상대 차이 < 1e-6), (b) 전 행 high ≥ open, low ≤ open, high ≥ low, (c) close = Adj Close(관문 1 유지). 이번 진단값으로는 (a)–(c) 모두 충족하므로, 개정은 "결과를 본 뒤의 기준 변경"이라는 점을 개정 기록에 적어야 한다(성과 값은 아직 아무도 보지 않았다).
- 같은 스냅샷을 쓰도록 서버 `~/f4work/mt/out_fix/data.csv`(29 MB, sha256 980ecf8c…)는 지우지 않고 남겼다. 실행기는 이 파일이 있으면 데이터 받기를 건너뛴다. 받기 실행 폴더(`runs_fix/fetch`)는 지웠다.
- 같은 비용 등가중 비교(ew_comparison2 (1))도 하지 않았다(시드 실행 결과가 필요).

## 5. 한계
- 관문 1의 "실제 Adj Close"는 2026-11-28 맥에서 받은 값이다. Yahoo의 수정 종가는 새 배당이 생기면 과거 값이 바뀐다(4.4e-7 차이는 float32 저장 반올림 수준).
