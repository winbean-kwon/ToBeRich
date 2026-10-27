# 다음 연구 방향 검토 (독립·비판적 리뷰, 2026-10-27)

> 역할: 회의적인 저널 심사위원 겸 지도교수 관점. 부풀리지 않는다.
> 표기: **[검증]** = 이번 검토에서 원문/코드를 직접 확인, **[미검증]** = 확인 못 함 또는 추정, **[반박됨]** = 확인해 보니 사실과 다름.

---

## 0. 먼저: 이번 검토에서 새로 확인된 사실 (방향 판단에 결정적)

| 주장 | 상태 | 근거 |
|---|---|---|
| FinRL `StockPortfolioEnv`는 `transaction_cost_pct`를 저장만 하고 `step()`에서 쓰지 않음 | **[검증]** (커밋 7e98df4, 89행에서 저장, 184–189행 수익 계산에 비용 항 없음) | [env_portfolio.py @7e98df4](https://github.com/AI4Finance-Foundation/FinRL/blob/7e98df4/finrl/meta/env_portfolio_allocation/env_portfolio.py) |
| 그런데 FinRL 공식 문서는 이 예제에서 비용이 없다고 **명시**함: "We also assume no transaction cost, because we are trying to make a simple portfolio allocation case as a starting point." | **[검증]** | [FinRL docs – Portfolio Allocation](https://finrl.readthedocs.io/en/latest/tutorial/Introduction/PortfolioAllocation.html) |
| 그러면서도 공식 튜토리얼 코드는 `"transaction_cost_pct": 0.001`을 넘김 (적용은 안 됨) | **[검증]** (115행) | [FinRL-Tutorials 1-Introduction/FinRL_PortfolioAllocation_NeurIPS_2020.py](https://github.com/AI4Finance-Foundation/FinRL-Tutorials/blob/master/1-Introduction/FinRL_PortfolioAllocation_NeurIPS_2020.py) |
| 설명 가능 DRL 튜토리얼(Guan & Liu ICAIF'21 대응)은 `transaction_cost_pct: 0`을 명시 | **[검증]** (329행) | [FinRL-Tutorials 2-Advance/FinRL_PortfolioAllocation_Explainable_DRL.py](https://github.com/AI4Finance-Foundation/FinRL-Tutorials/blob/master/2-Advance/FinRL_PortfolioAllocation_Explainable_DRL.py) |
| FinRL GitHub 이슈 트래커에 "포트폴리오 env가 비용을 무시한다"는 보고는 **없음** (검색어: transaction_cost_pct, transaction cost, portfolio commission 등). PR #68 "Solve transaction_cost_pct issue"는 단일 종목 트레이딩 노트북 관련. | **[검증]** (GitHub 검색 API, 2026-10-27) | [PR #68](https://github.com/AI4Finance-Foundation/FinRL/pull/68), [Issue #896](https://github.com/AI4Finance-Foundation/FinRL/issues/896) |
| 다만 개인 포크(RL-pricing)가 2026-10 PR에서 "Portfolio environment charges transaction costs"로 고치고, 시작 상태를 현금으로 바꿔 첫 매수 비용을 물게 함 — 즉 **같은 두 현상(비용 누락·시작 상태)을 이미 손본 공개 기록이 존재**(논문은 아님) | **[검증]** | [RL-pricing PR #65](https://github.com/BichengWang/RL-pricing/pull/65), [PR #72](https://github.com/BichengWang/RL-pricing/pull/72) |
| EarnMore(The Web Conference 2024): config 전부 `transaction_cost_pct = 1e-3`, env는 저장만 하고 `step()`에서 미사용 | **[검증]** (커밋 810ff59, `pm/environment/pm_based_portfolio_value.py` 34행 저장, 151–171행 보상에 비용 없음; 학회명은 README의 bibtex) | [DVampire/EarnMore](https://github.com/DVampire/EarnMore) |
| EarnMore 논문 본문은 비용률을 **언급하지 않음** (0.1%를 썼다고 주장하지도 않음) | **[검증]** (HTML 본문 검색) | [arXiv 2311.10801v3](https://arxiv.org/html/2311.10801v3) |
| PRUDEX-Compass AlphaMix+ PM env: `transaction_cost_pct` 0.001을 config로 받아 저장만, 미사용. FinRL `env_portfolio.py`를 그대로 포함(vendored) | **[검증]** (커밋 2b62831, `AlphaMix+/PM/rl_env/portfolio_management.py` 26행만 참조) | [TradeMaster-NTU/PRUDEX-Compass](https://github.com/TradeMaster-NTU/PRUDEX-Compass) |
| PRUDEX-Compass 논문(TMLR 2023)도 비용률을 명시하지 않고, 보상은 비용 항 없는 계좌 손익 | **[검증]** (본문 앞 10만 자 검색; 나머지 2만 자 미확인) | [arXiv 2302.00586](https://ar5iv.labs.arxiv.org/html/2302.00586), [TMLR 2023 목록](https://mlanthology.org/tmlr/2023/sun2023tmlr-prudexcompass) |
| "TradeMaster는 수수료를 한 스텝 늦게 부과한다" | **[반박됨]** (커밋 1747cc1의 `portfolio_management/environment.py` 등 5개 env 모두: `weights_memory`에 [새 목표, 드리프트 후 가중치]를 순서대로 넣고 `[-3]`(직전 드리프트 가중치)과 `[-2]`(새 목표)의 차이로 수수료 계산 → **같은 스텝, 올바른 시점**) | [TradeMaster environment.py](https://github.com/TradeMaster-NTU/TradeMaster/blob/main/trademaster/environments/portfolio_management/environment.py) |

**시사점:** 이전 조사 에이전트의 3개 주장 중 2개(EarnMore, PRUDEX)는 맞고 1개(TradeMaster)는 틀렸다. 그리고 가장 중요한 것은: **FinRL 건은 "조용한 버그"가 아니라 문서에 적힌 가정**이라는 점이다. 문제는 "비용 인자를 받는데 무시하는 오해 소지가 있는 API"이지, 숨은 버그가 아니다. 논문에서 "silently ignore"라고 쓰면 첫 심사위원이 문서 한 줄로 반박한다.

---

## D1. 시작 상태 공식의 사전 예측 검증 (관성 정책, 새 시장)

### (1) 선행 연구
- 실무 백테스트 도구는 이미 웜 스타트를 권장한다. MathWorks: "To start, set the initial weights of the strategy to avoid starting all in cash." / 역분산 전략이 현금으로 시작해 약 2.5개월간 머무는 예를 보여 줌. **[검증]** [MathWorks runBacktest](https://www.mathworks.com/help/finance/backtestengine.runbacktest.html), [MathWorks Backtest Investment Strategies](https://www.mathworks.com/help/finance/backtest-investment-strategies.html)
- RL 포트폴리오 쪽에서 시작 상태 편향을 정량화하고 닫힌 형태로 예측한 논문은 찾지 못함 **[검증: 검색 범위 내 부재]**. Sood et al.(J.P. Morgan)은 DRL과 MVO 모두 전액 현금에서 시작하고, MVO는 시작 전 60일 데이터를 웜업으로 쓴다(웜업이 "데이터 창"에만 있고 "보유 상태"에는 없음). [arXiv 2602.17098](https://arxiv.org/html/2602.17098)
- 공식 자체는 1차 지수 필터(EMA)의 과도 응답(transient)이다. w_t − w̄_t 의 편차가 (1−α)^k로 감쇠한다는 건 신호처리 교과서 내용이다. **신규성은 "공식"이 아니라 "이 분야가 이걸 안 챙긴다는 측정"에 있다.**

### (2) 영향받는 논문 수
- 본인 조사 기준 명시적 관성 메커니즘 6/56편 **[미검증: 본인 조사, 독립 재확인 안 됨]**. 0/56이 웜업을 쓰지 않는다는 것도 본인 조사.
- 그 6편 중 공개 코드가 있고 **결과가 실제로 바뀌는지** 확인된 것은 0편. 즉 "영향받는 논문"은 현재 **잠재적 6편, 확인 0편**.

### (3) 심사위원의 가장 강한 반론
1. "EMA 과도 응답이다. α=0.01이면 시간상수 100스텝(30분봉 기준 약 2일), 반감기 약 69스텝. 4주 평가에서 첫 2일이 다르게 보유된다는 것 외에 무엇을 새로 말하나?" — **가장 치명적.** 답하려면 "그래서 어떤 출판된 비교 결론이 뒤집히는가"를 보여야 함.
2. "효과의 부호가 무작위(34창 중 41% 양수)다. 평균이 ~0이면 편향(bias)이 아니라 분산(variance)이다. 여러 창 평균을 내는 논문에는 영향이 작다." — 실제로 평균 효과가 0 근처면 '편향'이라는 단어부터 틀렸다. 창 1개짜리 평가(대부분 논문)의 **분산 증가**로 재프레이밍해야 함.
3. "닫힌 형태 r=0.98은 사후 적합(post-hoc), 정책 계열 하나." — D1이 바로 이걸 해결하려는 것이므로 사전 등록이 있으면 방어 가능.
4. "학습 관성은 비용이 있어도 안 생겼다(EIIE α_eff≈1). 그러면 이 문제는 인위적 스무딩을 넣은 소수 논문에만 해당." — 사실이며, 범위가 좁다는 걸 인정해야 함.
5. "새 시장에 EIIE + 출력 스무딩을 직접 붙인 건 연구자가 만든 정책이지 출판된 정책이 아니다." — 외적 타당도 약함.

### (4) 실행 가능성 (학부생 1인, Colab CPU, 2–4주)
- 높음. 이미 EIIE 브라질·다우30 파이프라인이 있고(커밋 630b401·4884adc), α 그리드는 평가만 다시 돌리면 됨. 1–2주.
- 단, 사전 예측(공식 값)을 평가 전 커밋하는 절차는 이미 갖춰져 있음.

### (5) 현실적 게재 수준
- 단독으로는 **워크숍 짧은 논문 또는 arXiv 노트** 수준. 예: ICAIF 워크숍, NeurIPS/ICML의 금융·재현성 워크숍 포스터, 국내 학회(KIISE/KCC 학부생 논문). ICAIF 본 트랙·저널은 반론 1·2 때문에 어려움.

### (6) 판정: **단독으로는 하지 말 것. 다른 방향의 한 절(section)로만.**
- 조건부 예외: 6편 중 **공개 코드가 있는 출판 논문 1편 이상**에서 웜업 유무로 그 논문의 비교 결론(순위)이 바뀌는 것을 보일 수 있으면 단독 짧은 논문 가치가 생김. 그 확인 없이 "새 시장 + 우리가 만든 스무딩 EIIE"는 공식이 맞다는 것만 재확인할 뿐이다.

---

## D2. 비용 누락 감사 (공개 RL 포트폴리오 환경)

### (1) 선행 연구
- **비용 누락 일반론은 이미 잘 알려짐.** 2019년 체계적 리뷰는 검토한 RL 트레이딩 논문 모두가 비용·유동성·호가 스프레드 중 하나 이상을 비현실적으로 가정했다고 보고 [Data 4(3):110, DOI](https://api.crossref.org/works/10.3390%2FDATA4030110) / [IDEAS](https://ideas.repec.org/a/gam/jdataj/v4y2019i3p110-d252469.html) (저자명 미확인 **[미검증]**). 2024 리뷰도 대부분 슬리피지 0 가정을 지적 [arXiv 2411.12746](https://arxiv.org/pdf/2411.12746) (검색 요약 기준 **[부분 검증]**). 2022 서베이 [arXiv 2212.06064](https://arxiv.org/pdf/2212.06064).
- **"엔진 간 비용 구현 차이"를 정량화한 매우 가까운 선행연구가 2026년에 나옴:** Yin et al., "Implementation Risk in Portfolio Backtesting" — 5개 오픈소스 백테스트 엔진에서 비용 0이면 완전 일치, 비용>0이면 최대 3.71%p 차이, 3개 엔진에서 미보고 결함 7개 발견. 단, RL 환경은 다루지 않음. **[검증: 초록]** [arXiv 2603.20319](https://arxiv.org/abs/2603.20319)
- Abbade & Costa(2026): 대부분의 오픈소스 백테스트 환경이 비용을 무시하거나 고정 비용만 가정한다고 지적, FinRL-Meta 확장으로 시장충격 모형 env 제시, 비용 모형이 DRL 알고리즘 순위를 바꾼다고 보고. 기존 env의 코드 감사는 아님. **[검증: 초록]** [arXiv 2603.29086](https://arxiv.org/abs/2603.29086)
- **특정 프레임워크(FinRL StockPortfolioEnv, EarnMore, PRUDEX AlphaMix+)가 설정한 비용을 무시한다는 공개 보고는 찾지 못함** (FinRL 이슈 트래커 검색, 웹 검색). 개인 포크 수정 기록만 있음([RL-pricing PR #65](https://github.com/BichengWang/RL-pricing/pull/65)). → **구체적 코드 사실은 신규**.

### (2) 실제 영향받는 논문 (확인된 것만)
| 논문 | 사용 환경 | 비용 처리 | 논문 서술 | 판정 |
|---|---|---|---|---|
| FinRL (Liu et al., ICAIF 2021) 포트폴리오 배분 사용 사례: A2C 샤프 2.36 / 연 42.57% 등 | StockPortfolioEnv로 **추정** **[미검증]** | 튜토리얼은 0.001 전달, env는 무시 | 포트폴리오 사례에 비용률 언급 없음; 암호화폐 사례에만 "with transaction cost" 명시 | **아마 영향** (코드-결과 대응은 미확인) [ar5iv 2111.09395](https://ar5iv.labs.arxiv.org/html/2111.09395) |
| Guan & Liu, "Explainable DRL for Portfolio Management" (ICAIF 2021): PPO 샤프 2.11 vs DJIA 2.0 | FinRL 사용("We use the FinRL library") | 튜토리얼에서 **0으로 명시** | 유도식에서 "Ignoring the transaction cost" | 비용 0 결과이지만 **은폐는 아님** [ar5iv 2111.03995](https://ar5iv.arxiv.org/html/2111.03995) |
| EarnMore (Zhang et al., The Web Conference 2024): "14개 베이스라인 대비 수익 40% 이상 개선" | 자체 env | config 0.001, **미적용** [검증] | 비용률 언급 없음 | **영향 있음(무비용 결과)**, 단 "0.1% 적용"이라 주장한 적은 없음 |
| PRUDEX-Compass / AlphaMix+ (Sun et al., TMLR 2023) | 자체 env + FinRL env 포함 | config 0.001, **미적용** [검증] | 비용률 언급 없음 | **영향 있음(무비용 결과)**, 위와 같음 |
| Wong & Liu (Eng OA 2025) 멀티모달 PPO, 0.1% 비용 | FinRL **주식 트레이딩 env**(주식 수 단위, hmax) | 이 env는 비용 적용함 | 0.1% 명시 | **영향 없음** (반례) [PDF](https://www.opastpublishers.com/open-access-articles/portfolio-optimization-through-a-multimodal-deep-reinforcement-learning-framework.pdf) |
| Sood et al. (J.P. Morgan) | 자체 env | 비용 0을 명시 | 명시 | 해당 없음 [arXiv 2602.17098](https://arxiv.org/html/2602.17098) |

**정직한 집계:** "설정은 비용을 주는데 실제로는 0" 상태로 결과를 낸 것이 확인된 출판 논문 **2편(EarnMore, PRUDEX/AlphaMix+)**, 가능성 높은 1편(FinRL ICAIF'21), 나머지는 미확인. 그리고 **이 2편도 비용을 적용했다고 주장하지 않았다** → 엄밀히는 "허위 보고"가 아니라 "비용 미보고 + 코드 설정이 오해를 부름". 이 구분을 논문에서 흐리면 저자 측 반박에 무너진다.

OpenAlex에서 "FinRL portfolio allocation" 검색 결과 228건 [OpenAlex 쿼리](https://api.openalex.org/works?search=FinRL%20portfolio%20allocation) — 이 중 StockPortfolioEnv 사용 논문을 세는 작업은 하지 못했음 **[미검증]**. 저인용 학부/석사 논문·저널에 다수 있을 가능성이 높지만 지금은 추정일 뿐.

### (3) 심사위원의 가장 강한 반론
1. "FinRL은 문서에 비용 없음이라고 썼다. 버그 아님." — 맞다. 'API 오해 소지'로만 주장 가능.
2. "EarnMore·PRUDEX는 비용을 적용했다고 말한 적 없다. 무비용 결과임은 잘 알려진 일반적 한계(2019 리뷰 이후)." — 기여가 "또 한 번의 확인"으로 축소될 위험.
3. "비용을 켜면 성능이 떨어진다는 건 자명. 무엇이 새로운가?" — **답은 '순위 역전'이어야 한다.** 비용을 넣었을 때 제안 기법이 베이스라인(특히 동일가중·buy-and-hold)보다 못해지는지, 그리고 비용을 넣고 **재학습**했을 때 회복되는지. 평가 시에만 비용을 붙이면 "훈련 조건과 다르니 불공정"이라는 반론이 즉시 나옴.
4. "2편으로는 '감사(audit)'라 부르기 빈약하다." — 최소 5–10개 공개 프레임워크/논문 코드를 같은 체크리스트로 훑어야 '감사'.
5. Yin et al. 2026과의 차별점 요구 — "RL 환경은 보상이 비용에 의존하므로 비용 누락이 평가뿐 아니라 **학습된 정책 자체**를 바꾼다"는 점이 유일한 강한 차별점. 이걸 실험으로 보여야 함.

### (4) 실행 가능성
- 정적 코드 감사(5–10개 저장소): 1주, CPU 불필요. 높음.
- 영향 정량화:
  - 평가 시 비용만 사후 적용(공개 체크포인트나 재현 정책으로 회전율 × 비용률): 매우 싸다. 하루 회전율만 기록하면 됨.
  - 비용 켜고 재학습: EarnMore는 마스크 트랜스포머+SAC, 다수 종목 풀 → Colab CPU로 4주 안에 원 논문 규모 재현은 **불확실**(데이터 준비·학습 시간 미확인 **[미검증]**). PRUDEX AlphaMix+는 앙상블이라 역시 무거울 가능성. FinRL 튜토리얼은 가볍다(이미 경험 있음).
  - 현실적 범위: FinRL 튜토리얼(재학습 포함, 시드 다수) + EarnMore/PRUDEX 중 1개(평가 시 비용 적용 + 축소판 재학습).
- 저자/유지관리자에게 이슈 먼저 보고(책임 있는 공개). FinRL에는 1줄짜리 PR(비용 적용 또는 인자 제거/경고)이 가능 — 졸업 프로젝트 산출물로도 깔끔.

### (5) 현실적 게재 수준
- 워크숍(ICAIF 워크숍, NeurIPS/ICML 재현성·금융 워크숍), 또는 ML Reproducibility Challenge 류의 재현 보고서, arXiv 노트. 국내 학회 학부 논문은 충분.
- 순위 역전 + 재학습 결과까지 있으면 ICAIF 본 트랙 short/poster를 "시도"할 수 있으나 1인·4주로는 가능성 낮다고 봄.

### (6) 판정: **조건부로 추진 — 핵심 축으로 가장 낫다.**
조건: (a) "silent bug"가 아니라 "설정-구현 불일치·미보고"로 정확히 프레이밍, (b) 감사 대상을 최소 5–10개 저장소로 넓히고 각 판정에 커밋 해시·행 번호, (c) 최소 1개 출판 결과에서 **비용 적용(재학습 포함) 시 베이스라인 대비 순위가 바뀌는지**를 사전 등록 후 측정. (c)가 안 나오면(순위 불변) 그 자체로 "무해함" 결과로 보고하되 기대치를 낮출 것.

---

## D3. RL 포트폴리오 백테스트 평가 프로토콜 종합 감사

### (1) 선행 연구 — 이미 상당히 붐빔
- PRUDEX-Compass(TMLR 2023): "대부분 FinRL 기법이 수익 지표만 본다"며 6축 17개 지표 평가 체계 제안 [arXiv 2302.00586](https://arxiv.org/abs/2302.00586)
- Gort et al.(FinRL 팀): 백테스트 과적합 확률(PBO)로 과적합 에이전트 기각 [arXiv 2209.05559](https://arxiv.org/abs/2209.05559)
- Velay et al.(INISTA 2023): 대부분 DRL 포트폴리오 알고리즘이 강건하지 않음 [arXiv 2306.10950](https://arxiv.org/abs/2306.10950)
- 시드 민감도·다중 베이스라인 프로토콜 제안(2026 프리프린트) [Research Square rs-9824202](https://doi.org/10.21203/rs.3.rs-9824202/v1)
- 리뷰들: [2106.00123](https://arxiv.org/abs/2106.00123v1), [2212.06064](https://arxiv.org/pdf/2212.06064), [2411.12746](https://arxiv.org/pdf/2411.12746), [2512.10913](https://www.arxiv.org/pdf/2512.10913), 2019 Data 리뷰.
- 비전통 RL 쪽: Yin et al. 2026 엔진 구현 위험 [2603.20319](https://arxiv.org/abs/2603.20319); 시장충격 env [2603.29086](https://arxiv.org/abs/2603.29086).
→ "프로토콜이 엉망이다"라는 일반 주장은 신규성이 거의 없다. 새로울 수 있는 것은 **(i) 코드 수준 증거(커밋·행 번호), (ii) 지금까지 아무도 체크리스트에 넣지 않은 항목(평가 시작 상태/웜업), (iii) 정량적 영향**뿐.

### (2) 영향받는 논문 수
- 본인 56편 조사가 핵심 자산(웜업 0/56, 이전 가중치를 상태에 넣음 32/56, 명시 관성 6/56) **[미검증: 독립 재확인 필요 — 최소 무작위 10편을 다시 코딩해 일치율 보고]**.
- 코드 수준 확인은 위 D2 표 수준.

### (3) 가장 강한 반론
1. "체크리스트 논문은 많다. 차별점은?" — 위 (i)–(iii) 없이는 리젝.
2. "56편 조사의 코딩 기준·신뢰도(평가자 1명)?" — 2차 코딩/일치도 필요.
3. "항목을 많이 넣을수록 각 항목의 정량 증거가 얕아진다." — 4주 1인으로는 실제로 그렇게 됨.

### (4) 실행 가능성
- 전체 버전: 2–4주 1인으로는 **낮음**. 각 항목마다 재실행이 필요해지기 때문.
- 축소 버전(아래 권고안): 가능.

### (5) 게재 수준
- 축소·정밀 버전이면 워크숍~ICAIF 포스터 시도 가능. 넓고 얕은 버전은 arXiv 노트 이상 어려움.

### (6) 판정: **넓은 버전은 하지 말 것.** D2를 축으로 하고 D1을 한 항목으로 넣은 "좁고 깊은" 버전만.

---

## 종합 권고

**권고안 (D2 중심 + D1 한 절 = 좁은 D3):**
가제: "Configured but not charged: a code-level audit of evaluation conditions in open-source RL portfolio environments" (비용 설정–구현 불일치 + 시작 상태).

1. **1주차 — 정적 감사:** FinRL(StockPortfolioEnv, PortfolioOptimizationEnv), FinRL-Meta, TradeMaster(5개 PM env), PRUDEX-Compass, EarnMore, 그 외 공개 RL 포트폴리오 코드 5개 이상(56편 조사에서 코드 공개된 것). 각 저장소마다 항목 3개만: ① 설정 비용이 `step()`에 실제 반영되는가 ② 반영 시점(같은 스텝/지연) ③ 평가 시작 보유 상태(현금/동일가중/웜업). 커밋 해시·행 번호 표. **TradeMaster 사례처럼 "정상"도 그대로 보고** — 오탐을 줄였다는 게 신뢰도.
2. **사전 등록 후 2–3주차 — 정량:** (a) FinRL 튜토리얼: 비용 0 vs 0.1% 적용 평가, 그리고 0.1%로 재학습(시드 ≥5), 동일가중·buy-and-hold 대비 순위. (b) EarnMore 또는 PRUDEX 중 하나: 최소한 공개 설정 재현 후 평가 시 비용 적용, 가능하면 축소 재학습. (c) 시작 상태: 명시 관성 정책 1개(가능하면 6편 중 공개 코드)에서 웜업 유무로 순위가 바뀌는지.
3. **책임 있는 공개:** FinRL·EarnMore·PRUDEX에 이슈 제기(가능하면 FinRL에 PR). 졸업 산출물로도 명확.
4. **보고 원칙:** "silent bug" 대신 "설정–구현 불일치/미보고". 순위 불변이면 그대로 보고.

**현실적 기대치:** 워크숍 1편 또는 arXiv 노트 + 오픈소스 이슈/PR. 저널·본 트랙은 이번 범위에서 기대하지 말 것. 졸업 논문으로는 "원래 목표 실패 → 왜 비교가 신뢰하기 어려운지를 코드 수준에서 보였다"라는 서사가 충분히 성립한다.

**하지 말 것:** D1 단독(공식이 EMA 과도응답이라는 반론에 약하고, 평균 효과가 0 근처라 '편향'이라는 이름부터 흔들림), D3 넓은 버전(붐비는 분야, 1인 4주로 깊이 부족).

**목록에 없는 대안 검토:** "평가 창 1개짜리 논문의 결론이 시작일·시드만 바꿔도 뒤집히는 비율" 같은 분산 중심 재분석도 생각해 봤으나, 시드 민감도(Research Square 2026, Velay 2023)와 PBO(Gort 2022)가 이미 다룸 → 권하지 않음. 위 권고안이 더 낫다.

---

## 확인하지 못한 것 (후속 작업 전 반드시 확인)
- FinRL ICAIF'21 포트폴리오 결과가 실제로 StockPortfolioEnv + 0.001 설정으로 나왔는지.
- StockPortfolioEnv를 쓰고 비용 0.1%를 **주장**한 출판 논문이 실제로 있는지(있으면 D2의 무게가 크게 올라감 — 가장 가치 있는 추가 검색).
- EarnMore·PRUDEX를 Colab CPU로 재학습하는 데 드는 시간.
- 56편 조사 수치(6/56, 32/56, 0/56)의 독립 재코딩.
- 2019 Data 리뷰의 저자명, 2411.12746 리뷰의 세부 수치.
