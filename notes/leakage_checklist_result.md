# 결과: 공식 코드 누설 정적 체크리스트 (2026-11-27)

> 사전 등록 `notes/leakage_checklist_prereg.md`(9f95cfc). 항목·정의·코드 규칙은 바꾸지 않았다. 평가자 Claude 1명, 비맹검, 정적 읽기만. 코드를 실행하지 않았고 성과 파일은 열지 않았다. 이 표는 기술표다. 판정(유효/무효)이나 분야 빈도 주장은 하지 않는다. 탐색적 대상(X1–X4)은 "탐색적"이다.
> 읽은 위치: 로컬 `.t1env/DeepAries`, `.t3env/fm`, `.marswork/L`(git 2561606 확인), `.audit/wavecorr`(서버 @20ff832 사본과 md5 7개 파일 일치), `~/f4mac/p2407`(저자 스크립트 사본, FinRL @55764e8 설치본). 서버(읽기 전용): `~/f4work/ensemble/repo`(@f02a762), `~/f4work/RAT`(@d1cbe96, 로컬 `.audit/rat/main.py`와 914행 주석 1곳만 다름 — 서버 판을 읽음), `~/f4work/frontier/repo`(@e019ce4), `~/f4work/mt/repo`(@7b7fa9e, 설치된 finrl dist-info 0.3.5). raw.githubusercontent 고정 커밋 파일: PRUDEX-Compass @2b62831 7개(`AlphaMix+/PM/AlphaMix+_sz50.py`, `rl_env/portfolio_management.py`, `rlkit/core/batch_rl_algorithm.py`, `finrl/finrl_meta/preprocessor/preprocessors.py`, `.../processor_yahoofinance.py`, `finrl/apps/config.py`, `data/portfolio_management/AlphaMix+/sz50.ipynb`), BellmanMarkwitzProject @93c273f 2개(`profilo management/produce_raw_data.py`, `data_process.py`)와 트리 목록. 서버 C: 여유 6.53 GB 확인 후 시작, 읽기 끝에 `wsl --shutdown` 실행.
> 판 미확인: DeepAries 로컬 사본은 `.git`이 없다(기록 판 634f559, 대조 안 함). FinRL-Meta `.t3env/fm`도 `.git`이 없다(기록 판 286fef6, 이전 노트에서 env 파일 md5만 대조). T3 데이터 경로는 튜토리얼을 옮긴 우리 스크립트(`replication/finrl_t3_run.py`, `finrl_t3_timing.ipynb`)를 함께 읽었다.

## 1. 요약표

예 = 경로가 코드에 있음, 아니오 = 관련 코드를 읽었고 경로 없음, 해당 없음 = 그 단계가 없음, 미정 = 결정 못 함(이유는 2절). "경미"는 영향 범위가 학습 시작부 등으로 좁다는 기술이며 판정이 아니다.

| 대상 | L1 정규화 | L2 특성 시점 | L3 분할 겹침 | L4 시험 기반 선택 | L5 시험 지표 기록 | L6 유니버스 | L7 보상·목표 정렬 | L8 기타 |
|---|---|---|---|---|---|---|---|---|
| T1 DeepAries | 아니오 | 아니오 | 아니오 | 아니오 | 예 | 예 | 아니오 | 없음 발견 |
| T2 AlphaMix+ | 해당 없음 | 예(경미) | 아니오 | 예(SZ50 노트북) / DJ30 미정 | 예 | 예 | 아니오 | 없음 발견 |
| T3 FinRL SPE | 해당 없음 | 아니오 | 아니오 | 아니오 | 아니오 | 예 | 아니오 | 예(미발동 경로) |
| T4 MARS L | 아니오 | 아니오 | 아니오 | 아니오 | 아니오 | 미정 | 예 | 없음 발견 |
| E Ensemble | 해당 없음 | 예(경미) | 아니오 | 아니오 | 아니오 | 예 | 아니오 | 미정 |
| R RAT | 아니오 | 예(정도 미정) | 아니오 | 예 | 예 | 아니오 | 아니오 | 없음 발견 |
| X1 FRONTIER (탐색적) | 아니오(조건부 경로) | 예 | 예(경미) | 아니오 | 아니오 | 예 | 아니오 | 예(설계, 판정 모델 밖) |
| X2 P24-07 (탐색적) | 해당 없음 | 미정 | 아니오 | 미정 | 아니오 | 예 | 아니오 | 없음 발견 |
| X3 WaveCorr (탐색적) | 아니오 | 아니오 | 예 | 아니오 | 예 | 미정 | 아니오 | 없음 발견 |
| X4 Margin Trader (탐색적) | 해당 없음 | 예(경미) | 아니오 | 아니오 | 아니오 | 예 | 아니오 | 없음 발견 |

## 2. 대상별 근거 (파일:줄 @판)

### T1 DeepAries (@634f559 기록, 로컬 판 미확인)
- L1 아니오: `data_provider/data_loader.py` 113–119 `RobustZScoreNorm`을 `df_train`(학습 구간)으로만 적합, `utils/preprocessor.py` 231–244.
- L2 아니오: `data_provider/data_prep.py` 122–130(동시점 비율, 후향 rolling, `pct_change`). `data_loader.py` 83 `fillna(0)`.
- L3 아니오: `data_loader.py` 88–93(학습 < valid_year ≤ 검증 < test_year ≤ 시험), `main.py` 49–52(2020-12-31, 2021-12-31).
- L4 아니오: `exp/exp_DeepAries.py` 265 `early_stopping(vali_loss, …)`, 272–275 그 체크포인트 로드.
- L5 예: `exp_DeepAries.py` 258–264(에폭마다 `vali()`가 시험 손실도 계산해 `TestLoss` 로그), 278–283(`vali`가 test 데이터셋 평가).
- L6 예: `complete_dj30_tickers.csv` 27종목 하드코딩. `data_prep.py` 62–75 상수 가격·영수익 비율(>10%) 종목 제거를 2000-01-01~2025-02-09 전 구간(`main.py` 141–147, 시험 구간 포함)으로 계산. 77–81 전 종목이 있는 날만 남김.
  - 기술: 목록은 XOM·PFE를 포함하고 AMGN·CRM·HON이 없어, 2020-08-31 이전 다우 구성(V·DOW·UTX/RTX 제외)과 맞는다(지수 이력은 외부 지식, 코드 근거 아님). 시험 시작(2021-12-31) 전 구성이다. 이전 노트 `notes/deeparies_static_reading.md` 27행의 "2020년대 구성 종목 목록"이라는 서술과 다르다 — 재확인 필요.
- L7 아니오: `data_loader.py` 179–180(입력은 seq_end_date 미만), 199–205(라벨은 final_date 종가 기준 미래 수익), `preprocessor.py` 102–104 `shift(-lh)`. 학습 보상의 보너스(`exp_DeepAries.py` 216–226)는 고르지 않은 기간의 실현 수익까지 쓰지만 학습 데이터 안의 설계다.

### T2 AlphaMix+ (PRUDEX-Compass @2b62831, `AlphaMix+/PM`)
- L1 해당 없음: `rl_env/portfolio_management.py` 360–388 특성은 비율뿐, 적합 통계 없음.
- L2 예(경미, **새 발견**): `portfolio_management.py` 388 `df_indicator.fillna(method="ffill").fillna(method="bfill")`. 프레임은 종목별로 이어 붙였다(377–387, `sort_values(["tic","date"])`). 종목별 groupby 없이 채우므로, 각 종목(첫 종목 제외)의 첫 ≤29행(2012-01, rolling 워밍업 NaN)이 **앞 종목의 마지막 행(dj30 단계는 2021-12, 시험 구간 끝) 값으로 ffill**된다. 학습 입력의 시작부에만 해당한다. 같은 패턴이 `preprocess()` 292–312에도 있다.
- L3 아니오: `portfolio_management.py` 389–391([2012,2020), [2020,2021), [2021,2022)), `finrl/finrl_meta/preprocessor/preprocessors.py` 20–29(반열린 구간).
- L4: 실행 코드(`rlkit/core/batch_rl_algorithm.py` 61–127)는 모든 에폭을 기록할 뿐 고르지 않는다 → DJ30 보고값의 선택 규칙은 미정(논문·코드에 없음, 이미 논문 서술). **저자 노트북** `data/portfolio_management/AlphaMix+/sz50.ipynb` 셀 1: 에폭은 검증 SR 최대로 고르지만, 하이퍼파라미터 구성(`model_list`)은 그 에폭의 **시험 TR 평균 최대**로 고른다(`loc=test_sr_average.index(max(test_sr_average))`, 주석 "here we use sr as our test score and do the trick"). SZ50 시장용이다 → "예(SZ50 노트북)". **새 발견**(이전 노트에 없음).
- L5 예: `batch_rl_algorithm.py` 82–96(에폭마다 학습 전에 시험 경로 평가, `test_daily_return_{epoch}.csv`·`test_daily_action_{epoch}.npy` 저장), 123–127(`result.csv`의 `test_tr`·`test_sr`).
- L6 예: `portfolio_management.py` 324–355 종목 목록(AMGN·CRM·HON 포함, DOW 포함, XOM·PFE·RTX 없음)을 세 단계 모두에 씀(rolling1 409–439 시험 2020, rolling2 490–520 시험 2019). AMGN·CRM·HON 편입(2020-08-31, 외부 지식)은 rolling1·rolling2 시험 시작 뒤다. dj30 단계(시험 2021)는 시작 전이다. 또 `clean_data`(358–366)가 2012–2022 전 구간 종가 결측 종목을 제거(시험 구간 포함, DOW 제외됨).
- L7 아니오: `portfolio_management.py` 96–118(행동은 t의 상태, 수익은 close_{t+1}/close_t, 다음 상태는 t+1 특성).

### T3 FinRL 포트폴리오 에이전트 (FinRL-Meta `StockPortfolioEnv` @286fef6 기록, 판 미확인)
- L1 해당 없음: 지표·공분산 원값, 적합 통계 없음.
- L2 아니오: 공분산 창 `replication/finrl_t3_run.py` 88–95(튜토리얼 이식, `df.loc[i-252:i]`는 결정일 i 종가까지), stockstats 후향 지표 `meta/data_processors/_base.py` 185–245(NaN 있는 날 제거 238–245).
- L3 아니오: `finrl_t3_run.py` 54–55, 221; `meta/data_processor.py` 140–150.
- L4 아니오: 고정 스텝(`finrl_t3_run.py` PARAMS), 학습 중 시험 평가 없음(`agents/stablebaselines3_models.py` 106·205 TensorboardCallback만).
- L5 아니오.
- L6 예: `meta/config_tickers.py` 5–36 `DOW_30_TICKER`(AMGN·CRM·HON·DOW 포함, XOM·PFE 없음) = 2020-08-31 이후 구성(외부 지식). 시험 2020-07-01~2021-07-01 시작 뒤다. A1(시작일 자료 없는 종목 제외, `finrl_t3_timing.ipynb`)은 시작일만 본다.
- L7 아니오: `meta/env_portfolio_allocation/env_portfolio_yahoofinance.py` 184–201, 236–245.
- L8 예(미발동 경로, **새 발견**): `meta/data_processors/yahoofinance.py` 171–186. 시작일 종가가 NaN이면 "first valid close"로 채운다고 하나, 루프가 break 없이 끝까지 돌아 **마지막 유효 종가**(구간 끝, 시험 구간 포함)로 시작일을 채운다. T3 경로에서는 A1이 그런 종목을 먼저 빼므로 발동하지 않는다(코드 순서상).

### T4 MARS (출판판 L @2561606)
- L1 아니오: `utils.py` 350–392 고정 상수로 나눔.
- L2 아니오: `utils.py` 53–121(ta 후향 지표, 120 `ffill().fillna(0)`), 분할별 따로 계산.
- L3 아니오: `config.py` 12–17, 데이터 날짜 2018-01-02~2022-12-30 / 2023 / 2024(파일 머리·끝 행).
- L4 아니오: `main.py` 725–732(검증 composite 최대 → `best_models`), 617–623(시험 전 재로드).
- L5 아니오: 시험은 학습 뒤 1회(`main.py` 404–460).
- L6 미정: `data/stock_pool_nasdaq_nyse_{training,validation,test}.csv` 세 파일이 같은 50종목, `data/metadata.csv`에 목록만 있고 선정 기준·코드 없음.
- L7 예(이미 기록됨): `main.py` 180 `returns_history.iloc[:t]` + `utils.py` 133–134 `pct_change().dropna()` → 마지막 행이 p_t/p_{t−1}, 거래는 p_{t−1}(161·168행). 이 이력이 행동 혼합 위험(`multi_agent.py` 177–187)과 unsafe 판정(`main.py` 211, `agent.py` 184–185)에 들어간다. `notes/mars_t4_o1_prereg.md` 41행과 일치.

### E Ensemble (Yang et al. 2020, @f02a762)
- L1 해당 없음.
- L2 예(경미): `preprocessing/preprocessors.py` 104 `fillna(method='bfill')`, 프레임은 (tic, datadate) 정렬(44). 각 종목 2009년 초 지표 워밍업 NaN을 같은 종목의 뒤 행으로 채운다(학습 구간만). 난류 지수 131–146은 확장 창 `unique_date[0:i]`(후향).
- L3 아니오: `model/models.py` 155–160(학습·검증), 77(거래 창).
- L4 아니오: `models.py` 199–208 검증 Sharpe로 모델 선택.
- L5 아니오.
- L6 예: `data/dow_30_2009_2020.csv` 30종목, 모두 2009-01-02~2020-08-17. WBA(2018-06 편입)·DD·RTX(2020-04 명칭)·V·XOM·PFE 포함 → 2018-06 이후 구성(외부 지식). 거래 시작 2016-01-04 뒤다.
- L7 아니오: `env/EnvMultipleStock_trade.py` 152–193.
- L8 미정: 난류 임계값을 거래 창 번호로 하드코딩(`models.py` 130: 140, 147–151: i 692–1089 "2018-2019" 100, i ≥ 1090 "2020" 90). 주석은 "in-sample 분석 기반"이라 하지만 근거는 코드에 없다. 별도 노트(`notes/funnel_f7x_ensemble_turb_*`)에서 다룬 주제다.

### R RAT (@d1cbe96, 서버 판)
- L1 아니오: `main.py` 603 창 마지막 종가로 나눔.
- L2 예(정도 미정): `main.py` 179 `panel_fillna(panel, "both")`, 310–323(시간축 bfill 후 ffill). 결측 가격을 뒤 값으로 채운다. 결측 범위는 `Data.db`에 달려 있어 확인하지 않았다.
- L3 아니오: `main.py` 506–524(학습 끝 window+1 잘라냄). 검증 구간은 없다(학습·시험 둘).
- L4 예(이미 기록됨): `main.py` 1341–1351(`train_net`이 시험 구간 `test_batch` 가치가 최대일 때만 저장), 1443–1448(재로드 후 `test_online` 보고). `notes/funnel_f4_rat.md` 13행과 일치.
- L5 예: 같은 위치, 1000스텝마다 시험 가치 출력.
- L6 아니오: `select_coins` 186–210, `get_global_panel` 117–120, `get_volume_forward` 305–309 → 거래량 순위 창이 시험 시작 직전에서 끝난다.
- L7 아니오: `__pack_samples` 474–485(X = M[..., :-1], y = 다음 기간 가격비), 497.

### X1 FRONTIER (탐색적, @e019ce4, 판정 모델 RL_CNN)
- L1 아니오(조건부 경로): `data/data_manager.py` 270–276 처음 30일 평균으로 척도. 평균이 0이면 전 구간 평균(273–274), 0 추정값은 전 구간 최솟값으로 대체(260–261) — 전 구간에 시험 포함. 발동 여부 미확인.
- L2 예(**새 발견**, 번들 파일 정렬은 미확인): `code/REINFORCE/REINFORCE_soft.py` 470 로그수익 창은 현재 행을 빼지만, 얻는 수익은 현재 행 `time_locator(self.returns, curr_time)`(543–545) = close_d/close_{d−1}(`data_manager.py` 47). 같은 상태의 `sigma_est`·`volume_est`는 `.loc[curr_time]`(487–488)이다. sigma_estimate는 sigma_d = |log open_d − log close_d|를 포함한 10일 평균(`data_manager.py` 143, 258, 276), volume_estimate는 volume_d 포함(256, 275). 즉 결정 대상 기간(d)의 장중 변동 크기·거래량이 상태에 1/10 가중으로 들어간다. 번들 `preprocessed_data`의 날짜 정렬이 이 코드와 같은지는 값을 열지 않아 확인하지 않았다.
- L3 예(경미, 이미 기록됨): `REINFORCE_soft.py` 378(시작일은 FROM~UNTIL에서 추출), 393(끝 = 시작 + 29거래일, 상한 없음). 학습 UNTIL = 시험 시작(2018-01-01)이라 시험 첫 ≤29거래일이 학습 에피소드에 들어갈 수 있다. `notes/funnel_f7x_frontier_prereg.md` 97행과 일치.
- L4 아니오: `train_template.ipynb` 셀 4, 200 에피소드 최종 가중치.
- L5 아니오.
- L6 예: `data/DOW_30/historical_data/` 30종목(WBA·DD·RTX·V·XOM·PFE 포함) → 2018-06 이후 구성(외부 지식), 시험 2018-01-01 시작 뒤. `data_manager.py` 147–149·192 결측·이상 수익 필터를 전 구간으로 계산.
- L7 아니오: 보상의 위험항 `Sigma`(338, rolling 10)는 d의 수익을 포함하지만 보상은 사후값이고 결정 입력이 아니다. 거래비용(531–537)은 실현 sigma_d·volume_d를 쓴다(시뮬레이터 비용 모형).
- L8 예(설계, 판정 모델 밖): "strong/weak forecast"는 실현 수익 + 가우스 잡음(`data_manager.py` 226–250, Boyd et al. 2017 방식이라는 주석 228). RL_str_fcast·RL_all_inp의 상태로 쓰인다(`REINFORCE_soft.py` 345–349, 473–480). 판정한 RL_CNN은 쓰지 않는다(`model_config.py` 2–7).
- 참고: 위험 모형(`data_manager.py` 303–339)은 매월 첫날 이전 730일 수익으로 적합(후향). 번들 `risk_model.h5`가 이 코드로 만들어졌는지는 미확인.

### X2 Markowitz Meets Bellman (탐색적, @93c273f)
- L1 해당 없음.
- L2 미정: `draw/algo/knowledgement_drill_ddpg.py` 74는 저장소 루트 `raw_data.csv`를 읽는다. 생성 코드는 확인 못 함. 후보 `profilo management/produce_raw_data.py`는 `raw_data_new.csv`를 쓴다(162행). 후보는 FinRL FeatureEngineer(120–126; FinRL @55764e8 `preprocessors.py` 106 `ffill().bfill()`, 난류 236–237 후향)를 쓴다. Markowitz `weight` 열은 DDPG 스크립트에서 삭제된다(82행).
- L3 아니오: `knowledgement_drill_ddpg.py` 68–71, 92–93(학습 2009–2014, 거래 2016-01~2018-08).
- L4 미정: 코드는 50,000스텝 고정이고 선택이 없다(132–135). 저장소 `final/`에 실행 폴더 191개가 있고, 보고 곡선 폴더를 고른 기준은 기록이 없다.
- L5 아니오.
- L6 예: 5종목 필터 AAPL·CRM·V·UNH·BA(77행). CRM의 다우 편입(2020-08-31, 외부 지식)은 거래 구간(2016–2018) 뒤다. 후보 생성 코드는 FinRL `DOW_30_TICKER`(`config_tickers.py` 6행 주석 "2021/10 구성")를 쓴다. 5종목 선정 기준은 코드에 없다.
- L7 아니오: FinRL @55764e8 `meta/env_stock_trading/env_stocktrading.py` 310–351.

### X3 WaveCorr (탐색적, @20ff832)
- L1 아니오: `src/wavecorr_input.py` 50–53 capped_norm의 min/max가 axis=1(종목) — 시점·특성별 횡단면.
- L2 아니오: 코드에 미래 참조 없음. 데이터 열은 `date,x_close,y_close`, 마지막 행의 y_close가 비어 있다(y는 다음 기간 가격비로 보임, x_close 값의 정의는 값을 열지 않아 미확인).
- L3 예(이미 기록됨): `src/wavecorr_run.py` 41–44 `trainSetLen = 2766`, `wavecorr_agent.py` 251–254 학습 표본이 trainSetLen 미만. 분할은 학습·시험 둘뿐이다. 2766행은 2014-01 초(`data/can/ABX.csv` 날짜열)여서 논문의 검증 구간 2010–2013이 학습에 들어간다.
- L4 아니오: `wavecorr_agent.py` 225–290 마지막 에폭(3000) 사용. 논문의 조기 종료 서술과 다르다(이미 기록됨).
- L5 예(이미 기록됨): `wavecorr_agent.py` 269–276(에폭마다 시험 APV 계산·`track_test` 누적), 354–356(최대·최종 시험 APV 출력), 285–286(`track_test_train` 저장).
- L6 미정: 선정 코드 없음. 번들 `can` 69파일은 모두 2003-01-02 시작, 66개가 2019-10-31·3개가 2019-10-25 끝. `us` 70파일은 모두 2002-07-01~2020-03-31. 시험 끝까지 자료가 있는 종목만 들어 있다. 로더는 `os.listdir` 순서 첫 50개를 쓴다(`wavecorr_input.py` 17, 27).
- L7 아니오: `wavecorr_agent.py` 140–141(y를 입력 창 마지막 행부터 정렬).

### X4 Margin Trader (탐색적, @7b7fa9e; FinRL 설치본 dist-info 0.3.5)
- L1 해당 없음.
- L2 예(경미): FinRL `meta/preprocessor/preprocessors.py` 106 `fillna(method="ffill").fillna(method="bfill")`, (date, tic) 정렬 프레임(종목 사이에 걸침), 데이터 시작부. 난류 232–239 후향 252일.
- L3 아니오: `trading_margin_a2c.py` 57–62, 86–88(학습 2009–2018, "test" 2019–2020-04, 보고 "trade" 2020-05~2023-05).
- L4 아니오: 50,000스텝 고정(133–135). "test(validation)" 평가는 선택에 쓰이지 않는다. 하이퍼파라미터 선택 근거는 코드에 없다.
- L5 아니오.
- L6 예: FinRL `config_tickers.py` `DOW_30_TICKER`(주석 "2021/10 구성") → 보고 구간 시작(2020-05-01) 뒤 구성. `preprocessors.py` 121 `dropna(axis=1)`이 2009–2023 전 구간(보고 구간 포함)으로 종목을 거른다.
- L7 아니오: `env/marginEnv.py` 457–553(행동 후 day+1, 보상 = 자산 차 + 실현 경로 Sharpe 항).

## 3. 미정 항목과 이유
- T2 L4(DJ30): 보고 에폭 선택 규칙이 코드·논문에 없다. SZ50 노트북의 규칙이 DJ30 보고에도 쓰였는지는 알 수 없다.
- T4 L6, X3 L6: 종목 선정 코드·기준이 저장소에 없다(X3은 번들이 생존 종목만 담고 있다는 사실만 확인).
- E L8: 기간별 난류 임계값의 근거가 코드에 없다.
- R L2: bfill이 실제로 채우는 범위는 `Data.db` 결측에 달려 있다(데이터 값 미열람).
- X2 L2: `raw_data.csv` 생성 코드를 특정하지 못했다(저장소 데이터는 받지 않음).
- X2 L4: 191개 실행 폴더 중 보고 곡선을 고른 기준이 기록되지 않았다.
- FRONTIER L1·L2: 코드 경로는 확인했으나, 번들 전처리 파일이 그 경로대로 만들어졌는지는 값을 열지 않아 미확인.

## 4. 이전 기록과 다른 점·새 발견 (보고 전 반박 검토 필요, 이 작업 범위 밖)
1. AlphaMix+ 저자 `sz50.ipynb`: 구성 선택에 시험 TR 사용(L4). 이전 노트에 없다.
2. AlphaMix+ `portfolio_management.py` 388: 종목 간 ffill로 학습 시작부 입력에 다른 종목의 시험 구간 끝 값이 들어간다(L2, 경미).
3. FRONTIER 상태의 `sigma_est`·`volume_est`가 결정 대상일 d의 값을 포함한다(L2, 코드 기준).
4. FinRL-Meta `yahoofinance.py` 171–186: 시작일 결측 채움이 마지막 유효 종가를 쓴다(T3 경로에서는 미발동).
5. DeepAries 종목 목록은 2020-08-31 이전 다우 구성과 맞는다. 이전 노트의 "2020년대 구성"과 다르다. 사후 필터(영수익 비율 등)는 시험 구간 포함 전 구간으로 계산한다.
- 이미 기록된 것과 일치(줄 번호로 재확인): WaveCorr 검증 연도 학습·에폭별 시험 APV, RAT 시험 구간 체크포인트 선택, MARS `iloc[:t]`, FRONTIER 에피소드의 시험 구간 침범, AlphaMix+ 에폭별 시험 기록.

## 5. 한계
- 평가자 1명, 비맹검, 정적 읽기만. 명령줄 인자·설정으로 바뀌는 경로는 기본값만 봤다.
- 구성 종목 편입·편출 날짜는 외부 지식이며 이 작업에서 출처를 다시 확인하지 않았다(L6 기술의 근거 일부).
- "경미"는 범위 기술일 뿐이다. 성과 영향은 측정하지 않았다.
- 대상 10개는 편의 표본이다. 빈도를 일반화하지 않는다.
