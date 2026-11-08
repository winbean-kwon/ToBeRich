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
