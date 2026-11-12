# F4 ADRL 기록 (cspun/ADRLwIntReward @2e73349)

프로토콜 `notes/funnel_protocol.md`. 대상: Lim, Lesmana, Pun, "Autoregressive DRL with Learned Intrinsic Rewards for Portfolio Optimisation", ICAIF 2024(보충 표본 SUP-ADRL). 정적 층 순서 11. F7 자리가 차서 **F4까지만**. 서버 대기열에서 SmartFolio 다음.

## 1. 코드 읽기(정적, 2026-11-12)
- 저장소 44MB. 번들 데이터 `done_data.csv`(전처리 완료), `data/`(dow30 2009–2020). 수정된 stable_baselines 사본을 저장소에 포함한다(`A2C_autoregressive` 등). `requirements.txt`: numpy 1.16.4, pandas 1.0.3, scikit-learn 0.21.0, gym 0.15.3, stable-baselines[mpi], tensorflow 1.15.4, joblib 0.15.1, matplotlib 3.2.1(stockstats는 판 없음). 코드는 `quantstats`도 import한다(requirements에 없음).
- 진입점 `A2C_autoregressive_run.py`(논문의 제안 방법, autoregressive + 학습된 내재 보상). 파일 끝에서 `run()`을 조건 없이 호출한다: 보상 5종(profit, logreturn, csr, dsr1, dsr2) × 시드 17개 × 각 `run_once`. `run_once`는 Ensemble(ICAIF 2020) 계열 환경으로 2015-10~2020-07을 63일 재학습·63일 검증 사이클(18회)로 돌며, 사이클마다 내재 보상 A2C와 원 A2C를 각 6,000스텝 학습·검증하고 Sharpe로 고른 뒤 세 경로(내재·원·선택)로 거래한다. 끝나면 `results/autoA2C/<보상>/SUMMARYRESULTS.csv`에 한 줄을 덧붙인다.
- `results/` 폴더가 저장소에 없고 코드가 만들지 않는다. `config.py`는 import 시 `trained_models/<시각>`을 만든다.

## 2. F4 사전 등록(2026-11-12, 실행 전, 성과 미열람)

### 2.1 실행 단위
- `A2C_autoregressive_run.py`를 수정 없이 실행하고, **첫 단위**(보상 profit, 시드 6280: 18사이클 학습·검증·거래 전체)가 `results/autoA2C/profit/SUMMARYRESULTS.csv`에 첫 줄을 쓰면 프로세스를 멈춘다. 전체 85단위는 F4 범위를 넘는다(F7 대상 아님).
- 비자기회귀 스크립트(`A2C_nonautoregressive_run.py`)는 돌리지 않는다(같은 계열의 비교 조건).

### 2.2 환경(서버 WSL2 CPU)
- Python 3.7, requirements.txt 고정값 그대로(위), protobuf<3.20. 판이 없는 것: stockstats 0.3.2, quantstats 0.0.59, cloudpickle 1.6.0, opencv-python-headless 4.2.0.34(번들 stable_baselines 의존성). pip `stable-baselines`는 설치하지 않고 저장소 번들 사본을 쓴다. mpi4py는 설치하지 않는다(번들 `__init__`이 mpi 없을 때를 처리, A2C는 mpi 불필요).

### 2.3 허용 수정(v3 2.3)
1. 출력 폴더 생성: 실행 사본에 `results/autoA2C/<보상 5종>/`을 만든다. 코드는 고치지 않는다.
2. 실행 사본: `git archive 2e73349`로 실행 폴더를 만든다.

### 2.4 판정
- **F4 통과:** 첫 단위의 `SUMMARYRESULTS.csv`가 생기고 크기 > 0(존재·크기만 확인, 열지 않음) → 그 시점에 정지.
- **F4 실패:** 그 전에 프로세스가 끝나면. stderr 마지막 40줄만 연다. 허용 수정 범위에서 고칠 수 있으면 고쳐 최대 3회. 설치 실패는 시도로 세지 않는다.
- **상한:** 첫 단위까지 벽시계 3시간. 넘으면 "상한 내 미완".
- **성과 비노출:** stdout(검증·거래 Sharpe print), `results/` CSV, 모델 파일을 열지 않는다.

스크립트: `replication/funnel_f4_adrl_local.py`, 순서: `replication/funnel_f4_after_smartfolio.sh`.

**설치 정정(2026-11-12 18:10, 실행 전, 성과 미열람):** 첫 설치(16:35)는 `extra` 단계에서 pip 오류로 멈췄고, 다시 설치한 환경은 관문에서 `import quantstats` → `yfinance` → `multitasking`의 `from typing import TypedDict`로 실패했다(최신 multitasking은 Python 3.8 이상). quantstats 0.0.59가 판을 고정하지 않은 의존성이라, `extra` 단계에 Python 3.7과 맞는 2022년 판 `yfinance==0.1.70`·`multitasking==0.0.11`을 더한다. 환경은 처음부터 다시 만든다(`env_ok`·`gate_ok` 삭제). 코드·판정·상한은 그대로이고, 설치 실패이므로 시도 횟수에 넣지 않는다.

## 3. 결과(2026-11-12, 성과 미열람): **F4 실행 불가**
- 설치(정정 2 반영)는 통과했다: python 3.7.12, tf 1.15.4, gym 0.15.3, numpy 1.16.4, pandas 1.0.3.
- 관문에서 `stable_baselines/__init__.py` 5행 `from stable_baselines.a2c_original import A2C_Original`이 `ModuleNotFoundError`로 실패했다. 같은 파일이 `a2c_original`, `a2c_timedebug`, `a2c_infrequentintrinsic_old`, `a2c_infrequentintrinsic`, `a2c_infrequentintrinsictimedebug` 5개를 import하는데, 저장소(@2e73349)에 이 모듈들의 소스가 없다.
- 저장소 이력 26커밋 전체에도 이 `.py` 파일은 없다. `1ac855c`(2024-08-03, "Add files via upload")에 `stable_baselines/a2c/__pycache__/a2c_original.cpython-38.pyc` 하나만 있고, 이것도 `__init__`이 찾는 경로(`stable_baselines.a2c_original`)와 다르다. 저자 로컬에만 있던 파일이 공개되지 않은 것으로 보인다.
- **시도 1(실제 실행, 2.4):** 실행 사본(`git archive 2e73349`)에 출력 폴더만 만들고 `A2C_autoregressive_run.py`를 그대로 실행했다. 16행 `from stable_baselines import A2C_autoregressive as A2C`에서 같은 오류로 rc 1, 1초, stdout 0바이트. 서버 WSL CPU, 18:1x 시작.
- **판정:** 고치려면 누락 모듈을 새로 쓰거나(스텁 포함) 저자 `__init__.py`의 import를 지워야 한다. 둘 다 v3 2.3 허용 수정(호환 shim·날짜 인자·비용 함수·결과 기록)에 해당하지 않으므로 v3 1.1 규칙대로 **실행 불가**로 판정하고 시도 2·3은 하지 않는다.
- 이탈 가능성(사용자 결정 사항, 실행하지 않음): 진입점이 쓰는 것은 `A2C_autoregressive`와 `A2C`뿐이라, 누락 5개 import를 지우면 돌 가능성이 있다. 이는 허용 목록 밖의 코드 수정이므로 하려면 결과를 보기 전에 이탈로 기록해야 하고, 그 경우에도 "공개 코드 그대로는 실행 불가"는 바뀌지 않는다.
