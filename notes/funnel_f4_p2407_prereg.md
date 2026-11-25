# P24-07(Markowitz Meets Bellman, KDD) — F4·F5 사전 등록 (2026-11-25, 실행 전, 성과 미열람)

## 0. 지위와 결정
- **탐색적(프로토콜 3.3 밖).** F1 저자 계정 점검에서 찾은 논문의 후속 단계다. `notes/funnel_f1_recheck_followup.md`의 이탈 결정(사용자, 2026-11-24)을 따른다. 본 깔때기의 F7 자리와 순서에는 들어가지 않는다.
- 사용자 결정(2026-11-25, 결과를 보기 전):
  - 비교 기준은 "저자 실행(5종목)"이다.
  - 실험은 두 가지를 모두 한다. ① 저자 학습 모델 평가와 ② 공개 코드로 새로 학습이다.
- 이 문서는 F4(실행되는가)와 F5(계산 한도)만 정한다. 재현 판정(F7x)의 보고값·허용 폭·판정 규칙은 F4를 마친 뒤, **성과를 열기 전에** 별도 문서로 사전 등록하고 반박 심사를 받는다.

## 1. 대상
- 저장소 `BMEgang/BellmanMarkwitzProject`. 코드 커밋은 `93c273f`(2024-02-17) 하나다. 이 커밋은 arXiv v1(2405.05449, 2024-05)보다 앞서므로 버전 규칙 2.1상 이 커밋을 쓴다.
- 스크립트: `draw/algo/knowledgement_drill_ddpg.py`, 공개된 그대로 쓴다.
  - 5종목 필터(AAPL, BA, CRM, UNH, V)가 켜져 있다.
  - FinRL `StockTradingEnv`, DDPG 50,000스텝, 거래비용 0.1%, `hmax 100`, 초기 10,000, `reward_scaling 1e-4`.
  - 거래 구간은 2016-01-01~2018-09-01이고, 평가 환경은 `risk_indicator_col='vix'`다.
- 공개 `draw/algo/policies.py`의 Markowitz 증류 블록은 주석 처리되어 있다(정적 관찰, `notes/funnel_f1_recheck_followup.md`). 따라서 ②는 증류 없는 5종목 DDPG다. 이 점은 판정 문서에서 해석한다.
- 저자 실행 폴더 `final/2023-11-21_19-19-07`(KDD 곡선 `draw/richard.csv`와 같은 blob인 `data/originate_ddpg.csv`가 있는 폴더):
  - `model/agent_ddpg.zip` sha256 bd97bda2…7c5b
  - `data/train_data.csv` sha256 2c704217…f5f6. 7,550행, 5종목, 2009-01-02~2014-12-31(1,510일).
  - `data/trade_data.csv` sha256 890ea0b0…4608. 3,355행, 5종목, 2016-01-04~2018-08-30(671일).
  - 결과 파일(`data/originate_ddpg.csv`, `draw/richard*.csv`)은 열지 않는다. 학습 로그 `result/progress.csv`는 F4 준비 중 첫 줄 몇 개를 열었다(학습 구간 손실·보상, 거래 구간 아님).

## 2. 환경(맥, CPU)
- 저자 모델 zip의 `system_info.txt`에는 macOS(Apple M1에서 x86_64 Python), Python 3.10.13, SB3 2.2.0a11, PyTorch 2.1.0, NumPy 1.26.1, Gymnasium 0.29.1이 적혀 있다.
- 우리 환경:
  - conda Python 3.10(arm64)
  - PyPI `stable-baselines3==2.2.0a11`, `torch==2.1.0`, `numpy==1.26.1`, `gymnasium==0.29.1`
  - FinRL은 저자 지시("pip install git+…FinRL")를 따라 KDD 실행(2023-11-21) 전 마지막 커밋 `55764e824c`(2023-11-19)를 `--no-deps`로 설치한다.
  - 나머지(pandas, stockstats, matplotlib 등)는 import가 되는 최소 판을 설치하고 `pip freeze`를 남긴다.
- 저자 `policies.py`는 SB3에 덮어쓰지 않는다. 주석과 빈 줄을 빼고 비교하면 SB3 2.2.1(=2.3.0) 원본과 같고, 다른 점은 쓰지 않는 import와 쓰지 않는 클래스(`HuFeatureExtractor`)뿐이다. 즉 실행되는 계산은 같다.
- 아키텍처 차이(arm64 대 저자 x86_64 Rosetta)는 부동소수 차이를 낼 수 있다. 기록만 한다.

## 3. 허용 수정(실행 래퍼, 저자 파일 무수정)
1. **입력:** 스크립트는 `/Users/ganghu/…/raw_data.csv`(저장소에 없음, `weight` 열 포함)를 읽고, 5종목으로 거른 뒤 나눠서 `train_data.csv`·`trade_data.csv`로 저장하고 곧바로 다시 읽는다. 래퍼는 이 읽기·필터·분할 단계를 건너뛰고, 1절의 저자 실행 폴더 분할 파일을 그대로 쓴다. 이후 코드는 원문 그대로다.
2. **경로:** `base_folder`를 우리 출력 폴더로 바꾼다.
3. **시드(②만):** `agent.get_model("ddpg", seed=s)`로 SB3 시드를 준다. 저자 모델은 `seed None`(미고정)이다.
4. `MPLBACKEND=Agg`.
5. 래퍼와 저자 스크립트의 차이(diff)는 커밋한다.

## 4. F4 실행
- **①** 저자 `agent_ddpg.zip`을 `DDPG.load`로 읽고, 스크립트와 같은 `env_kwargs`와 `risk_indicator_col='vix'`로 `DRLAgent.DRL_prediction`을 거래 데이터에 돌린다. 계좌 가치 CSV를 저장한다.
- **②** 시드 0, 50,000스텝 전체 학습(논문 설정 그대로) → 같은 방식으로 예측 → 계좌 가치 CSV 저장. 시간을 잰다.
- **판정:**
  - F4 통과 조건: ①과 ②가 예외 없이 끝나고, 계좌 가치 CSV가 생기며, 행 수가 거래일 수에 맞음(671 또는 FinRL 관례에 따른 ±1).
  - 오류가 나면 원인만 확인해 허용 수정 범위 안에서 고친다. 최대 3회, 벽시계 8시간을 넘으면 "F4 실패"다.

## 5. F5
- 시드당 시간 = ② 시드 0의 학습과 예측 벽시계 시간(맥, 측정 장치 명시).
- 10시간 이하이면 통과다.

## 6. 성과 비노출
- F7x 사전 등록 커밋 전에는 다음을 열지 않는다: 계좌 가치 CSV, 행동 CSV, 표준출력 로그(FinRL이 계좌 가치를 출력함), SB3 progress·tensorboard.
- F4 판정에는 종료 코드, 예외, 파일 존재와 행 수, 시간만 쓴다.
