# F4 Margin Trader 기록 (JingyiGu/Margin-Trader @7b7fa9e)

프로토콜 `notes/funnel_protocol.md`. 대상: Gu, Du, Rahman, Wang, "Margin Trader: A Reinforcement Learning Framework for Portfolio Management with Margin and Constraints", ICAIF 2023. 정적 층 `notes/lit/f1/static_layer.csv` 순서 12(S-Q). F7 자리가 차서 **F4까지만** 진행한다(프로토콜 3.3-3).

## 0. 순서 이탈(2026-11-12, 실행 전, 성과 미열람)
프로토콜 3.3은 실행 층을 고정 순서로 진행한다. 서버 대기열은 RAT F7 R5 → li2019 → xiong2018(F4)이고, 그 뒤 순서 10(SmartFolio)·11(ADRL)이 남아 있다. 이 대상(순서 12)과 HARLF(순서 14)를 **맥에서 병행**한다(사용자 결정 2026-11-12).
- 이유: 3.3의 순서 고정은 F7 자리를 성과와 무관하게 배정하기 위한 것인데 F7 두 자리는 이미 찼다. F4만 남은 논문의 실행 순서는 판정에 영향을 주지 않는다. 11-24 마감 전에 "미시험(일정)"을 줄인다.
- 맥에서 고른 기준: 저장소가 작고(0.1MB), TF1이 필요 없으며(맥 M1에 TF1 없음), 데이터를 공개 경로로 받는다. SmartFolio(525MB, 맥 디스크 부족), ADRL(TF1), SCR(대형 데이터 파이프라인)은 맥에 맞지 않아 원래 순서(서버)로 둔다.
- 순서 10·11이 이 대상보다 늦게 실행될 수 있다. 결과 표에는 실행 장치와 시작 시각을 적는다.

## 1. 코드 읽기(정적, 2026-11-12)
- 저장소: HEAD `7b7fa9e`(2025-02-24, LICENSE 추가). 코드 변경 마지막 커밋은 `ea8fc36`(2024-04-05, `trading_margin_a2c.py` 1줄 수정). `2fd227f`(2024-07-08)은 사전 학습 모델 `agent_a2c.pth` 추가뿐이다(쓰지 않음).
- 실행 진입점 `trading_margin_a2c.py`: FinRL `YahooDownloader`로 FinRL `DOW_30_TICKER`를 2009-01-01~2023-05-01 받아 `FeatureEngineer`(기술 지표·VIX·난류)로 가공해 `./datasets/data.csv`에 저장한다. 학습 2009–2018, 검증(test) 2019-01~2020-04, 거래(trade) 2020-05~2023-05. A2C 50,000스텝, seed 0, `n_steps 5, gamma 0.99, lr 0.005, ent_coef 0.005, penalty 0.05`(argparse 기본값). 검증·거래 구간을 `turbulence_threshold=70, risk_indicator_col='vix'`로 평가하고 `results/<시각>/a2c/` 아래에 성과 CSV·그림을 쓴다.
- 정적 층 비고(재기록): 스크립트는 A2C만 있다. 논문의 4개 알고리즘·최종 하이퍼파라미터·λ2 값은 적혀 있지 않다. FinRL 버전이 고정돼 있지 않아 종목 목록이 버전에 따라 바뀔 수 있다.
- 의존성: README는 "FinRL, Python 3.10, torch"만 적는다. 코드는 `finrl.main.check_and_make_directories`, `finrl.plot`(pyfolio), `finrl.meta.preprocessor.*`, gymnasium 기반 env, stable-baselines3를 쓴다.

## 2. F4 사전 등록(2026-11-12, 실행 전, 성과 미열람)

### 2.1 환경(맥 M1, CPU)
- Python 3.10.22(conda-forge, README 명시 3.10).
- FinRL **0.3.6**(PyPI sdist, sha256 1294e43c…c6d9, 2023-02-07): 논문(ICAIF 2023, 11월)과 저장소 코드 커밋(2024-04-05) 시점에 배포된 최신판이다(0.3.7은 2024-04-12). sdist의 `python_requires`가 `<3.9`라 `--ignore-requires-python --no-deps`로 설치한다(README의 3.10 지시를 따름). 설치된 파일은 sdist 원본과 같다(diff 확인). pip 메타데이터의 판 표기는 0.3.5로 나온다(egg-info 표기 문제).
- 의존성(직접 설치, 버전 고정): stable-baselines3 2.0.0, gymnasium 0.28.1, gym 0.26.2, torch 2.9.0, pandas 1.5.3, numpy 1.26.4, matplotlib 3.7.5, stockstats 0.6.11, pyfolio-reloaded 0.9.9, yfinance 0.2.65, tensorboard 2.21.0, alpaca-trade-api 3.2.0, exchange_calendars 4.13.2, wrds 3.1.6(뒤 셋은 `import finrl`이 끌어오는 모듈이며 이 경로에서 쓰지 않음), websockets 16.1.1.

### 2.2 허용 수정(v3 2.3)
1. **호환 shim(2.3-1):** `replication/funnel_f4_yf_shim.py`. FinRL 0.3.6 `YahooDownloader`는 `yf.download(..., proxy=...)`가 단일 레벨 컬럼(Open·High·Low·Close·Adj Close·Volume)을 돌려준다고 가정한다. 현재 yfinance는 `proxy` 인자가 없고 다단 컬럼을 돌려주며, 옛 yfinance(0.2.54·0.2.58 시험)는 지금 Yahoo 응답과 맞지 않아 실패한다. shim은 `proxy`를 버리고, 구버전 기본값(`auto_adjust=False`)을 주고, 다단 컬럼의 첫 레벨만 남긴다. 저자 코드와 FinRL 파일은 고치지 않는다. 실행 래퍼가 shim을 먼저 import한 뒤 `runpy`로 저자 스크립트를 그대로 실행한다.
2. 실행 인자: 없음(저자 스크립트 기본값). 그림 백엔드 `MPLBACKEND=Agg`.

### 2.3 판정
- **F4 통과:** rc = 0이고 `results/*/a2c/perf_stats_trade.csv`가 생김(학습 → 검증 평가 → 거래 평가 끝까지 실행). 존재만 확인하고 열지 않는다.
- **F4 실패:** rc ≠ 0 또는 표지 없음. stderr 마지막 40줄만 열어 원인을 적는다(성과는 stdout으로만 나간다). 허용 수정 범위 안에서 고칠 수 있으면 고쳐 최대 3회. 넘으면 "F4 실패".
- **상한:** 1회 벽시계 3시간. 넘으면 "상한 내 미완".
- **데이터 기록(성과 아님):** 받은 `data.csv`의 sha256·행 수·종목 목록을 기록한다. 재수집 데이터라 저자 데이터와 다를 수 있다(F3 유형 "재수집").
- **성과 비노출:** stdout(성과표 print), `results/` 아래 CSV·그림, tensorboard 로그를 열지 않는다. F7 대상이 아니므로 성과는 이 연구에서 쓰지 않는다.

스크립트: `replication/funnel_f4_margintrader_mac.py`(이 절과 같은 커밋). 결과 기록은 `~/f4mac/out/margintrader/`.

**설치 정정(2026-11-12, 시도 1 뒤, 성과 미열람):** 시도 1은 0.7초 만에 `ModuleNotFoundError: typing_extensions`로 끝났다(rc 1, 시도 1회로 셈). 사전 설치 확인은 사용자 site-packages(`~/.local/lib/python3.10`)가 섞인 상태였고, 실행 래퍼는 `PYTHONNOUSERSITE=1`로 이를 막는다. 같은 조건의 import 관문(`finrl`·`finrl.main`·`finrl.plot`·전처리·`env.marginEnv`·`env.agent`·SB3 tensorboard 로거)이 통과할 때까지 빠진 패키지를 env에 설치했다: typing_extensions 4.16.0, torch 2.14.1(2.1의 2.9.0은 사용자 site의 판이었음 — 정정), requests 2.34.2, aiohttp 3.14.5. 저자 코드·FinRL 파일 변경 없음. 시도 2로 진행한다.
