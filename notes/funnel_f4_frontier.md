# 깔때기 FRONTIER 기록 (W22_PretoriusVanZyl, ruankie/frontier-rl)

대상: Pretorius & van Zyl, "Deep Reinforcement Learning and Convex Mean-Variance Optimisation for Portfolio Management", arXiv:2203.11318(TechRxiv 10.36227/techrxiv.19165745.v1, IEEE TAI 양식, 출판 미확인). 표본 S56. 프로토콜 `notes/funnel_protocol.md`.

## 0. 이탈 기록(2026-11-21, 정적 단계 시작 전, 성과 미열람)
- **F1:** 원래 판정 `not_found`(Claude, 본문만 확인하고 1저자 GitHub를 확인하지 않음). F1 재확인에서 사용자가 1저자 계정 저장소 `github.com/ruankie/frontier-rl`을 찾았다(`notes/lit/f1/f1_recheck_log.md`). 층 1 거짓 음성이다.
- **사전 등록 이탈:** `notes/f1_recheck_prereg.md`의 "미통과가 통과로 바뀐 논문은 후속 단계(F2 이후)를 이번 일정에서 실행하지 않는다"에서 이탈한다. 사용자 결정(2026-11-21)이다. 이유: 연구 질문이 공개 코드로 보고 수치 재현을 시도하는 것이고, 다른 작업과 병행할 수 있다. 이 이탈은 이 논문이 어떤 성과를 내는지 보기 전에 정했다.
- **집계 처리:** 프로토콜 3.3의 F7 두 자리(Ensemble, RAT)는 이미 찼다. 이 논문의 F2 이후 결과는 **탐색적(F1 재확인 후 추가, 프로토콜 3.3 밖)**이다. 깔때기 표에는 "F1 재확인에서 찾음"으로 적고 후속 단계는 탐색적 비고로만 적는다. F1 재확인의 주 지표 계산은 이 결과와 무관하다.
- **이미 본 정보(2026-11-21):** 원문의 표는 Table I(시장 데이터)과 Table II(Yang et al. 2020의 DDPG·PPO·A2C를 선형·비선형 거래비용으로 비교: 초과수익률·초과위험·Sharpe)뿐이다. 제안 모델 FRONTIER의 성과는 그림(파레토 프런티어)에만 있다. 저장소 커밋 메시지 목록을 보았다(`aaf09ac` "reproduced findings for long-only policy" 등). 저장소의 `experiments/*/backtests/*.csv`(저자 실행 결과)는 열지 않았다.
- **성과 비노출:** 저장소의 `experiments/` 아래 결과 파일과 노트북 출력 셀은 열지 않는다(저자 결과 노출 방지). 코드 셀만 읽는다. 우리 실행의 성과는 F7 사전 등록 전에는 열지 않는다(프로토콜 2.2).

## 1. 정적 단계(F2·F6·F3, 2026-11-21, 코드·원문만 읽음)
**코드 버전(2.1).** 저장소는 2022-04-09 생성(arXiv 초판 2022-03, TechRxiv 2022-02-21보다 늦음)이라 초판 직전 커밋이 없다. 가장 이른 코드 커밋은 `f04dbb3`("added original project files")이고, 같은 날 `e019ce4`가 데이터를 추가하며 코드를 `code/REINFORCE/`로 옮겼다. 두 커밋의 코드 파일은 같다(rename만, `git diff -M`에서 README만 다름). **주 대상은 `e019ce4`**(코드는 가장 이른 판과 동일, 데이터 포함, 노트북의 `DATA_DIR='../../data/...'`가 이 배치에서 맞음). `experiments/`가 없어 저자 결과가 들어 있지 않다. HEAD(`main`)는 공매도 확장판이라 쓰지 않는다("출판 후 수정").

**F2 통과.** 학습 진입점 `code/REINFORCE/train_template.ipynb`, 평가 진입점 `backtest_template.ipynb`(둘 다 papermill `parameters` 태그 셀), 환경·보상·정책망 `REINFORCE_soft.py`(`MultiStockEnv`, 보상 = 수익 − γ_trade·거래비용 − γ_risk·위험, REINFORCE 갱신), 모델 설정 `model_config.py`(RL_CNN·RL_str_fcast·RL_all_inp = 논문의 log-returns·forecast-only·all-inputs 정책망).
비고(논문–코드):
- 병렬 실행기 `train_parallel.py`는 이 커밋에서 정의되지 않은 이름(`split_seeds`, `train_rl`)을 불러 그대로는 돌지 않는다. 노트북을 papermill 인자로 직접 실행하면 된다.
- 노트북 기본 인자(TEST_5 5종목, 2017-01-03~2019-01-01)는 논문 설정이 아니다. 시장·기간은 인자로 준다(`train_config.json`은 LA_40만 적힘).
- 에피소드 수 200(노트북 기본값)은 논문에 적혀 있지 않다. γ 격자 24×21=504쌍은 논문과 같다.
- 거래비용 `HALF_SPREAD = 0.0005/2`. 논문은 FRONTIER의 a 값을 따로 확인하지 않았다(Table II 설명의 a=0.0005는 FinRL 비교용).
- SPO·MPO·EW(cvxportfolio)와 FinRL 기준선 코드는 저장소에 없다.

**F6 그림 판독.** 원문의 수치 표는 Table I(시장·기간)과 Table II(FinRL DDPG·PPO·A2C, 거래비용 함수 비교)뿐이다. FRONTIER의 성과는 Fig. 7·8의 평균 파레토 프런티어(초과위험–초과수익, 시드 10개, 95% 구간)에만 있다. 본문 수치는 LatAm의 FinRL 기준선(−28.4%, −29.4%, −35.5%)뿐이다. 시험 구간: Dow 30·Nikkei 2018-01-01~2020-01-01, LatAm 2014-12-01~2016-01-01.

**F3 번들.** `e019ce4`의 `data/{DOW_30,NIK_25,LA_40}/preprocessed_data/`에 가공된 수익률·로그수익률·변동성·거래량·수익 예측(`return_estimate`)이 있다. 종목 수 30·24·24(`market_tickers.py` 목록과 일치, 현금 `USDOLLAR` 포함). 기간: DOW 2009-11-03~2020-01-31, NIK 2013-01-07~2020-01-31, LA 2009-12-02~2016-01-29. 원 수집 코드(`data/data_manager.py`)는 Quandl 키가 필요하지만 실행에는 번들 파일만 쓴다.

## 2. F4·F5 사전 등록(2026-11-21, 실행 전, 성과 미열람)
### 2.1 환경(서버 WSL2 Ubuntu, i5-9300H 8코어, CPU, WSL 메모리 3GB)
- micromamba로 Python 3.7(conda-forge 3.7 계열 최신. 저자 Dockerfile `python:3.7.6-slim`, 논문 "Python 3.7, TensorFlow 2.4").
- pip: `requirements.txt`의 주석 아닌 판 중 실행 경로에 필요한 것 — tensorflow 2.4.0, numpy 1.19.5, pandas 1.0.1, matplotlib 3.1.3, scipy 1.4.1, six 1.15.0. 설치가 안 되면 가장 가까운 판으로 바꾸고 기록한다. 설치 뒤 `pip freeze`를 저장한다.
- 맥 M1에는 TF 2.4 휠이 없어 쓰지 않는다.

### 2.2 허용 수정
1. 실행기 `replication/funnel_f4_frontier_wsl.py`: papermill과 같은 방식으로 저자 노트북의 코드 셀을 순서대로 실행하고, `parameters` 셀 직후에 인자를 덮어쓴다. 셀 매직(`%%time`)만 지운다. 저자 파일은 고치지 않는다.
2. 시간 측정: `play_one_episode`와 `MultiStockEnv.__init__`을 시간 기록용으로 감싼다(반환값 그대로). 손실·지표는 저장하지 않는다. 표준출력은 파일로만 보내고 열지 않는다.
3. `MPLBACKEND=Agg`.

### 2.3 실행(시드 0, Dow 30, 에피소드 2)
- **학습:** 세 모델(RL_CNN, RL_str_fcast, RL_all_inp) 각각, 504쌍 전부, `NB_EPISODES=2`, 기간 2010-01-01~2018-01-01(논문 Table I 학습 구간). 순서 RL_CNN → RL_str_fcast → RL_all_inp, 단일 프로세스로 하나씩 실행한다.
- **평가(성과 비노출):** RL_CNN만, 위 모델로 `backtest_template` 경로를 2016-01-01~2018-01-01(**학습 구간 안의 조각**)에 돌린다. 결과 CSV는 존재만 확인하고 열지 않는다.
- Dow 30을 쓰는 이유: 종목이 가장 많아(30) 시간 환산이 보수적이다.

### 2.4 판정
- **F4 통과:** 세 모델 모두 예외 없이 끝나고 각 504쌍의 최종 가중치가 저장되며, 저자 코드의 오류 문자열("*** error in episode", "**error for model") 수가 0이고, 평가 결과 CSV가 생김. 오류면 원인만 확인해 허용 수정 범위에서 고친다(최대 3회, 벽시계 8시간). 넘으면 "F4 실패".
- **F5 환산(시드당 = 논문 절차의 1 시드 전체 학습 = 3시장 × 3모델 × 504쌍 × 200에피소드):**
  `H = 3 × Σ_모델 504 × (s_m + 200 × e_m) / 3600`
  - `e_m` = 모델 m의 에피소드 평균 시간(첫 쌍 제외).
  - `s_m` = 쌍마다 (쌍 소요 − 그 쌍의 에피소드 시간 합)의 평균(첫 쌍과 마지막 쌍 제외, 환경 생성·저장·그림 포함).
  - Nikkei·LatAm(24종목)도 Dow 값으로 환산한다(상한 쪽).
- H ≤ 10시간이면 F5 통과, 넘으면 "한도 초과(서버 i5-9300H CPU, 단일 프로세스)". 8코어 병렬 환산은 탐색적 기록으로만 적는다.
- 평가 시간(504쌍 백테스트)은 환산에 넣지 않고 따로 적는다.
- F5 이후(F7)는 이 결과를 본 뒤 별도 사전 등록과 반박 심사를 거쳐 정한다. 어느 경우에도 탐색적이다(0절).
