# F4·F5 WaveCorr 기록 (saeedmarzban/waveCorr @20ff832)

프로토콜 `notes/funnel_protocol.md`. 대상: "WaveCorr: Correlation-savvy Deep Reinforcement Learning for Portfolio Management"(arXiv 2109.07005). 순서상 Ensemble 다음이다(3.3, `notes/lit/f1/static_layer.csv` 순서 5). Ensemble의 F4/F5 결과와 무관하게 진행한다(3.3: 순서는 성과·다른 대상 상태와 무관, 고정).

## 1. 정적 확인 (2026-11-09, 실행 전)
- **코드 버전:** 저장소 생성 2021-06-01(`c5ab22d` Initial commit). 이 초기 버전(예: `aefaac2`, 2021-06-16)은 `epochs=5000`, `learningRate=5e-5`, `decayRate=0.99999`, `number_of_stocks=30`, `normalization_mode.no_norm`을 쓴다. 그런데 **이전 감사(`notes/code_audit_static.md` 20행, `notes/lit/f1/static_layer.csv` 순서 5행)가 이미 Table 2(Can-data SR 1.73±0.25, 10회)와 대조해 현재 HEAD `20ff832`(2022-08-15, "Delete run2.sh")를 기준으로 썼다** — `number_of_experiments=10`과 "무작위 50종목" 비고가 HEAD의 `number_of_stocks=50`과 일치하고, 초기 버전의 30종목·no_norm과는 다르다(저자가 "@author: Saeed Marzban"에서 "@author: Anonymous"로 바꾼 커밋도 이 구간에 있어, 심사용 익명화 재제출과 겹치는 개정으로 추정). **이 대상은 날짜가 아니라 "논문 표 값과 맞는 하이퍼파라미터"로 기준 커밋을 고른다**(2.1 규칙의 취지 — 코드가 논문과 대응하는지 — 를 날짜 대신 수치로 적용). HEAD `20ff832`를 쓴다. F2·F6 판정과 같은 커밋을 F4·F5에도 쓰므로 단계 간 기준 불일치가 없다.
- **파일 해시(20ff832):** `src/wavecorr_run.py` sha256은 설치 칸에서 고정 확인한다(관문).
- **README:** 짧다("wavecorr_run.py가 주 실행 파일, 파라미터를 지정해 돌린다"). WaveNet 기반 아키텍처(그림 2개).
- **데이터:** 저장소 내 `src/data/{can,us,covid}/` 번들(전체 52MB). `can`·`us`는 `trainSetLen=2766`, 입력을 4220행까지 자른다. 외부 다운로드 불필요.
- **하이퍼파라미터(HEAD, `wavecorr_run.py`):** `epochs=3000`, `learningRate=1e-4`, `decayRate=0.9999`, `minimmumRate=1e-5`, `minibatchSize=1`, `lookback_window=32`, `planning_horizon=32`, `seed=1111`, `net_depth=8`, `regularizer_multiplier=1e-6`, `RNN=True`, `keep_prob_value=.5`, `tradeFee=0.0005`, `constrain_action=False`, `dataset_name='can'`, `number_of_stocks=50`(실제 로드된 종목 수로 재조정), `train_mode=1`(다른 시드로 10회) → `number_of_experiments=10`.
- **실행 절차:** `train_mode=1`이면 `differentSeedExperiments(seed=1111, number_of_experiments=10)`가 `seed+1`부터 10회 `runSingleExperiment(seed)`를 순차 호출한다. 매 회 새 TF 세션을 만들어 `agent.train_test`로 3000 에폭을 학습한다(배치 1, `lookback_window` 안에서 반복). 10회가 각자 독립 실행이라 PPN의 S/P, Ensemble의 사이클과 같은 "반복 단위" 구조다.
- **에폭 내부 구조:** `train_test`(`wavecorr_agent.py` 190행)의 `for epoch in range(self.epochs):` 루프는 에폭마다 `time_spots`(약 `trainSetLen/(planning_horizon-2)` ≈ 92개 구간)를 돈다. 코드를 고치지 않고 내부에 시간 기록을 넣을 수 없으므로(허용 수정은 `main.py` 비수정과 같은 원칙), 에폭 수 전체를 두 값으로 바꿔 두 번 실행해 기울기로 1에폭당 시간을 구한다(2.3·2.4).
- **장치:** `tf.compat.v1.Session()`만 쓰고 명시적 GPU 배치가 없다(코드 확인). `requirements.txt`가 `tensorflow==1.14.0`(CPU 휠, GPU 전용 패키지 아님)을 고정하므로 CPU로만 돈다. Ensemble과 같은 이유로 PPN·RAT의 GPU 우선순위 규칙이 이 대상에는 적용되지 않는다.
- **비용·매개화(참고, `notes/code_audit_static.md` 20행에서 이미 확인, F4·F5와 무관):** 거래비용 0.0005, 반복 해로 비용 계산, 현금 칸 없음(등가중 시작), 선형 출력+softmax(무경계).
- **성과 노출 위험:** `wavecorr_agent.py`의 `train_test`가 학습 중 Sharpe·보상 등을 출력할 가능성이 높다(정확한 줄은 확인하지 않았다 — 열지 않을 대상이므로 성과 문구 필터로 충분하다, 2.1). 결과 저장 경로(`saveModel=False`로 호출하므로 모델 파일은 안 남긴다)와 표준출력만 있다.
- **설치:** `src/requirements.txt` 고정: `pandas==0.24.2`, `tensorflow==1.14.0`, `numpy==1.18.5`, `Keras==2.3.1`. Python 버전 명시 없음, TF 1.14 호환 범위로 Python 3.7(micromamba)을 쓴다(PPN·RAT·Ensemble과 같은 패턴). `wavecorr_enum.py`(18행, `normalization_mode` 열거형)도 같은 디렉터리에 있어야 import된다.

## 2. 사전 등록 (실행 전 고정, 이 커밋)

### 2.1 성과 비노출
- 표준출력, 저장 파일(있다면)은 열지 않는다. 화면·보고에는 설치 결과, 시간 이벤트, traceback만 쓴다.
- 래퍍는 자식 프로세스의 표준출력·표준오류를 파일로만 보내고, PPN·RAT·Ensemble과 같은 고정 필터(Error/Traceback/Killed 등 포함, sharpe·return·reward·pv·value 등 성과 문구가 든 줄은 제외)를 거친 마지막 15줄만 화면에 낸다.

### 2.2 환경
- Python 3.7(micromamba conda-forge). `src/requirements.txt`의 버전을 그대로 고정 설치한다. 관문 칸에서 버전·`import tensorflow, numpy, pandas, keras` 성공, `wavecorr_run.py`·`wavecorr_agent.py`·`wavecorr_network.py`·`wavecorr_input.py`·`wavecorr_enum.py`의 sha256을 확인하고 다르면 멈춘다.
- 장치: **CPU만 쓴다**(1절, GPU 전용 TF 패키지가 아니다). 측정 장치는 "서버 노트북(CPU)"로 적는다. Ensemble과 같은 이유로 장치 우선순위·모니터니시티 쟁점이 없다. 동시 실행 금지(PPN·RAT·Ensemble과 같음, 한 번에 한 대상만 돈다)는 그대로 적용한다.
- 시간대: 코드가 시간대를 쓰지 않는다. 별도 `TZ` 설정 불필요.

### 2.3 허용 수정(v3 2.3 준용)
1. **실행 래퍼:** `wavecorr_run.py`·`wavecorr_agent.py`·`wavecorr_network.py`·`wavecorr_input.py`·`wavecorr_enum.py`를 수정하지 않는다. 래퍼가 `wavecorr_run.py`를 읽어 하이퍼파라미터 정의 직후·`data = loadInput(...)` 직전까지를 실행한 뒤(PPN·RAT의 분할-실행과 같은 방식), **그 지점의 `epochs` 전역 변수만 래퍼가 두 값으로 바꿔 두 번**(아래 2) `runSingleExperiment(seed=1111, perm=1)`을 직접 호출한다. 파일 끝의 `if train_mode==1: differentSeedExperiments(...)` 10회 자동 디스패치가 나머지 부분을 실행할 때 같이 돌아버리는 것을 막기 위해 `train_mode`도 0(두 분기 모두 해당 없음)으로 바꾼다 — 전체 10회를 다 돌리지 않고 1회 실행을 두 에폭 수로 반복하는 것이 허용 수정 2다.
2. **실행 길이(1에폭당 시간 추정, 2점 보정):** `epochs = E1`로 1회(`runSingleExperiment`) 실행해 전체 벽시계 시간 `T1`을 재고, 같은 프로세스 안에서 새 TF 세션으로 `epochs = E2`(E2 > E1)로 다시 1회 실행해 `T2`를 잰다. `E1=5`, `E2=25`로 고정한다(측정 전 고정, 결과를 보고 바꾸지 않는다). 1에폭당 시간 `p = (T2−T1)/(E2−E1)`, 기동 시간 `startup = T1 − E1×p`. 전체 1회 실행 추정 시간 = `startup + 3000×p`. 나머지 하이퍼파라미터(학습률·배치·lookback 등)는 바꾸지 않는다.
3. **결과 기록:** 각 보정 실행의 시작·끝 시각을 `times.jsonl`에 쓴다(`calib1_start`/`calib1_end`, `calib2_start`/`calib2_end`). 값(Sharpe 등 성과)은 기록하지 않는다.

알고리즘·보상·관측·나머지 하이퍼파라미터·데이터 정규화·시드는 바꾸지 않는다(시드는 코드 기본값 1111을 그대로 쓴다, `perm=1`은 `differentSeedExperiments`가 넘기는 기본 인자와 같다).

### 2.4 실행
- **S:** 설치 → 관문(버전·import·해시 확인) → 보정 실행 1(epochs=5) → 보정 실행 2(epochs=25) 전체 경로.
- 벽시계 상한 3시간(PPN·RAT·Ensemble과 같은 기준, 두 보정 실행의 합에 적용). 넘으면 끊는다(두 번째 보정 실행 도중이면 그 실행만 끊고 첫 보정 실행 결과는 보존).
- 측정은 1회다(보정 실행 1·2 한 세트가 "1회"). 설치·실행 오류나 연결 끊김으로 값이 안 나올 때만 다시 돈다.
- 끊김 처리(PPN·RAT·Ensemble과 같음): 시간 표시를 60초마다 결과 폴더에 복사한다. 다시 실행하면 끝난 보정 실행은 건너뛴다. 끊긴 보정 실행은 처음부터 다시 돈다.

### 2.5 판정
**F4:** 두 보정 실행이 모두 `rc=0`이고 각자 끝 표시가 있으면 통과("2점 보정 기준, 3000에폭·10회 전체 미실행"으로 표기). 상한으로 끊기면 "상한 내 미완". 실패하면 허용 수정 범위에서 고친다.

**F5(판정값 A):**
A = 10 × (startup + 3000×p) / 3600 시간, 단 `p = (T2−T1)/(E2−E1)`, `startup = T1 − E1×p`(2.3-2).
- 10 = `number_of_experiments`(1절, 코드 값).
- A > 10: F5 "한도 초과"(장치 표기). 다음은 순서(3.3)상 큐의 다음 대상.
- A ≤ 10: F5 통과. F7 설정은 사전 등록에서 정해야 하므로 **멈추고 사용자에게 보고**한다.
- **하한 규칙:** 보정 실행 2(E2=25)가 상한으로 끊겨 `T2`가 없으면, 보정 실행 1(`T1`, E1=5)만으로 `p_lb = T1/E1`(기동 시간을 0으로 두는 보수적 상한 추정이 아니라 — 기동 시간을 무시하면 과소추정이므로 반대로 **A_lb = 10×(T1/E1)×3000/3600`**로 "한도 초과" 쪽으로만 보수적으로 쓴다. 보정 실행 1조차 상한에 걸리면 A_lb = 10×3 = 30시간("한도 초과(하한 기준)")로 확정한다.
- **일반 규칙(PPN·RAT·Ensemble과 같음):** 코드가 정한 항목(에폭 수 3000, 실험 수 10)은 코드 값을 그대로 쓴다(이 논문은 F6 대조에 쓴 Table 2 수치가 이미 이 코드 버전과 대응됨을 1절에서 확인했다).

**탐색적 기록:** CPU 이용률, 메모리, `p`의 신뢰도(두 보정 구간이 선형인지 — 에폭 5개와 25개 사이에 캐시·그래프 최적화 효과로 비선형일 수 있음, 판정에는 안 씀).

### 2.6 한계(실행 전)
- **2점(E1=5, E2=25) 선형 보정은 TF 그래프 최초 빌드·세션 시작 오버헤드가 두 실행 모두에 새로 들어간다는 뜻이다**(매 `runSingleExperiment` 호출이 새 `tf.compat.v1.Session()`을 연다). `startup`에 이 오버헤드가 들어가 있어 실제 10회 반복 시(10회 모두 새 세션을 열므로) `startup`도 10배 되는 것은 맞지만(식에 반영됨), 세션 재사용 최적화가 없다는 가정에 의존한다.
- E1=5·E2=25라는 적은 에폭으로 추정한 기울기는 3000에폭 전체로 외삽할 때 오차가 커질 수 있다(학습률 감쇠(`decayRate=0.9999`)로 에폭이 늘수록 각 에폭의 계산량 자체는 변하지 않지만, OS 캐시·메모리 단편화 등으로 뒤쪽이 느려질 수 있다 — 관찰되지 않는다).
- 30종목 버전(초판 추정)과 50종목 버전(HEAD)의 시간 차이를 재지 않았다. HEAD(50종목) 기준으로만 잰다.
- 종목 선택이 `os.listdir` 순서에 좌우돼 실행 환경(파일시스템)마다 다를 수 있다(1절 F2 비고, 시간 측정에는 영향 없음).
- `minibatchSize=1`이 코드 주석상 "가장 효율적"이라 하지만 실제 그런지 확인하지 않았다(저자 주장 그대로 둔다).

**실행 전 실패 기록 1(설치, 시간 측정 전, 2026-11-09, 성과 미확인):** 서버 노트북 시도 1에서 설치·해시 확인은 통과했지만 관문에서 `import tensorflow`가 Ensemble과 같은 `TypeError: Descriptors cannot not be created directly`로 실패했다(pip가 `tensorflow==1.14.0`과 함께 최신 `protobuf` 4.x를 설치, 2.6에 이미 예견한 범위). 설치 명령에 `pip install "protobuf<3.20"`을 추가해 고쳤다. main.py·판정 규칙과 무관, 측정값 없어 재시도 조건(2.4)에 해당.

**실행 전 실패 기록 2(실행 환경, 시간 측정 전, 2026-11-09, 성과 미확인):** 시도 2에서 관문은 통과했지만 보정 실행 1(`runSingleExperiment`)이 `wavecorr_agent.py`의 `save_results`에서 `FileNotFoundError: results/can_waveCorr_50stocks_seed1111_permutation1/APV_.csv`로 죽었다(`rc≠0`). 원인은 저장소 clone에 `results/` 최상위 디렉터리가 없는 것이다(`save_results`는 `os.mkdir(path)`를 `try/except:`(무조건 통과)로 감싸는데, 부모 디렉터리가 없으면 `os.mkdir`이 실패하고 그 예외가 조용히 삼켜진 뒤 바로 다음 `to_csv` 호출에서 진짜 오류가 난다 — git이 빈 디렉터리를 추적하지 않아 저자 작업 폴더에는 있었을 `results/`가 clone에는 없는 것으로 추정). `wavecorr_run.py`·`wavecorr_agent.py`를 고치지 않고, 래퍼가 실행 전에 `os.makedirs('results', exist_ok=True)`를 한 번 호출하도록 했다(환경 준비 단계, Ensemble의 `trained_models`/`results` 생성과 같은 범주). main.py·판정 규칙과 무관, 측정값 없어 재시도 조건(2.4)에 해당.
