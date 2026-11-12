# F4·F5 Adaptive DDPG 기록 (YinchuanLl/Reinforcement-learning-for-portfolio-allocation @326640a)

프로토콜 `notes/funnel_protocol.md`. 대상: Li, Li, Zhan, Liu, "Optimistic Bull or Pessimistic Bear: Adaptive Deep Reinforcement Learning for Stock Portfolio Allocation", ICML 2019 Workshop on AI in Finance(arXiv 1907.01503). 순서상 WaveCorr 다음이다(3.3, `notes/lit/f1/static_layer.csv` 순서 6).

## 1. 정적 확인 (2026-11-09, 실행 전) — 미완, 설계 판단이 필요해 멈춤

- **코드 버전:** 저장소는 2019-06-11 하루에 생성·업로드됐다(`0ba515e` Initial commit ~ `326640a` Update README.md, 5개 커밋 전부 같은 날). HEAD `326640a`를 쓴다(초판 전후를 가를 다른 날짜가 없다).
- **코드 구성:** 저장소 자체에는 `README.md`와 두 zip(`baselines.zip`, `gym.zip`)만 있다. `baselines.zip`은 OpenAI `baselines`의 전체 작업 복사본(자체 `.git` 포함, 베이스 커밋 `5d8041d` 2019-04-20)에 저자가 수정을 더한 것이다. `gym.zip`은 OpenAI `gym`의 전체 작업 복사본에 `gym/envs/portfolio/`(신규)를 더한 것이다.
- **베이스 대비 실제 수정(줄바꿈 노이즈 제외, `git diff -b`로 확인):** `baselines/ddpg/ddpg.py`(32줄), `baselines/ddpg/ddpg_learner.py`(83줄, 논문의 "adaptive" 메커니즘 — `alpha` 플레이스홀더로 `target_Q` 계산을 시장 지표 기반으로 보정), `baselines/ddpg/memory.py`(6줄), `baselines/run.py`(143줄), `baselines/common/cmd_util.py`(10줄), `baselines/bench/monitor.py`·`vec_env.py` 등 소폭. 새 파일(미추적): `calculate_table.py`(Table 1 생성, 성과 코드), `ddpg1.py`/`ddpg_learner1.py`/`memory1.py`(어떤 `.py` 파일도 import하지 않는다 — grep 확인, 미사용 dead code로 추정), 그 외 `.txt`·`.jpg`·`.npy`·`workshop_data/`(성과·결과 산출물로 추정, 열지 않음).
- **환경(`gym/envs/portfolio/portfolio_env.py`, 193줄):** `Portfolio-v0`. Dow30 중 거래일수가 정확히 4711인 종목 + NKE·KO를 더해 28종목. 초기 자산 100,000. 행동 공간 `Box(-20, 20, shape=(28,))`(종목당 최대 20주 매수·매도, "board_lot"). 관측 57차원([현금]+[가격 28]+[보유 주식 28]). **에피소드 길이 3268일**(`self.terminal = self.day >= 3268`, 2001~2014 데이터). 보상은 전후 총자산 차(거래비용 항 없음 — 코드 확인, 다른 대상과 달리 수수료가 명시적으로 없다). 종료 시 `plt.savefig(...)`로 그림을 저장하고 `print("total_reward:...")`로 **성과를 표준출력에 직접 찍는다**(2.1 대응 필요).
- **데이터:** `gym/envs/portfolio/Data_Daily_Stock_Dow_Jones_30/`에 번들(`dow_jones_30_daily_price.csv`, `^DJI.csv`). 외부 다운로드 불필요.
- **하드코딩 경로(허용 수정 대상):** `portfolio_env.py`가 데이터·그림 경로를 저자의 Windows 절대경로(`E:/Anaconda3/envs/tensorflow/Lib/site-packages/gym/envs/portfolio/...`)로 하드코딩했다. **README가 이미 "주소를 자신의 주소로 바꿔라"고 명시 지시**하므로(저자 공식 안내), 이 경로들을 실행 환경의 실제 경로로 바꾸는 것은 허용 수정이다(판정 규칙 변경이 아니라 설치 절차).
- **실행 절차(README):** `python -m baselines.run --alg=ddpg --env=Portfolio-v0 --num_timesteps=<N>` 형태(원문 그대로는 `run.py`를 실행, `--env` 기본값이 이미 `Portfolio-v0`, `--alg` 기본값이 이미 `ddpg`로 저자가 `cmd_util.py` 자체를 고쳐놓았다. 즉 인자 없이 `python -m baselines.run`만 돌려도 Portfolio DDPG가 돌아간다).
- **⚠ 막힌 지점(설계 판단 필요, 측정 전):** `cmd_util.py`가 고친 `--num_timesteps` 기본값은 **1e4(10,000)**다. 그런데 `baselines/ddpg/ddpg.py`의 `learn()`은 `nb_epochs = int(total_timesteps) // (nb_epoch_cycles * nb_rollout_steps)`로 에폭 수를 정하고, `nb_epoch_cycles`(기본 50)·`nb_rollout_steps`(기본 500)는 저자가 고치지 않았다(diff에 없음, portfolio 전용 `baselines/ddpg/defaults.py`도 없다 — 확인함). 50×500=25,000이므로 **10,000//25,000 = 0**, 즉 기본값 그대로 실행하면 **학습이 0 에폭, 사실상 아무것도 학습하지 않는다**. 저자가 실제 실험에서 쓴 `--num_timesteps` 값은 저장소에 남아 있지 않다(쉘 스크립트·README 예시 없음, `.txt`/`workshop_data/` 결과 파일은 성과라 열지 않았다). 즉 **이 코드의 유일하게 적힌 기본값이 비기능적**이라 PPN·RAT·Ensemble·WaveCorr처럼 "저장소 값을 그대로 쓴다"는 일반 규칙을 적용할 수가 없다(적용하면 "0 에폭 학습"이라는 무의미한 측정이 된다).

**다음 결정이 필요하다(사용자):**
1. 측정에 쓸 `num_timesteps`(또는 동등하게 에폭 수)를 어떻게 정할지 — 예: (a) 1에폭(25,000스텝)을 측정 단위로 삼고 그 시간만 보고하며 F5 "통과/초과" 판정은 "에폭 수를 알 수 없어 판정 불가"로 둔다, (b) PPN·RAT·Ensemble·WaveCorr의 10시간 상한에 맞춰 "몇 에폭까지 돌릴 수 있는지"를 역으로 재는 방식으로 F5를 재정의한다, (c) 이 대상을 "미시험(정적 의심)"으로 분류하고 다음 대상으로 넘어간다(`notes/funnel_protocol.md` 부록 A가 이미 RAT·WaveCorr 등에 썼던 분류와 같은 범주).
2. 보상에 거래비용이 없다는 점(F2 비고, 논문 본문과 대조 필요하지만 F4/F5 시간 측정과는 무관)과 `ddpg1.py` 등 미사용 파일을 무시해도 되는지 확인(가능성 높지만 재확인 안 함).

이 판단이 날 때까지 F4/F5 사전 등록(2절)·로컬 스크립트는 작성하지 않는다(사전 등록 원칙 — 핵심 실험 변수를 결과를 보지 않은 상태에서 임의로 정해 커밋하면 사후에 바꾸기 어렵고, 이건 "경로만 바꾸는" 수준의 허용 수정이 아니라 측정 단위 자체를 새로 정의하는 것이라 사용자 승인이 필요하다고 판단했다).

**결정(2026-11-10, 사용자가 "추천대로" 위임, 측정 전·성과 미열람):** F7 두 자리가 RAT·Ensemble로 찼으므로(프로토콜 3.3-3 "2편이 차면 이후 논문은 F4까지만") 이 대상은 **F4까지만** 진행한다. F5(시간 상한 판정)는 적용하지 않아 학습 길이를 정할 필요가 없다. F4 실행 단위는 **1에폭 = `nb_epoch_cycles`(50) × `nb_rollout_steps`(500) = 25,000스텝**(`--num_timesteps=25000`)으로 고정하고, "학습 1에폭과 그 뒤 평가 경로가 오류 없이 끝나면 통과"로 판정한다. 저장소 기본값(1e4)이 0에폭이 되는 점은 F2 비고("논문·코드에 학습 길이가 사실상 지정되지 않음")로 기록한다. 이 대상의 F4 사전 등록·로컬 스크립트는 F4 예산(벽시계 40시간) 안에서 순서대로 쓴다.

## 2. F4 사전 등록 (2026-11-11, 실행 전, 성과 미열람)

순서: 프로토콜 3.3에 따라 S56의 다음 대상(EIIE 앞 순번, F7 자리 없음 → F4까지만). 실행 장치: 서버 노트북 WSL2 CPU. **RAT F7(R1~R5)이 끝난 뒤** 순서 스크립트가 실행한다(메모리 3.9GB, RAT 학습 2.5GB와 동시 실행 금지).

### 2.1 코드·환경
- 저장소 HEAD `326640a`, `baselines.zip` sha256 `8481a9c8…c560`, `gym.zip` sha256 `d58a57f0…c4d0`(정적 확인 시 값). 두 zip을 푼다. baselines(베이스 `5d8041d`)는 `pip install -e`로 설치한다. gym 사본은 site-packages의 패키지 폴더 자체(setup.py 없음, 0.10.0)라서 `pip install gym==0.10.0`으로 의존성을 맞춘 뒤 설치된 gym 폴더를 사본으로 바꾼다(저자가 site-packages gym을 고친 환경과 같은 상태). (설치 1차 시도에서 setup.py를 찾지 못해 실패한 뒤 정정, 실행 전)
- Python 3.7, tensorflow 1.15.2, numpy 1.16.4, pandas 1.0.3, scipy·matplotlib는 TF1.15·py3.7과 맞는 고정 버전. baselines `install_requires`(scipy, tqdm, joblib, dill, progressbar2, cloudpickle, click, opencv-python)는 pip가 고르는 버전으로 설치하고 `install_versions.log`에 남긴다. mpi4py는 설치하지 않는다(코드가 `MPI is None` 분기를 가짐).

### 2.2 허용 수정(v3 2.3 범위)
1. **경로(README 지시):** `portfolio_env.py`·`portfolio_testenv.py`의 `E:/Anaconda3/envs/tensorflow/Lib/site-packages/gym/envs/portfolio/`와 `.../gym/envs/zxstock/` 접두어를 설치된 `gym/envs/portfolio/` 실제 경로로 바꾼다(sed, 그 밖의 글자는 그대로). 그림 저장 폴더 `DQN/`이 없으면 만든다.
2. **실행 인자:** `python -m baselines.run --num_timesteps=25000 --seed=0 --play`. 1에폭(50×500)은 2026-11-10 결정 그대로. `--play`는 저자 코드의 시험 경로(`PortfolioTest-v0`, 1190스텝 고정 루프)다. `--seed=0`은 기록용(저장소 기본 None).
3. **성과 비노출(프로토콜 2.2):** 표준출력·표준오류는 파일로만 보내고 열지 않는다. 시험 env가 끝에 쓰는 `Adaptive DDPG.txt`(가치 경로)와 그림도 열지 않는다. 판정에 쓰는 것은 종료 코드, 벽시계 시간, 아래 표지 파일의 **존재 여부**뿐이다.

### 2.3 판정
- **F4 통과:** rc = 0이고, 작업 폴더에 `Adaptive DDPG.txt`가 생김(시험 env가 terminal(day ≥ 1189)에 도달해야 쓰는 파일 = 학습 1에폭 후 시험 경로 끝까지 실행). 표기: "1에폭(25,000스텝) 기준, 논문 학습 길이 미지정".
- **F4 실패:** rc ≠ 0 또는 표지 없음. 오류는 stderr 마지막 40줄만 열어 원인을 적는다(성과 줄이 섞이면 그 줄은 옮기지 않는다). 허용 수정 범위 안에서 고칠 수 있으면 고쳐 최대 3회까지 다시 돈다. 설치 실패는 "실행 불가(환경)"로 적는다.
- **상한:** 실행 1회 벽시계 3시간. 넘으면 끊고 "상한 내 미완"(실행 실패로 세지 않음).
- F5는 적용하지 않는다(F7 자리 없음). 시간은 참고로만 적는다.
- **예산:** F4 대상별 작업 기록이 대상마다 같은 형식으로 남아 있지 않아 전체 40시간 대비 누적 사용량을 정확히 계산할 수 없다(한계로 적는다). 남은 대상은 프로토콜 3.3 순서대로 진행하고 11-24에 멈춘 위치 이후는 "미시험(일정)"이다.

스크립트: `replication/funnel_f4_li2019_local.py`(이 절과 같은 커밋).

**설치 정정 기록(2026-11-12, 실행 전, 성과 미열람):** 관문에서 환경 import 시 matplotlib가 Tk 창을 열려다 실패했다(서버에 디스플레이 없음). 관문과 실행에 환경변수 `MPLBACKEND=Agg`를 준다(코드 수정 아님, 그림은 파일로만 저장).

**설치 정정 기록 2(2026-11-12, 실행 전, 성과 미열람):** 02:55 관문이 다시 실패했다. (1) 같은 저자 경로 접두어(`E:/Anaconda3/.../gym/envs/zxstock/`)가 env 두 파일 밖의 학습 코드 `baselines/ddpg/ddpg.py` 287행(손실 그림 저장)에도 있다. 허용 수정 1(경로 접두어 교체)을 이 파일에도 같은 방식으로 적용한다. 실행에 쓰지 않는 독립 그림 스크립트 `plot_property.py`는 고치지 않는다. (2) 관문이 `import baselines.run`을 하면 저자 `run.py` 끝의 조건 없는 `main()`이 실행돼 기본값(0에폭)으로 학습 경로가 돈다. 관문은 `baselines.ddpg.ddpg`·`baselines.common.cmd_util`·`gym.envs.portfolio`만 import한다(본 실행은 원래대로 `python -m baselines.run`). 관문 출력에서 본 것은 에이전트 설정 출력과 traceback뿐이고 성과 값은 없었다. (3) 11-11 22:39의 설치 실패 기록 `done.json`(`실행 불가(환경)`, stage install)은 설치 정정 전의 기록이라 `done.install_fail_1111.json`으로 이름을 바꿔 보존하고, 환경을 처음부터 다시 설치한다. 본 실행 시도 수(최대 3)에는 넣지 않는다(본 실행은 아직 시작한 적 없음). 실행은 RAT F7이 끝난 뒤 `replication/funnel_f4_after_rat.sh`(tmux `f4_seq`)가 한다.

## 3. 결과(2026-11-12)
- **F4 통과(1에폭 기준, 논문 학습 길이 미지정).** 시도 1(서버 WSL CPU, RAT F7 종료 직후 16:19 시작): rc 0, 76.5초, 표지 `Adaptive DDPG.txt` 존재(열지 않음). 설치 실패 기록(11-11)은 `done.install_fail_1111.json`으로 보존.
