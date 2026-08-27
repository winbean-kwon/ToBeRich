# 관련 연구 스캐폴드

**주의**: 아래 인용 중 "✅ 확인됨"은 프로젝트 내 다른 문서(`progress_report_final.md` §4 References,
`RL_PIVOT_SUMMARY.md`)에 이미 정확한 서지정보(저자·연도·venue)가 기록돼 있어 재사용 가능한 것들이다.
"⚠️ 확인 필요"는 이 세션에서 실제로 방법론 이식에 썼지만(노트북 §13 주석에 근거) 정확한 서지정보를
직접 검증하지 않은 것 — **투고 전 원문 대조해서 정확한 인용 정보로 교체할 것**. 확인되지 않은 서지
정보를 추측으로 채워넣지 않았다.

---

## 1. 이 프로젝트가 직접 이식한 방법론

### ✅ EarnHFT — 계층적 RL의 뼈대 (2026-07-29 웹 검색으로 venue 확인)
Qin, M., Sun, S., Zhang, W., Xia, H., Wang, X., & An, B. (2024). **EarnHFT: Efficient Hierarchical
Reinforcement Learning for High Frequency Trading**. *Proceedings of the AAAI Conference on Artificial
Intelligence*, 38(21). arXiv:2309.12891. https://arxiv.org/abs/2309.12891
(공식 구현: https://github.com/qinmoelei/EarnHFT — 저자명은 arXiv 페이지에서 재확인 권장, 검색
결과에서는 1저자만 확정적으로 확인됨)

이 프로젝트의 Stage A(레짐 분할)/Stage B(β 선호도 풀)/Stage C(라우터) 구조 전체의 원형. 원 논문은
**초 단위·단일자산(BTC 등) 고빈도 트레이딩**을 대상으로 하며, Stage I(DP 기반 Q-teacher, "수백 개
에이전트를 학습해 수익률 기준으로 선별")까지 포함한 3단계 전체가 원안이다. 이 프로젝트가 이식하지
않은 부분(Stage I)이 바로 핵심 발견(v3의 다양성 붕괴, `paper/FINDINGS_LOG.md` §3)으로 이어짐 —
"단일자산·이산 포지션 논문을 다자산·연속 비중 세팅으로 옮기면서 Stage I을 뺐더니 다양성 엔진이
사라졌다"는 것이 이 프로젝트의 핵심 대조점이므로, 원문 Stage I 수식(Algorithm 1, Eq. 2-4)을
정확히 인용해 "무엇을 안 가져왔는지"를 명시할 것.

### ✅ FreQuant — top-K 희소 종목선택 (2026-07-29 웹 검색으로 확인)
Jeon, J., Park, J., Park, C., & Kang, U. (2024). **FreQuant: A Reinforcement-Learning based Adaptive
Portfolio Optimization with Multi-frequency Decomposition**. *Proceedings of the 30th ACM SIGKDD
Conference on Knowledge Discovery and Data Mining (KDD '24)*, 1211–1221.
https://dl.acm.org/doi/10.1145/3637528.3671668

핵심 기여는 시간 도메인이 아니라 **주파수 도메인 전체에서 동작하는 RL 프레임워크**로, Frequency
State Encoder(FSE, Multi-Event Fusion Network + Frequency-Relation Encoder)를 통해 급격한
시장 충격(abrupt events)과 평상시 패턴(prevalent patterns)을 동시에 포착한다. v4(§13-A)에서
가져온 "top-K 희소 선택"은 이 논문의 한 구성요소(Eq. 13-14 confidence score 기반 선택)이며,
**주파수 도메인 인코더 자체는 이 프로젝트에서 이식하지 않았다** — 이 점을 논문에 명시할 것
(FreQuant의 부분 이식이지 전체 재현이 아님).

### ✅ DeepClair — 시장 예측 기반 포트폴리오 선택 (2026-07-29 웹 검색으로 확인)
Choi, D., Kim, J., Gim, M., Lee, J., & Kang, J. (2024). **DeepClair: Utilizing Market Forecasts for
Effective Portfolio Selection**. *Proceedings of the 33rd ACM International Conference on Information
and Knowledge Management (CIKM '24)*. arXiv:2407.13427. https://arxiv.org/abs/2407.13427

핵심 기여는 Transformer 기반 시계열 예측 모델을 먼저 사전학습하고(시장 가격 예측), 이를 LoRA로
파인튜닝해 RL 기반 포트폴리오 선택 프레임워크에 통합하는 2단계 전략이다. v4(§13-A)에서 가져온
"전용 리스크게이트 ρ(총 익스포저 결정)"는 이 논문의 예측 기반 롱/숏 비율 결정 아이디어를 단순화해
이식한 것 — **원 논문의 예측모듈 사전학습·LoRA 파인튜닝 자체는 이식하지 않았다**(이 프로젝트는
이미 Chronos+MTGNN 하이브리드 백본이 그 역할을 대신함). 이것도 부분 이식임을 명시할 것.

### ✅ 다자산 포트폴리오 HRL 선행 연구 지형 — "아무도 안 해봤다" 과잉주장 방지용 (2026-08-26 웹 검색으로 확인)

이 프로젝트가 방법론을 이식한 문헌은 아니지만, "계층적 RL을 다자산 연속비중 포트폴리오에 적용한
시도 자체가 선행연구에 없다"는 과도하게 넓은 주장을 막기 위해 §2.1(Related Work) EarnHFT 단락
직후에 반드시 인용해야 하는 지형 문헌. 외부 검토(2026-08-26)에서 이 공백이 지적되어 추가함 —
DRAFT.md/DRAFT_KR.md §2.1에 이미 반영 완료.

- Wang, R., Wei, H., An, B., Feng, Z., & Yao, J. (2021). **Commission Fee is not Enough: A
  Hierarchical Reinforced Framework for Portfolio Management**. *Proceedings of the AAAI Conference
  on Artificial Intelligence*, 35(1), 626–633. (HRPM)
  — 전략적 배분(저빈도 상위정책)과 주문 실행(슬리피지 최소화, 하위정책)을 분리한 2단계 계층.
  리스크 선호도 조건부 전문가 풀이나 레짐 라우터는 없음.
- Zha, L., Dai, L., Xu, T., & Wu, D. (2022). **A Hierarchical Reinforcement Learning Framework for
  Stock Selection and Portfolio**. *2022 International Joint Conference on Neural Networks (IJCNN)*,
  1–7. DOI: 10.1109/IJCNN55064.2022.9892378.
  — 상위정책이 대규모 유니버스에서 유망 종목 부분집합을 선별하고, 하위정책이 그 부분집합에
  대해서만 연속 비중을 배분하는 선별+배분 2단계.
- Niu, H., Li, S., & Li, J. (2022). **MetaTrader: An Reinforcement Learning Approach Integrating
  Diverse Policies for Portfolio Optimization**. *Proceedings of the 31st ACM International
  Conference on Information and Knowledge Management (CIKM '22)*. arXiv:2210.01774.
  — RL+모방학습 결합 목적함수로 다양한 트레이딩 정책을 먼저 학습한 뒤, 메타정책이 그 사이를
  라우팅. 구조적으로 EarnHFT의 Stage II–III와 가장 가깝지만 다양성 유발원이 DP 교사가 아니라
  모방학습 항이고, 처음부터 다자산 세팅.
- Millea, A., & Edalat, A. (2023). **Using Deep Reinforcement Learning with Hierarchical Risk Parity
  for Portfolio Optimization**. *International Journal of Financial Studies*, 11(1), 10.
  DOI: 10.3390/ijfs11010010.
  — DRL 에이전트를 상태적(stateful) 멀티암드밴딧으로 프레이밍해, 여러 HRP/HERC(비학습) 배분기
  중 어느 것을 쓸지만 선택. 하위 배분기 자체는 학습되지 않으므로 연속 비중을 직접 학습하는
  어려움을 회피.
- Zong, C., Wang, C., Qin, M., Feng, L., Wang, X., & An, B. (2024). **MacroHFT: Memory Augmented
  Context-aware Reinforcement Learning On High Frequency Trading**. *Proceedings of the 30th ACM
  SIGKDD Conference on Knowledge Discovery and Data Mining (KDD '24)*. arXiv:2406.14537.
  — EarnHFT와 저자진이 일부 겹치는(Xinrun Wang, Bo An 공저) 후속작. 레짐(추세·변동성)별로 분해된
  하위 에이전트 + 메모리 증강 하이퍼에이전트가 이들을 혼합. 단, 여전히 단일자산·고빈도 세팅에 국한.
- Coriat, B., & Benhamou, E. (2025). **HARLF: Hierarchical Reinforcement Learning and Lightweight
  LLM-Driven Sentiment Integration for Financial Portfolio Optimization**. arXiv:2507.18560.
  (2026-08 기준 동료심사 미완료 프리프린트 — 인용 시 명시할 것)
  — 기초 에이전트(base)/메타 에이전트(meta)/슈퍼 에이전트(super) 3단계로 다자산 배분을 수행하며
  LLM 기반 센티먼트를 결합.

**이 프로젝트와의 관계**: 위 6편 모두 "다자산 + 계층적 RL" 조합 자체는 다루므로, §2.1에서 "이런
시도가 전혀 없었다"는 절대적 문구는 쓸 수 없다. 그러나 여섯 편 중 EarnHFT의 3단계 파이프라인
(DP 교사로 학습한 전문가 풀 + 검증기반 증류 + 레짐 라우터)을 Q-teacher 없이 그대로 연속 다자산
심플렉스로 이식하며 그 과정의 실패 연쇄(비용에 의한 신호 소거 → 다양성 붕괴 → 라우터 상수함수화)를
기록하고 검증/테스트 일관성 진단으로 검증한 사례는 없다 — 이것이 §1.4의 좁혀진 기여 주장이 실제로
방어 가능한 지점이다.

---

## 2. 백본/피처 관련 (✅ 전부 확인됨 — `progress_report_final.md` §4에서 그대로 재사용 가능)

- Ansari, A. F., et al. (2024). **Chronos: Learning the Language of Time Series**. Amazon Science/arXiv.
- Wu, Z., et al. (2020). **Connecting the Dots: Multivariate Time Series Forecasting with Graph Neural
  Networks (MTGNN)**. KDD 2020.
- Nie, Y., et al. (2023). **PatchTST**. ICLR 2023.
- Liu, Y., et al. (2023). **iTransformer**. ICLR 2024.
- Gu, A., & Dao, T. (2023). **Mamba**. arXiv.
- Hu, E. J., et al. (2022). **LoRA**. ICLR 2022.
- Kim, T., et al. (2022). **RevIN**. ICLR 2022.
- Wang, Y., et al. (2022). **StockMixer**. AAAI 2023.

크립토 트랙에도 동일 백본(Chronos+MTGNN 하이브리드)이 재사용됐으므로, 이 인용들은 그대로
크립토 트랙 논문에도 유효하다.

## 3. 고전 포트폴리오 최적화 (✅ 확인됨)

- Black, F., & Litterman, R. (1992). **Global Portfolio Optimization**. Financial Analysts Journal.
- Ledoit, O., & Wolf, M. (2004). **A Well-Conditioned Estimator for Large-Dimensional Covariance
  Matrices**. Journal of Multivariate Analysis.
- Markowitz MVO — `GAP_ANALYSIS.md` §2.1의 베이스라인으로 실제 구현 시 원 논문(Markowitz, 1952,
  *Portfolio Selection*, Journal of Finance) 인용 필요.

## 4. RL 알고리즘 (✅ 확인됨)

- Schulman, J., et al. (2017). **Proximal Policy Optimization Algorithms (PPO)**. arXiv.
- DQN(라우터에 사용) — Mnih, V., et al. (2015). **Human-level control through deep reinforcement
  learning**. Nature. (이 프로젝트 문서에는 아직 직접 인용된 적 없음 — 투고 시 추가)

## 5. RL 기반 트레이딩의 재현성/과최적화 비판 문헌 (2026-07-29 웹 검색으로 확인)

이 프로젝트의 §14~16(test-set 하이퍼파라미터 선택 편향, valid/test 성적 낙차로 과적합 진단,
`crypto_beta_robustness_colab.ipynb`의 다중 시드 분산)이 정확히 이 문제의식과 겹친다. "우리만
이 문제를 겪은 게 아니라 이 분야의 알려진 함정"이라는 프레이밍의 핵심 근거들:

### ✅ 5.1 크립토 DRL 트레이딩의 backtest overfitting — 가장 직접적으로 겹치는 선행 연구
Gort, B. J. D., Liu, X.-Y., Sun, X., Gao, J., Chen, S., & Wang, C. D. (2022). **Deep Reinforcement
Learning for Cryptocurrency Trading: Practical Approach to Address Backtest Overfitting**.
arXiv:2209.05559. https://arxiv.org/abs/2209.05559

이 프로젝트와 도메인(크립토)·방법(DRL)이 동일하고, 문제의식(backtest overfitting)도 동일하다.
이들은 과최적화 탐지를 **가설검정 문제로 정식화**해 에이전트를 학습·평가하고, 과적합 확률을
추정해 과적합된 에이전트를 기각하는 절차를 제안한다 — 이 프로젝트의 §16(valid/test Sharpe 낙차로
정성적 진단)을 **정량적 가설검정으로 업그레이드할 근거**로 직접 인용 가능.

### ✅ 5.2 Probability of Backtest Overfitting (PBO) / Deflated Sharpe Ratio — 정량화 도구
- Bailey, D. H., Borwein, J., López de Prado, M., & Zhu, Q. J. (2016). **The Probability of Backtest
  Overfitting**. *Journal of Computational Finance*. (초판 SSRN 2014) https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
  — combinatorially symmetric cross-validation(CSCV)으로 PBO를 추정하는 방법론.
- Bailey, D. H., & López de Prado, M. (2014). **The Deflated Sharpe Ratio: Correcting for Selection
  Bias, Backtest Overfitting and Non-Normality**. *Journal of Portfolio Management*.
  https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf

**이 프로젝트에 직접 적용 가능성이 높음**: §14에서 발견한 "α를 test에서 골라서 생긴 선택 편향"과
§16/`crypto_beta_robustness_colab.ipynb`의 "시드 간 성적 분산"은 정확히 DSR/PBO가 정량화하려는
대상이다. 논문화 단계에서 지금의 정성적 진단("낙차가 크다/작다")을 **DSR·PBO 수치로 재계산**하면
훨씬 설득력 있는 통계적 근거가 된다 — `GAP_ANALYSIS.md` §1.3에 반영할 것.

### ✅ 5.3 계층적/앙상블 RL 일반 이론 (EarnHFT류 외) — 2026-08-05 웹 검색으로 확인

- Sutton, R. S., Precup, D., & Singh, S. (1999). **Between MDPs and Semi-MDPs: A Framework for
  Temporal Abstraction in Reinforcement Learning**. *Artificial Intelligence*, 112(1–2), 181–211.
  — 옵션(options) 프레임워크의 원 논문. 옵션 = 개시집합(initiation set) + 종료함수 + 옵션-내부
  정책의 3-튜플로, 옵션이 주어지면 MDP가 semi-MDP를 이룬다는 정식화.
- Dayan, P., & Hinton, G. E. (1993). **Feudal Reinforcement Learning**. *Advances in Neural
  Information Processing Systems 5* (NIPS 1992), 271–278. Morgan Kaufmann.
- Vezhnevets, A. S., Osindero, S., Schaul, T., Heess, N., Jaderberg, M., Silver, D., & Kavukcuoglu,
  K. (2017). **FeUdal Networks for Hierarchical Reinforcement Learning**. *Proceedings of the 34th
  International Conference on Machine Learning (ICML)*, PMLR 70. arXiv:1703.01161.
  — Dayan & Hinton의 feudal RL을 딥러닝으로 확장(Manager가 장기 서브골을 설정하고 Worker가 매
  스텝 원시행동을 선택하는 2단계 구조).
- Eysenbach, B., Gupta, A., Ibarz, J., & Levine, S. (2019). **Diversity is All You Need: Learning
  Skills without a Reward Function**. *International Conference on Learning Representations
  (ICLR)*. arXiv:1802.06070.
  — 스킬 인덱스 $z$와 그 결과 궤적 사이의 상호정보량을 보상항으로 목적함수에 직접 주입해 스킬들이
  서로 다르게 행동하도록 강제하는 비지도 스킬 발견(skill discovery) 방법. "다양성은 데이터
  분포만으로는 안 생기고 목적함수 수준에서 명시적으로 주입해야 한다"는 원리를 정식화한 대표 사례.

**이 프로젝트와의 관계**: EarnHFT의 3단계(Q-teacher 풀 학습 → 증류 → 라우터)는 옵션 프레임워크의
"고정된 서브정책 집합 + 그 사이를 전환하는 상위 정책"이라는 일반형의 한 구체적 사례로 읽을 수 있다.
다만 옵션 프레임워크·FeUdal 양쪽 모두 하위 정책(옵션/Worker)의 다양성이 보통 서로 다른 서브골이나
종료 조건에서 자연스럽게 발생하도록 설계되어 있는 반면, 이 프로젝트의 v1/v3 실패는 정확히 그
다양성 유발 메커니즘(EarnHFT의 경우 Q-teacher)이 없을 때 풀이 붕괴한다는 것을 보여준다 — 즉 본
논문의 실패 카탈로그는 일반적인 계층적 RL 이론이 "다양한 하위 정책"을 당연한 전제로 깔고 있는
지점을, 그 전제가 깨졌을 때 무슨 일이 일어나는지로 구체화해 보여주는 사례로 자리매김할 수 있다.
DIAYN의 상호정보량 목적함수는 이 "목적함수 수준 주입"이 EarnHFT에 국한된 특이 현상이 아니라
스킬/옵션 다양성 확보 전반에서 반복 확인된 원리임을 보여주는 독립적 사례이며, 4.3절에서 보고하는
$\lambda$-스윕(최소 형태의 목적함수 주입을 재현해 다양성이 예측된 방향으로 반응하는지 확인한 통제
실험)은 이 원리가 본 논문의 세팅에서도 성립함을 직접 검증한다.

### ✅ 5.4 포트폴리오 최적화용 희소선택의 고전 이론 — 2026-08-05 웹 검색으로 확인

- Markowitz, H. (1952). **Portfolio Selection**. *Journal of Finance* — 이미 §2.3에서 인용.
  카디널리티 제약(cardinality constraint, 보유 종목 수 상한)은 이 고전 평균-분산 프레임 위에
  얹는 확장으로 프레이밍된다.
- Chang, T.-J., Meade, N., Beasley, J. E., & Sharaiha, Y. M. (2000). **Heuristics for Cardinality
  Constrained Portfolio Optimisation**. *Computers & Operations Research*, 27, 1271–1302.
  — 카디널리티 제약(보유 종목 수 상한) + 종목별 비중 상하한을 표준 평균-분산 모델에 추가한
  최초기 정식화 중 하나. 유전 알고리즘·타부서치·시뮬레이티드 어닐링 기반 휴리스틱 3종 제안.
- Bertsimas, D., & Shioda, R. (2009). **Algorithm for Cardinality-Constrained Quadratic
  Optimization**. *Computational Optimization and Applications*, 43, 1–22.
  — 카디널리티 제약 이차계획법에 대한 분지한정(branch-and-bound) 정확해 알고리즘.

**이 프로젝트와의 관계**: FreQuant의 top-$K$ 신뢰도 선택(2.2절)은 학습된 신경망 확신도 점수로
카디널리티 제약을 근사한다는 점에서, 위 고전 문헌이 조합최적화로 정확히 풀던 "$N$개 자산 중 최대
$K$개만 보유"라는 동일한 제약을 미분 가능한 형태로 완화(relax)한 것으로 볼 수 있다. 이 연결고리는
4.4절의 구조적 설계가 임의의 딥러닝 트릭이 아니라 카디널리티 제약 포트폴리오 최적화라는 확립된
문제 부류에 대한 신경망 기반 근사임을 명시하는 데 쓸 수 있다. 다만 §17-A(2026-08-05)의 스피어만
IC 진단은 이 학습된 근사가 실제로는 자산의 미래 수익률 순위를 거의 예측하지 못한다는 것을 보여줘
(평균 IC ≈ 0), "고전 카디널리티 제약 최적화는 참 신호를 활용해 종목을 고르는 것을 전제하지만, 이
신경망 근사는 그 전제를 충족하지 못할 수 있다"는 흥미로운 대조점을 만든다 — 8장 한계 논의에
활용 가치가 있다.

### 5.5 최근(2020년대) 딥러닝 포트폴리오 관리 베이스라인 — LSRE-CAAN 구현·실행 완료(2026-08-06)

지금 6.6절의 유일한 딥러닝 베이스라인인 EIIE(Jiang et al., 2017)는 이미 거의 10년 전 아키텍처다.
톱티어 심사자가 "왜 더 최근 것과 비교 안 했나"라고 물을 가능성에 대비해 후보를 조사·구현했다:

- Li, J., Zhang, Y., Yang, X., & Chen, L. (2023). **Online Portfolio Management via Deep
  Reinforcement Learning with High-Frequency Data**. *Information Processing & Management*, 60(3),
  103247. — "LSRE-CAAN": long sequence representations extractor + cross-asset attention network,
  direct policy gradient. 공식 구현 공개됨: https://github.com/jiahaoli57/LSRE-CAAN — 재현
  난이도가 상대적으로 낮은 편(코드·논문 모두 공개, 우리 세팅처럼 고빈도 데이터 대상).
- 그 외 다수의 2024–2025 트랜스포머 기반 포트폴리오 RL(MIGT, MILLION 등)이 검색에서 발견됐으나
  서지정보만 확인했을 뿐 구조·재현성은 검토하지 않음 — 인용은 가능하나 베이스라인 구현 후보로는
  LSRE-CAAN이 코드 공개 여부상 가장 현실적.

**결과(2026-08-06, `crypto_lsre_caan_baseline_colab.ipynb` 실행 완료)**: LSRE-CAAN test Sharpe
0.332(이 노트북이 재계산한 등가중 0.330과 사실상 동일) — EIIE·v3에 이어 **세 번째로 다른
아키텍처에서 재현된 균등가중 수렴**. β=-30(배포) Sharpe 1.156으로 약 3.5배 압도. "2017년 방법과만
비교했다"는 지적을 방어하는 데 더해, 다양성 붕괴가 아키텍처 일반의 속성이라는 6.6절 주장을 한층
강화하는 세 번째 독립 증거를 확보. 상세: `paper/GAP_ANALYSIS.md` §2.4, `paper/FINDINGS_LOG.md`
§19. **아직 6.6절 본문에는 미반영** — 다음 작업.

---

## 6. Action Policy Smoothing 대조 문헌 — CAPS (2026-08-17 웹 검색으로 확인)

### ✅ CAPS — 훈련시점 정규화의 대조 사례(채택 아님, 반례로 인용)
Mysore, S., Mabsout, B., Mancuso, R., & Saenko, K. (2021). **Regularizing Action Policies for
Smooth Control with Reinforcement Learning**. *2021 IEEE International Conference on Robotics and
Automation (ICRA)*. arXiv:2012.06644. https://arxiv.org/abs/2012.06644
(프로젝트 페이지: http://ai.bu.edu/caps/)

CAPS("Conditioning for Action Policy Smoothness")는 로봇 제어(쿼드로터 등) RL 정책의 행동을
매끄럽게 만들기 위해 두 개의 정규화 항 — (i) 시간적 평활도(temporal smoothness): 연속된 스텝의
행동이 서로 비슷해야 한다, (ii) 공간적 평활도(spatial smoothness): 비슷한 상태는 비슷한 행동으로
매핑돼야 한다 — 을 **정책 손실함수에 직접 추가**해 학습 시점에 매끄러움을 유도한다. 실제
쿼드로터에서 전력소비를 약 80% 줄이면서도 비행 가능한 컨트롤러를 유지했다고 보고한다.

**이 프로젝트와의 관계 — 채택이 아니라 대조**: 이 논문의 채택 문헌(FreQuant, DeepClair)과 달리
CAPS의 메커니즘을 이식하지는 않았다. 오히려 4.2절의 두 번째 실험(`SmoothStepMixin`, 학습 환경
자체에 지수 블렌딩을 내장하는 것)이 구조적으로 CAPS의 시간적 평활도 항과 사실상 동일한 발상 —
"정책이 매끄럽게 행동하도록 훈련 시점에 직접 유도한다" — 을 44자산 연속 포트폴리오 세팅에서
독립적으로 재발견한 것이었다. CAPS가 로봇 제어에서 보고하는 결과와 정반대로, 이 프로젝트의 동일한
접근은 신용 할당 붕괴를 통해 비용 전 알파를 12.6%→0.92%로 파괴했다(4.2절, `paper/FINDINGS_LOG.md`
§2). 최종적으로 채택한 해법(스무딩은 추론 시점에만 적용하고 학습은 α=1 전권으로 진행)은 CAPS와
정확히 반대 지점에 있다 — "매끄러움을 훈련 목적함수에 주입"하는 대신 "훈련은 그대로 두고 매끄러움은
배포 시점 후처리로만 적용"한다. **이 대조는 단순한 관련 연구 인용이 아니라, CAPS류 훈련시점 평활
정규화가 조밀하고 지속적인 보상을 받는 로봇 제어에서는 성공하지만 거래비용이라는 희소하고 지연된
페널티가 지배하는 다자산 포트폴리오 RL에서는 왜 실패할 수 있는지에 대한 직접적인 반례로 4.2절에
명시할 가치가 있다**(두 세팅의 보상 밀도 차이가 원인일 수 있다는 가설은 미검증으로 남겨둔다).

---

## 다음 액션

1. ✅ ~~FreQuant·DeepClair·EarnHFT·RL 트레이딩 재현성 비판 문헌 검색~~ — 2026-07-29 웹 검색으로
   완료(§1, §5.1, §5.2). EarnHFT는 1저자(Qin, M.)만 검색 결과로 확정 확인됨 — 공저자 6명 전부
   정확한지는 arXiv 페이지에서 재확인 권장.
2. ✅ ~~§5.3(계층적/앙상블 RL 일반 이론), §5.4(희소 포트폴리오 선택 고전 이론) 검색~~ — 2026-08-05
   완료.
3. ✅ DSR은 §1.4/6.2에서 이미 시드 스윕에 적용 완료. **valid/test 격차 진단의 정식 가설검정
   formalize(Gort et al. 2022, §5.1 직접 적용)도 실행 완료(2026-08-06)** —
   `crypto_hrl_earnhft_colab.ipynb` §19(블록 순열검정 + 블록부트스트랩 CI, 4개 β 전문가에 적용).
   결과: β=30이 4개 중 p-value 가장 작음(0.282, 나머지 0.88~0.95)이나 관습적 유의수준(0.05)엔
   못 미침 — DSR(§5.2)과 동일 패턴("방향은 맞지만 공식 유의성 미달"). 상세는 `GAP_ANALYSIS.md`
   §1.5, `FINDINGS_LOG.md` §18.
4. ✅ §5.5의 LSRE-CAAN 베이스라인 실행 완료(2026-08-06) —
   `crypto/notebooks/crypto_lsre_caan_baseline_colab.ipynb`. 결과: test Sharpe 0.332(등가중
   0.330과 사실상 동일) — EIIE·v3에 이어 세 번째로 재현된 균등가중 수렴. 상세:
   `GAP_ANALYSIS.md` §2.4, `FINDINGS_LOG.md` §19.
5. ✅ §6(CAPS, action smoothing 대조 문헌) 검색·확인 완료(2026-08-17) — 외부 검토에서 4.2절의
   추론시점 스무딩 발견이 기존 action-smoothing 문헌(CAPS)과 어떻게 다른지 명시되지 않았다는
   지적을 받아 추가. `DRAFT.md`/`DRAFT_KR.md` §2.2·§4.2에 반영 완료.
6. ⬜ 서지정보 확정되는 대로 `paper/`에 `references.bib` 추가.
7. ✅ 다자산 HRL 선행연구 지형(HRPM, IJCNN'22, MetaTrader, MDPI HRP/HERC, MacroHFT, HARLF) 검색·
   확인 완료(2026-08-26) — §1(위 신규 절) 및 `DRAFT.md`/`DRAFT_KR.md` §2.1 모두 반영 완료.
   외부 검토에서 "다자산 포트폴리오에 계층 구조를 적용한 시도 자체가 전혀 없다"는 절대적 표현이
   과잉주장이라는 지적을 받아, §1.4 기여 주장을 "EarnHFT 3단계 구조를 Q-teacher 없이 연속
   다자산으로 이식할 때의 실패 캐스케이드 + 검증/테스트 일관성 진단"으로 좁히는 근거로 사용.
