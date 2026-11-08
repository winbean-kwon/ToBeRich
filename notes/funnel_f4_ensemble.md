# F4·F5 Ensemble 기록 (AI4Finance-LLC/…ICAIF-2020 @f02a762)

프로토콜 `notes/funnel_protocol.md`. 대상: Yang, Liu, Zhong, Walid, "Deep Reinforcement Learning for Automated Stock Trading: An Ensemble Strategy", ACM ICAIF '20(2020-10-15~16, Manhattan, NY). 순서상 RAT 다음이다(3.3). RAT의 F7(Colab 독립 확인 대기, `notes/funnel_f4_rat.md`)과 무관하게 F4·F5를 진행한다(3.3: 순서는 성과·다른 대상의 F7 상태와 무관, 고정).

## 1. 정적 확인 (2026-11-08, 실행 전)
- **코드 버전:** 저장소 생성 2020-06-20(`5eda2e0` Initial commit). 이 논문은 arXiv 사전공개가 없다(WebSearch로 확인: arXiv `2511.12120`은 2025-11-15 제출된 재업로드이고 2020년 당시 preprint가 아니다, ACM ICAIF '20 proceedings만 초판). 콘퍼런스(2020-10-15~16) 직전 `run_DRL.py` 커밋은 `f02a762`(2020-09-01, "Update run_DRL.py", `c45c453` "Add Ensemble Strategy" 바로 다음)다. **`f02a762`를 쓴다**(2.1 규칙: 초판 직전 커밋). **출판 후 수정:** `7fbee07`(2020-10-19, 콘퍼런스 직후)에서 DDPG에 `OrnsteinUhlenbeckActionNoise` 추가, PPO2에 `ent_coef=0.005`·`nminibatches=8` 추가 — 동작이 달라지는 실질적 하이퍼파라미터 변경이라 쓰지 않는다. 이후 `489168b`(2020-11-06, libiomp 이슈 수정), `20b5898`(2022-07-16)에서 저장소가 "FinRL-Live-Trading" 구조로 전면 리팩터링돼 `run_DRL.py`가 사라진다(현재 HEAD는 완전히 다른 레이아웃).
- **파일 해시(f02a762):** `run_DRL.py` sha256 `a2f8261c…`, `model/models.py` `026987d8…`, `env/EnvMultipleStock_train.py` `540146a5…`, `env/EnvMultipleStock_validation.py` `0ec43c80…`, `env/EnvMultipleStock_trade.py` `5f73d052…`, `preprocessing/preprocessors.py` `46a27892…`, `config/config.py` `b720d773…`.
- **README:** PPO·A2C·DDPG(모두 stable_baselines, TensorFlow 1.15) 3개를 따로 학습해 검증 구간 Sharpe가 가장 높은 모델을 다음 거래 구간에 쓰는 앙상블. "성장 창(growing window)으로 3개월마다 재학습, 12개월 검증 창" (README). Dow30 종목, 데이터 출처는 Compustat/WRDS. 저장소에 데이터가 번들돼 있어 외부 다운로드가 불필요하다(PPN·RAT와 달리 데이터 접근 위험이 거의 없다).
- **데이터:** 저장소 내 `data/dow_30_2009_2020.csv`(4.9MB), `data/dow30_turbulence_index.csv`(76KB, 코드에서는 실제로 쓰이지 않고 `preprocessing/preprocessors.py`가 난류 지수를 직접 재계산한다), `data/^DJI.csv`, `data/ETF_SPY_2009_2020.csv`(비교 벤치마크용, 미사용 추정).
- **분할(코드, 실측):** `run_DRL.py`가 `unique_trade_date`를 `20151001 < datadate <= 20200707`로 자른다(하드코딩). 번들 데이터 기준 이 구간의 고유 거래일은 **1,198일**(첫날 2015-10-02, 마지막날 2020-07-07, 직접 집계). `rebalance_window = validation_window = 63`(거래일 ≈ 3개월). 루프는 `range(126, 1198, 63)`로 **18회** 돈다(직접 집계). README는 검증 창을 "12개월"이라 적었지만 코드는 63거래일(≈3개월)이다(**F2 비고: 논문 설명–코드 불일치**, PPN·RAT와 같은 유형).
- **논문·코드 절차(사이클당, `model/models.py`):** A2C `timesteps=20000`, PPO2(`PPO2('MlpPolicy', ...)`) `timesteps=50000`, DDPG `timesteps=10000`(모두 stable_baselines 기본 `MlpPolicy`, 노이즈·엔트로피 보정 없음 — 위 출판 후 수정에서 추가됨). 학습 데이터는 `20090000`부터 그 사이클 시작까지(성장 창, 사이클마다 커진다). 검증(63거래일) 후 세 모델의 Sharpe((4**0.5) × 일일수익률 평균/표준편차)를 비교해 최고를 골라 다음 63거래일 거래. 난류 지수 임계값은 코드에 구간별로 하드코딩(기본 140, 인덱스 692~1089는 100, 1090 이상은 90 — "과거 데이터 분석 기반"이라고만 설명, 재현 불가능한 설정).
- **장치:** `env/*.py`·`model/models.py`·`run_DRL.py`·`preprocessing/*.py` 전체에 CUDA·GPU 참조가 전혀 없다(grep 확인). TensorFlow 1.15 CPU, 관측 181차원·행동 30차원의 소형 MLP 정책(stable_baselines `MlpPolicy`)이라 GPU 가속 대상이 아니다. **PPN·RAT의 "GPU 있으면 GPU, 장치 우선순위" 규칙 자체가 이 대상에는 적용되지 않는다** — CPU만 쓴다.
- **성과 노출 위험:** `model/models.py`의 `train_A2C`/`train_PPO`/`train_DDPG`·`run_ensemble_strategy`가 Sharpe 비율과 거래 로그를 표준출력에 직접 `print`한다(예: `"A2C Sharpe Ratio: "`). `results/`에 계정 가치 CSV(`account_value_*.csv`, `last_state_*.csv`)를 쓴다. F4·F5는 성과를 보지 않는다(2.1).
- **미사용 파일:** `env/StockTradingRLEnv.py`는 `run_DRL.py`·`model/models.py`가 import하지 않는다(README 버전 이력의 "0.0.1 간단 버전"으로 추정, 무시한다).
- **설치:** Python ≥3.6(README), `requirements.txt` 고정: `numpy==1.16.4`, `pandas==1.0.3`, `stockstats`, `scikit-learn==0.21.0`, `gym==0.15.3`, `stable-baselines[mpi]`, `tensorflow==1.15.2`, `joblib==0.15.1`, `matplotlib==3.2.1`. `[mpi]` extra는 `mpi4py`→OpenMPI(OS 패키지) 설치가 필요할 수 있다(관문에서 import 확인, 안 되면 허용 수정 2.3-4).

## 2. 사전 등록 (실행 전 고정, 이 커밋)

### 2.1 성과 비노출
- 표준출력(Sharpe 비율·거래 로그), `results/*.csv`(계정 가치·마지막 상태), `trained_models/*`(모델 파일)은 열지 않는다. 화면·보고에는 설치 결과, 시간 이벤트, traceback만 쓴다.
- 래퍼는 자식 프로세스의 표준출력·표준오류를 파일로만 보내고, PPN·RAT와 같은 고정 필터(Error/Traceback/Killed/CUDA/OOM/Segmentation/Aborted 포함, portfolio·sharpe·return·value·benefit 등 성과 문구가 든 줄은 제외)를 거친 마지막 15줄만 화면에 낸다.

### 2.2 환경
- Python 3.7(micromamba conda-forge). `requirements.txt`의 버전을 그대로 고정 설치한다. 관문 칸에서 `python 3.7…`, 각 패키지 버전, `import stable_baselines, tensorflow, gym, stockstats` 성공을 확인하고 다르면 멈춘다.
- 장치: **CPU만 쓴다**(1절, GPU 코드 경로가 없다). 측정 장치는 "서버 노트북(GTX1650, CPU)" 또는 "Colab(CPU)"로 적는다. GPU 유무가 성능에 영향을 주지 않으므로 PPN·RAT에서 문제된 장치 우선순위·모니터니시티 쟁점이 이 대상에는 없다. **동시 실행 금지**(PPN 개정 기록 6·RAT 개정 기록 3과 같음, 한 번에 한 장치에서만 S를 돈다)는 그대로 적용한다. 서버 노트북에서 먼저 측정하고, Colab 측정은 참고로 병기한다(교차 확인 목적, 채택에 우선순위를 두지 않는다 — 어느 쪽이든 같은 CPU 성격의 측정이기 때문이다).
- 시간대: 코드가 쓰는 날짜(`datadate`)는 정수 `YYYYMMDD`이고 시각 연산이 없다. 별도 `TZ` 설정이 필요 없다.

### 2.3 허용 수정(노트북 없이 로컬 스크립트로 직접 작성, v3 2.3 준용)
1. **실행 래퍍:** `run_DRL.py`·`model/models.py`·`env/*.py`·`preprocessing/*.py`·`config/config.py`를 수정하지 않는다. 래퍼가 이 파일들을 `exec`로 그대로 실행하되(RAT에서 확인한 pickle 버그를 피하려고 `sys.modules['__main__'].__dict__`를 globals로 쓴다), `model.models.train_A2C`/`train_PPO`/`train_DDPG`와 `run_ensemble_strategy`의 `for i in range(...)` 루프 경계를 감싸 시각을 기록한다(함수를 patch하는 방식, PPN·RAT 래퍼와 같은 수준). main 모듈들의 로직·하이퍼파라미터는 바꾸지 않는다.
2. **실행 길이:** `run_ensemble_strategy`의 `for i in range(rebalance_window+validation_window, len(unique_trade_date), rebalance_window)` 루프를 **첫 반복(i=126) 1회만** 돌고 멈춘다(두 번째 반복 시작 전에 `break`). 사이클당 스텝 수(A2C 20000·PPO 50000·DDPG 10000)는 저장소 그대로 줄이지 않는다 — PPN·RAT와 달리 사이클 자체가 이미 수 분~수십 분 단위로 작아서 줄일 필요가 없다(실측 전 추정). 전체 18사이클을 돌리지 않는 것만 허용 수정이다.
3. **결과 기록:** 프로세스 시작, 데이터 전처리(`preprocess_data`+`add_turbulence`) 시작·끝, 사이클 시작, A2C/PPO/DDPG 각 학습 시작·끝, 각 검증(`DRL_validation`) 시작·끝, 거래 예측(`DRL_prediction`) 시작·끝, 사이클 끝 시각을 `times.jsonl`에 쓴다. 값(Sharpe·계정 가치 등 성과)은 기록하지 않는다.
4. `stable-baselines[mpi]` 설치가 OpenMPI 부재 등으로 실패하면 `stable-baselines`(mpi 없이)로 대체 설치한다. DDPG가 MPI 없이 동작하지 않으면(관문에서 확인) 그 사실을 기록하고 "실행 불가"로 판정한다(대체 알고리즘을 임의로 쓰지 않는다).

알고리즘·보상·관측·나머지 하이퍼파라미터·난류 지수 임계값은 바꾸지 않는다. 시드는 코드가 정하지 않으므로(각 stable_baselines 모델 생성 시 시드 미지정) 그대로 둔다.

### 2.4 실행
- **S:** 설치 → 관문(버전·import 확인) → 데이터 전처리 → 첫 사이클(A2C 20000 + PPO 50000 + DDPG 10000 스텝, 검증 3회, 거래 예측 1회) 전체 경로.
- 벽시계 상한 3시간(PPN·RAT와 같은 기준). 넘으면 끊는다. 상한으로 끊긴 것은 실행 실패로 세지 않는다.
- 측정은 1회다. 설치·실행 오류나 연결 끊김으로 값이 안 나올 때만 다시 돈다.
- 끊김 처리(PPN·RAT 2.4와 같음): 시간 표시를 60초마다 결과 폴더에 복사한다. 다시 실행하면 끝난 실행(F4 통과 또는 상한 중단)은 건너뛴다. 끊긴 실행은 처음부터 다시 돌고, 이전 기록은 `S_times.attemptN.jsonl`로 보존한다.
- 측정값(초): `startup`(프로세스 시작→전처리 끝), `a2c`·`ppo`·`ddpg`(각 학습 시작→끝), `val_a2c`·`val_ppo`·`val_ddpg`(각 검증 시작→끝), `trade`(거래 예측 시작→끝), `cycle_end`(사이클 전체).

### 2.5 판정
**F4:** S가 `rc=0`이고 사이클 끝 표시가 있으면 통과("첫 사이클 기준, 전체 18사이클 중 1회만 실행"으로 표기). 상한으로 끊기면 "상한 내 미완". 실패하면 허용 수정 범위에서 고친다(대상당 벽시계 8시간 안). 끝내 안 되면 "실행 불가".

**F5(판정값 A):**
A = (startup + 18 × (a2c + ppo + ddpg + val_a2c + val_ppo + val_ddpg + trade)) / 3600 시간.
- 18 = 1절에서 번들 데이터로 직접 집계한 전체 사이클 수(사후에 바꾸지 않는다).
- A > 10: F5 "한도 초과"(장치 표기). 다음은 순서(3.3)상 큐의 다음 대상.
- A ≤ 10: F5 통과. F7 설정은 사전 등록에서 정해야 하므로 **멈추고 사용자에게 보고**한다.
- **하한 규칙:** 상한으로 끊겨 A2C·PPO·DDPG 중 일부만 끝났으면, 끝난 것은 그대로 쓰고 못 끝난 것은 "그 알고리즘의 목표 스텝 대비 끝난 스텝 비율의 역수"로 선형 추정해 하한을 계산한다. 학습이 하나도 안 끝났으면(A2C조차 끝나지 않음) A_lb = 18 × 3 = 54시간("한도 초과(하한 기준)").
- **일반 규칙(PPN·RAT와 같음):** 저장소가 정한 항목(스텝 수 등)은 저장소 값을 그대로 쓴다(이 대상은 논문이 사이클당 스텝 수를 명시하지 않아 코드 값이 유일한 기준이다).

**탐색적 기록:** CPU 이용률, 메모리, 사이클별 전처리·학습 시간의 증가 추세(성장 창 효과 확인용, 판정에는 안 씀).

### 2.6 한계(실행 전)
- **18배 환산은 첫 사이클(가장 작은 학습 데이터) 기준이라 하한에 가깝다.** 성장 창이라 사이클이 뒤로 갈수록 학습 데이터(`data_split` 범위)가 커지고, pandas 인덱싱·전처리 비용이 늘 수 있다. 스텝 수는 고정이라 학습 자체의 1-스텝 비용은 데이터 크기에 거의 비례하지 않을 것으로 추정하지만(관측은 날짜별 고정 차원 181), 전처리·데이터 분할 비용은 커질 수 있다. 이 비선형성을 측정하지 않았다.
- 검증 창이 README "12개월"과 코드 "63거래일(≈3개월)"로 다르다(1절 F2 비고). F5는 코드 값(63거래일)을 쓴다.
- 난류 지수 임계값(140/100/90)이 하드코딩돼 있고 저자가 재현 가능한 산출 방법을 공개하지 않았다. 시간 측정에는 영향이 없다.
- `stable-baselines`(TF1, 2019-2020년대 라이브러리)의 설치 호환성, 특히 `[mpi]` 확장이 현재 패키지 생태계(pip·conda-forge 최신 인덱스)에서 깨졌을 수 있다(2.3-4로 대응).
- 시드가 코드에 없어 알고리즘별 학습 속도가 실행마다 달라질 수 있다(시간 측정에는 거의 영향 없음, GPU가 아니라 CPU 연산이라 변동성은 PPN·RAT보다 작을 것으로 추정).
- 모델 저장(`model.save`)·검증·거래 예측의 디스크 I/O 시간이 사이클 수만큼 반복되는데, 첫 사이클만 재므로 디스크 상태(캐시 등)에 따라 달라질 수 있다.

**실행 전 실패 기록 1(설치, 시간 측정 전, 2026-11-09, 성과 미확인):** 서버 노트북 시도 1에서 설치는 끝났지만(`stable-baselines[mpi]` 실패 → mpi 없이 대체 설치, 해시 확인 통과) 관문에서 `import tensorflow`가 `TypeError: Descriptors cannot not be created directly`로 실패했다. 원인은 pip가 `tensorflow==1.15.2`와 함께 최신 `protobuf`(4.x)를 설치해, TF1이 내부에 번들한 구버전 생성 코드(`_pb2.py`)와 호환되지 않는 것이다(2026년 pip 생태계에서 TF1 설치 시 흔한 문제, 2.6에 이미 "현재 패키지 생태계에서 깨졌을 수 있다"로 예견한 범위). 설치 명령에 `pip install "protobuf<3.20"`을 추가해 고쳤다(허용 수정이 아니라 설치 단계의 버전 고정 보완, main.py·판정 규칙과 무관). 측정값은 전혀 안 나왔으므로 재시도 조건(2.4)에 해당한다.

**실행 전 실패 기록 2(설치, 시간 측정 전, 2026-11-09, 성과 미확인):** 시도 2에서 `stable-baselines`(mpi 없이)에서 `DDPG`를 import할 수 없었다(`ImportError: cannot import name 'DDPG'`) — 2.3-4에서 예견한 대로 plain 설치는 DDPG를 지원하지 않았다. 대체 알고리즘을 쓰지 않고(2.3-4 원칙), 대신 OpenMPI 자체를 설치해 `stable-baselines[mpi]`가 정상 설치되게 했다(`libopenmpi-dev`·`openmpi-bin`·`libcrypt-dev`를 시스템에 설치, mpi4py 빌드에 `crypt.h`가 필요했다). 이 과정에서 `pip install --force-reinstall stable-baselines[mpi]`가 numpy 1.16.4→1.21.6, pandas 1.0.3→1.3.5, gym 0.15.3→0.26.2로 의존성을 올려버렸다(관문에서 `AssertionError`로 발견). `numpy==1.16.4 pandas==1.0.3 gym==0.15.3`을 `--no-deps`로 다시 고정해 해결했다. 설치 스크립트에 `step repin`을 추가해 앞으로는 `stable-baselines[mpi]` 설치 뒤 자동으로 재고정한다. main.py·판정 규칙과 무관, 측정값 없어 재시도 조건(2.4)에 해당.
