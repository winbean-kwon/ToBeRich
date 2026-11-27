# 공식 코드 저장소 지속성 점검 — 결과 (기술 통계)

사전 등록 `notes/repo_durability_prereg.md`(2cff9ad). 조회 2026-11-27(UTC), 인증 없는 GitHub API 57회 + 웹 HEAD/atom. 원자료 `replication/repo_durability.json`. 판정 없음.

## 이탈·보충 (사전 등록 대비)
- HARLF Colab URL은 HEAD 요청에 405를 돌려줘 GET(-L)으로 상태를 쟀다(200).
- Ensemble은 실행 파일이 바뀌었는지(수정/삭제)를 가르려고 compare를 1회 더 불렀다(파일별 status만, 내용 안 봄).
- T3 경로 필터(`env_portfolio_yahoofinance`, `meta/data_processors/`)는 사전 등록대로 적용했다. 바뀐 코드 경로 `meta/data_processor.py`는 이 필터 밖이라 "돌린 파일 변경"에 세지 않았다(표에 경로를 그대로 적음).

## 개수
| 항목 | 값 |
|---|---|
| 모집단 GitHub 저장소 | 32 (+ 비 GitHub 2: HARLF Colab, SCR Zenodo) |
| 지금 열림(API 200) | 29/32 |
| 열리지 않음(404) | 3: qq303067814/…portfolio-management-(liang2018), DavWinkel/SimplexDecompositionECAI(P23-04), sophialien/FinTech-DPM(SUP-CLRS) — 셋 다 F1에서 이미 link_dead로 기록된 것 |
| archived | 0/29 |
| 기록된 URL이 다른 곳으로 리디렉션 | 1/32: Ensemble(AI4Finance-LLC/…ICAIF-2020 → AI4Finance-Foundation/FinRL-Trading, 301) |
| 비 GitHub 열림 | 2/2 (Colab GET 200; Zenodo DOI 302 → zenodo.org/records/20410374 200) |
| 우리 커밋 기록 있는 저장소 | 21 (compare 24회) |
| 우리 커밋 이후 기본 브랜치 변경 있음(ahead_by>0, 저장소 하나라도) | 7/21: FinRL, FinRL-Meta, RAT, Ensemble, frontier-rl, BellmanMarkwitz, MARS |
| 그중 사전 등록 기준 "돌린 파일" 변경 | 5/21: FinRL, RAT, Ensemble, frontier-rl, MARS |
| 우리 커밋 = 기본 브랜치 HEAD(identical) | 14/21 |

## 우리 커밋이 있는 저장소
| 저장소 (논문) | 우리 커밋(날짜) | 기본 브랜치 | 최신 커밋 | ahead_by | 바뀐 경로 / 코드 경로 | 돌린 파일 변경 |
|---|---|---|---|---|---|---|
| dmis-lab/DeepAries (T1) | 634f559 (2026-04-30) | main | 2026-04-30 | 0 | 0/0 | 없음 |
| TradeMaster-NTU/PRUDEX-Compass (T2) | 2b62831 (2023-06-21) | main | 2023-06-21 | 0 | 0/0 | 없음 |
| AI4Finance-Foundation/FinRL-Meta (T3) | 286fef6 (2026-09-28) | master | 2026-11-22 | 2 | 2/2: `meta/data_processor.py`, `unit_tests/test_data_processor_run.py` | 필터 기준 없음 |
| jiayiderekchen/MARS (T4, L) | 2561606 (2025-07-30) | main | 2026-07-10 | 12 | 43/6: `agent.py`, `config.py`, `helper/__init__.py`, `helper/bmid_selector.py`, `main.py`, `multi_agent.py` (+ 체크포인트·README) | 있음 |
| jiayiderekchen/MARS (T4, N) | 6ca2051 (2026-07-10) | main | 2026-07-10 | 0 | 0/0 | 없음 |
| Ivsxk/RAT (F7) | d1cbe96 (2020-07-02) | master | 2020-11-25 | 27 | 2/1: `main.py`, README | 있음(`main.py`) |
| Ivsxk/RAT (감사) | 9a65269 (2020-11-25) | master | 2020-11-25 | 0 | 0/0 | 없음 |
| AI4Finance-LLC/…Ensemble-ICAIF-2020 → FinRL-Trading (F7) | f02a762 (2020-09-02) | master | 2026-09-18 | 264 | 119/75 | 있음: 실행 파일 7개(`run_DRL.py`, `model/models.py`, `env/EnvMultipleStock_{train,validation,trade}.py`, `preprocessing/preprocessors.py`, `config/config.py`) 모두 기본 브랜치에서 **removed** |
| saeedmarzban/waveCorr | 20ff832 | main | 2022-08-15 | 0 | 0/0 | 없음 |
| kshre/PPN | 0210924 | master | 2020-06-30 | 0 | 0/0 | 없음 |
| JingyiGu/Margin-Trader | 7b7fa9e | main | 2025-02-25 | 0 | 0/0 | 없음 |
| YinchuanLl/…portfolio-allocation | 326640a | master | 2019-06-11 | 0 | 0/0 | 없음 |
| AI4Finance-Foundation/…DDPG-NIPS-2018 | e59b994 | master | 2024-03-15 | 0 | 0/0 | 없음 |
| ruankie/frontier-rl | e019ce4 (2022-04-09) | main | 2022-09-01 | 124 | 75/35 (`code/REINFORCE/*.ipynb`, `train_parallel.py` 등) | 있음 |
| BMEgang/BellmanMarkwitzProject | 93c273f (2024-02-17) | main | 2024-07-22 | 2 | 1/0 (README) | 없음 |
| ChloeWenyiZhang/SmartFolio | 013e089 | master | 2025-02-11 | 0 | 0/0 | 없음 |
| DVampire/EarnMore | 810ff59 | main | 2024-02-27 | 0 | 0/0 | 없음 |
| SteamerLee/MASA | d97ef0e | main | 2024-10-19 | 0 | 0/0 | 없음 |
| CMACH508/DeepTrader | 4b00b2a | main | 2021-11-10 | 0 | 0/0 | 없음 |
| TradeMaster-NTU/TradeMaster | 1747cc1 | 1.0.0 | 2025-06-04 | 0 | 0/0 | 없음 |
| ZhengyaoJiang/PGPortfolio | 48cc5a4 | master | 2021-07-30 | 0 | 0/0 | 없음 |
| jackieli19/PGPortfolio (Stock 브랜치) | a7c1333 (2019-12-16) | master | 2019-12-10 | Stock 0; master 대비 behind 7 | 0/0 | 없음 |
| AI4Finance-Foundation/FinRL | 7e98df4 (2026-10-25) | master | 2026-11-27 | 9 | 14/14 (`finrl/agents/stablebaselines3/models.py`, `finrl/meta/env_stock_trading/*` 등; `env_portfolio_optimization` 경로는 없음) | 저장소 전체 코드 기준 있음 |

## 우리 커밋 기록이 없는 저장소 (열림 여부·최신 커밋만)
| 저장소 (논문) | 상태 | 최신 커밋 |
|---|---|---|
| qq303067814/…portfolio-management- (liang2018) | 404 | — |
| DavWinkel/SimplexDecompositionECAI (P23-04) | 404 | — |
| sophialien/FinTech-DPM (SUP-CLRS) | 404 | — |
| jkcost/Deepclair (P24-10) | 200 | 2024-04-22 |
| ahmad-asadi/sopmoe (Y26-01; 논문에 링크 없음) | 200 | 2026-08-07 |
| ChenJiahaoJNU/SBCA (Y26-03; 논문에 링크 없음) | 200 | 2026-05-02 |
| edrtfu531/rlscr1 (SQ-SCR) | 200 | 2026-05-27 |
| Dumail/ReCAP (SUP-ReCAP) | 200 | 2026-05-26 |
| jiahaoli57/LSRE-CAAN (SUP-LSRE) | 200 | 2023-07-08 |
| cspun/ADRLwIntReward (SUP-ADRL) | 200 | 2024-11-27 |
| XiaHaochong98/Bayesian-Robust-… (SUP-BRT) | 200 | 2026-01-03 |

## 사실 메모 (해석 없음)
- RAT d1cbe96 → HEAD의 `main.py` 변경은 `notes/funnel_f4_rat.md`가 이미 기록한 것(주석 1줄)과 같은 범위의 커밋이다(내용은 이번에 다시 보지 않음). 감사에 쓴 9a65269는 HEAD와 같다.
- MARS 2561606 이후 변경은 이미 알려진 저자 수정본(6ca2051, 2026-07-10)이며, 6ca2051은 지금 HEAD와 같다.
- Ensemble: 우리가 돌린 f02a762의 파일 7개는 기본 브랜치에서 지워졌다. 저장소 이름이 FinRL-Trading으로 바뀌었고 옛 URL은 301로 넘어간다. 커밋 자체는 compare로 조회됐다(커밋은 남아 있음).
- frontier-rl e019ce4는 사전 등록 당시 "가장 이른 코드 판"으로 고른 것이라 이후 변경이 있는 것은 선택 규칙상 예상된 일이다.
