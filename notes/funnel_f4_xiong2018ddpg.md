# F4·F5 Practical DRL 기록 (AI4Finance-Foundation/…NIPS-2018 @14598b3, 원 코드 2018-10-13 a395165)

프로토콜 `notes/funnel_protocol.md`. 대상: Xiong, Liu, Zhong, Yang, Walid, "Practical Deep Reinforcement Learning Approach for Stock Trading", NeurIPS 2018 Workshop on AI in Finance(arXiv 1811.07522). 순서상 Adaptive DDPG 다음이다(3.3, `notes/lit/f1/static_layer.csv` 순서 7).

## 1. 정적 확인 (2026-11-09, 실행 전) — 미완, li2019adaptive와 같은 지점에서 막혀 멈춤

- **코드 계보:** 원 저장소(hust512/DQN_Stock_Trading류)는 2018-09-18 생성, 핵심 환경 파일(당시 이름 `gym/envs/zxstock/zxstock_env.py`)은 `8882a6e`(2018-10-10)에 추가, `a395165`(2018-10-13, "add two package")가 2018년의 마지막 커밋이다(arXiv 제출월 1811=2018-11보다 앞섬, 초판 직전으로 쓸 수 있는 가장 늦은 2018년 커밋). 이후 2019년 활동이 없다가 **2020-06-06**(`14598b3`·`e92f15b`)에 AI4Finance가 환경을 `zxstock`→`rlstock`로 이름을 바꾸고, 저장소 루트에 `run.py`(독자 실행 스크립트, 2018년에는 존재하지 않았다 — `git log --follow -- run.py` 확인)와 상세 README·정확한 실행 명령을 추가했다. HEAD(`e59b994`, 2024-03-15)는 LICENSE 파일만 바꾼 것이다.
- **2018 버전(`a395165`, `zxstock_env.py`)과 2020 버전(HEAD, `rlstock_env.py`)의 코드 로직은 동일하다**(경로·이름만 다름, `git diff -b` 확인). money=10000, 종목 28개(거래일수 4711 종목 + NKE·KO), 행동 공간 `Box(-5,5,shape=(28,))`, 에피소드 종료 `day>=1761`. (참고: 순서상 다음 대상도 아닌 li2019adaptive의 `portfolio_env.py`가 이 환경을 money=100000·행동폭 ±20·종료일 3268로 확장한 후속판임을 1절에서 이미 확인했다 — 같은 연구팀의 계보.)
- **데이터:** 번들(`Data/dow_jones_30_daily_price.csv`, `^DJI.csv`). `Data/`에는 입력 데이터와 함께 **성과로 보이는 파일(`ddpg.csv`, `history.csv`, `weights_table_*.xlsx`, `mean_variance_return.xlsx`, `return_final_quarterly.xlsx`, `calculate_return.ipynb`)이 섞여 있어 열지 않는다**(2.1 대응 필요 — 어떤 파일이 입력이고 어떤 게 결과인지 이름으로만 구분, 결과로 보이는 파일은 코드가 아니라 사람이 미리 저장해둔 것으로 추정).
- **하드코딩 경로:** `zxstock_env.py`/`rlstock_env.py`가 저자 개인 머신 절대경로(`/Users/xiongzhuoran/anaconda3/...`, `/Users/hongyangyang/...`)로 데이터를 읽는다. README가 "import data path를 자기 경로로 바꿔라"고 명시 지시하므로 허용 수정(설치 절차)이다.
- **실행 절차(README, 2020 버전 기준):** `python -m baselines.run --alg=ddpg --env=RLStock-v0 --network=mlp --num_timesteps=1e4`(학습), `--num_timesteps=2e4 --play`(거래/시험). 저장소 루트의 `run.py`가 공식 `baselines/run.py`를 대체한다(README Step 8).
- **⚠ 같은 지점에서 막힘(li2019adaptive와 동일한 구조적 문제):** 이 저장소의 `run.py`(2020년 추가분)는 공식 baselines의 `run.py`를 거의 그대로 가져온 것이고, `get_learn_function_defaults(alg, env_type)`은 `baselines/<alg>/defaults.py`에 `env_type` 이름의 함수가 있을 때만 그 값을 쓴다(`ImportError`/`AttributeError`면 `{}`). 공식 baselines에는 `baselines/ddpg/defaults.py`가 없다(li2019adaptive 조사에서 이미 확인). 따라서 DDPG의 하드코딩 기본값(`nb_epoch_cycles=50`, `nb_rollout_steps=500`)이 그대로 적용되고, **README가 명시한 `--num_timesteps=1e4`(10,000)는 `nb_epochs = 10000 // (50×500=25000) = 0`이 되어 학습이 0 에폭 실행된다.** 즉 이 연구팀(Xiong·Liu·Zhong·Yang·Walid, 2018~2020 논문 계열)의 두 논문(xiong2018ddpg, li2019adaptive)이 공개한 README 명령이 **공식 baselines DDPG 기준으로는 둘 다 문자 그대로 돌리면 학습이 안 되는** 같은 결함을 공유한다(우연이 아니라 계보가 같아서로 보인다). 저자들이 실제로 쓴 값은 남아있지 않다.

**다음 결정이 필요하다(사용자, li2019adaptive와 같은 질문):**
1. 측정 단위를 어떻게 정할지(1에폭=25,000스텝 단위로 시간만 보고 vs 역산 방식 vs "미시험(정적 의심)" 분류) — li2019adaptive에서 내릴 결정을 그대로 따르는 것이 일관적일 것이다(같은 결함, 같은 코드 계보).
2. `Data/` 안의 성과로 보이는 파일들을 무시하고 입력 데이터(`dow_jones_30_daily_price.csv`, `^DJI.csv`)만 쓰는 게 맞는지 확인(가능성 높음, 재확인 안 함).

이 판단이 날 때까지 F4/F5 사전 등록(2절)·로컬 스크립트는 작성하지 않는다. li2019adaptive와 같은 사전 등록 원칙(핵심 실험 변수를 결과를 보지 않은 상태에서 임의로 정해 커밋하면 안 됨)을 적용한다.

**결정(2026-11-10, 사용자가 "추천대로" 위임, 측정 전·성과 미열람):** F7 두 자리가 RAT·Ensemble로 찼으므로(프로토콜 3.3-3 "2편이 차면 이후 논문은 F4까지만") 이 대상은 **F4까지만** 진행한다. F5(시간 상한 판정)는 적용하지 않아 학습 길이를 정할 필요가 없다. F4 실행 단위는 **1에폭 = `nb_epoch_cycles`(50) × `nb_rollout_steps`(500) = 25,000스텝**(`--num_timesteps=25000`)으로 고정하고, "학습 1에폭과 그 뒤 평가 경로가 오류 없이 끝나면 통과"로 판정한다. 저장소 기본값(1e4)이 0에폭이 되는 점은 F2 비고("논문·코드에 학습 길이가 사실상 지정되지 않음")로 기록한다. 이 대상의 F4 사전 등록·로컬 스크립트는 F4 예산(벽시계 40시간) 안에서 순서대로 쓴다.

## 2. F4 사전 등록 (2026-11-11, 실행 전, 성과 미열람)

순서: S56에서 li2019adaptive 다음(F7 자리 없음 → F4까지만). 장치: 서버 노트북 WSL2 CPU, RAT F7이 끝난 뒤 li2019 다음에 실행.

### 2.1 코드·환경
- 저장소 HEAD `e59b994`(2024-03-15)를 쓴다. 이유: 2018 커밋 `a395165`에는 실행 절차가 없고(README는 DQN 노트북 안내뿐), 실행 절차(README Step 7~9)와 `run.py`는 이후 버전에만 있다. 환경 로직은 2018판과 같다(1절, `git diff -b` 확인). `14598b3`(2020-06)과 HEAD의 차이는 README·이름(zxstock→rlstock)·gym 등록이다. 실행 시 `run.py`·`rlstock_env.py`·`rlstock_testenv.py`의 sha256을 확인한다(b780bb89…, 81f7436a…, 3de1b4ae…).
- OpenAI baselines는 2018 커밋이 서브모듈로 고정한 `7bfbcf1`(2018-10-04)을 받아 설치하고, README Step 8대로 `baselines/run.py`를 저장소 `run.py`로 바꾼다.
- gym은 `pip install gym==0.15.7`(저장소 사본과 같은 버전, 사본에는 setup.py가 없음)로 설치하고, README Step 7·8대로 `rlstock` 폴더를 설치된 `gym/envs`에 복사하고 `RLStock-v0`·`RLTestStock-v0`를 등록한다.
- Python 3.7, tensorflow 1.14.0(README 명시), numpy 1.16.4, pandas 1.0.3, scipy 1.4.1, matplotlib 3.2.1. mpi4py는 설치하지 않는다.

### 2.2 허용 수정
1. **경로(README Step 8 지시):** `rlstock_env.py`·`rlstock_testenv.py`의 `/Users/hongyangyang/.../gym/envs/rlstock/` 접두어를 설치된 `gym/envs/rlstock/` 경로로 바꾼다.
2. **실행 인자:** `python -m baselines.run --alg=ddpg --env=RLStock-v0 --network=mlp --num_timesteps=25000 --seed=0 --play`. README 예시 1e4·2e4는 0에폭이 되므로 2026-11-10 결정(1에폭 = 25,000스텝)을 따른다.
3. **성과 비노출:** 표준출력·오류는 파일로만 보내고 열지 않는다. 그림(`result_training.png`, `result_test.png`)도 열지 않는다.

### 2.3 판정
- **F4 통과:** rc = 0이고 작업 폴더에 `result_test.png`가 생김(시험 env가 terminal(day ≥ 685)에서만 저장 = 1에폭 학습 후 시험 경로 끝까지 실행). 표기: "1에폭(25,000스텝) 기준, 논문 학습 길이 미지정".
- 실패·상한·재시도·예산 규칙은 li2019adaptive 2.3과 같다(상한 3시간, 최대 3회, stderr 마지막 40줄만 열람).

스크립트: `replication/funnel_f4_xiong2018_local.py`(이 절과 같은 커밋).
