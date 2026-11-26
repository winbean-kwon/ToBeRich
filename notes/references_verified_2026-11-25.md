# 참고문헌 후보 — 서지 실존 대조 (G1, 2026-11-25, Claude)

> 범위: 영어 초안(`thesis/en/`)·목차(`thesis/OUTLINE_KR.md` 2장)·선행연구 노트(`notes/lit/repro_literature_verified.md`)·결과 노트에서 인용할 문헌 후보.
> 방법: arXiv API(`export.arxiv.org/api/query`), Crossref API(`api.crossref.org/works/{DOI}`, 서지 검색), 출판처 페이지 메타데이터(JMLR, NeurIPS proceedings).
> **확인한 것:** 제목·저자·연도·게재처가 실제와 같다. **확인하지 않은 것:** 인용하려는 내용이 본문에 있는가. 내용 확인은 표의 "내용" 열을 따르고, 대장 G1의 사용자 확인은 그대로 남는다.
> 표본 56편(G2)은 이 문서 범위가 아니다.

## 1. 대상 논문(재현·깔때기)
| 키 | 서지(대조 결과) | 식별자 | 비고 |
|---|---|---|---|
| Yang 2020 Ensemble | Yang, Liu, Zhong, Walid. Deep reinforcement learning for automated stock trading: An ensemble strategy. ICAIF 2020, 1–8 | 10.1145/3383455.3422540; SSRN 10.2139/ssrn.3690996 | Crossref 제목은 부제 생략형. SSRN판은 부록(문턱 120 대 140) 확인용 |
| Xu 2020 RAT | Xu, Zhang, Ye, Zhao, Tan(5인). Relation-Aware Transformer for Portfolio Policy Learning. IJCAI 2020, 4647–4653 | 10.24963/ijcai.2020/641 | |
| Liu 2021 FinRL | Liu, Yang, Gao, Wang. FinRL: Deep reinforcement learning framework to automate trading in quantitative finance. ICAIF 2021, 1–9 | 10.1145/3490354.3494366; arXiv 2111.09395 | T3 |
| Liu 2020 FinRL library | Liu et al.(7인). FinRL: A deep reinforcement learning library for automated stock trading in quantitative finance. NeurIPS 2020 Deep RL Workshop | arXiv 2011.09607 | 다른 논문이다. 혼동 주의 |
| Sun 2023 PRUDEX | Sun, Qin, Wang, An. PRUDEX-Compass: Towards systematic evaluation of RL in financial markets. TMLR 2023 | arXiv 2302.00586 | T2(AlphaMix+). TMLR 게재 정보는 arXiv에 없음 → OpenReview로 사용자 확인 |
| Kim 2025 DeepAries | Kim, Yi, Gim, Choi, Kang(5인). DeepAries: Adaptive rebalancing interval selection for enhanced portfolio selection. CIKM 2025, 5780–5787 | 10.1145/3746252.3761572; arXiv 2510.14985 | T1 |
| Chen 2026 MARS | Chen, Li, Wang. MARS: A meta-adaptive RL framework for risk-aware multi-agent portfolio management. AAAI 2026, 40(24):20092–20099(사전 등록 노트 기준) | arXiv 2508.01173 | 인용 연도는 2026으로 통일 |
| Gu 2023 Margin Trader | Gu, Du, Rahman, Wang. Margin Trader: A RL framework for portfolio management with margin and constraints. ICAIF 2023, 610–618 | 10.1145/3604237.3626906 | |
| Pretorius & van Zyl 2022 | Deep RL and convex mean-variance optimisation for portfolio management | arXiv 2203.11318 | 게재 여부 미확인 → arXiv로 인용 |
| Hu & Gu 2024 | Markowitz Meets Bellman: Knowledge-distilled RL for portfolio management | arXiv 2405.05449 | 게재처 정보 없음(arXiv·Crossref). "KDD"는 학회가 아니라 논문 Table 1의 방법 이름이다. 영어 초안 Y.3과 Table 3에서 학회처럼 읽히던 표기를 고쳤다 |
| Marzban 2021 WaveCorr | Marzban, Delage, Li 외(5인). WaveCorr: Correlation-savvy deep RL for portfolio management | arXiv 2109.07005 | |
| Jiang 2017 EIIE | Jiang, Xu, Liang. A deep RL framework for the financial portfolio management problem | arXiv 1706.10059 | |
| Xiong 2018 | Liu, Xiong, Zhong 외(5인). Practical deep RL approach for stock trading. NeurIPS 2018 workshop | arXiv 1811.07522 | 첫 저자 표기 Liu(arXiv) |
| Li 2019 | Li, Li, Zhan 외(4인). Optimistic bull or pessimistic bear | arXiv 1907.01503 | |
| Zhang 2020 PPN | Zhang, Zhao, Li, Wu 외(6인). Cost-sensitive portfolio selection via deep RL. IEEE TKDE | 10.1109/TKDE.2020.2979700 | Crossref는 조기 공개(2020)만 줌. 권호 34(1) 2022는 사용자 확인 |
| Zhang 2024 EarnMore | RL with maskable stock representation for portfolio management in customizable stock pools. WWW 2024 | arXiv 2311.10801 | WWW 쪽수 미확인 |
| Coriat & Benhamou 2025 HARLF | HARLF … | arXiv 2507.18560 | |
| Li 2024 | A deep RL framework for financial portfolio management(석사논문) | arXiv 2409.08426 | |

## 2. 관련 연구
| 키 | 서지(대조 결과) | 식별자 | 내용(인용 범위) |
|---|---|---|---|
| DeMiguel, Garlappi, Uppal 2009 | Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy? RFS 22(5):1915–1953 | 10.1093/rfs/hhm075 | 1/N 기준선 |
| Kruthof & Müller 2025 | Can deep reinforcement learning beat 1/N? Finance Research Letters 75:106866 | 10.1016/j.frl.2025.106866 | **주의:** 앞선 확인에서, 그들의 DRL은 거래가 많아 비용에 지는 사례였다. 우리 "정적·1/N 근방 정책" 관찰의 근거로 인용하면 안 된다. "DRL이 1/N을 못 이긴 선행"으로만 쓴다. 본문 미열람(유료) |
| Velay et al. 2023 | Benchmarking robustness of deep RL approaches to online portfolio management. INISTA 2023, 1–6 | 10.1109/INISTA59065.2023.10310402; arXiv 2306.10950 | |
| Lavko, Klein, Walther 2023 | Reinforcement learning and portfolio allocation: Challenging traditional allocation methods. SSRN WP | 10.2139/ssrn.4346043 | 목차의 "EFMA 2023"은 확인 못 함 → SSRN WP로 인용 |
| Pawar et al. 2024 | Portfolio management using deep RL | arXiv 2405.01604 | 입력과 무관한 거의 같은 가중치 보고(노트 기준) |
| Mohammadshafie et al. 2024 | Deep RL strategies in finance: Insights into asset holding, trading behavior, and purchase diversity | arXiv 2407.09557 | 반박 심사가 찾은 문헌. 보유·매수 다양성 관찰. 본문 대조 전에는 "관련 관찰"로만 쓴다 |
| Seyde et al. 2021 | Is bang-bang control all you need? Solving continuous control with Bernoulli policies. NeurIPS 34, 27209– | arXiv 2111.02552 | 연속 제어에서 경계 행동(포화) 정책이 흔하다는 선행 → DDPG 포화 서술 |
| Kritzman & Li 2010 | Skulls, financial turbulence, and risk management. FAJ 66(5):30–41 | 10.2469/faj.v66.n5.3 | 난류 지수 정의(수익률 기반 — 초록 기준) |
| Henderson et al. 2018 | Deep RL that matters. AAAI 32(1) | 10.1609/aaai.v32i1.11694 | |
| Gundersen & Kjensmo 2018 | State of the art: Reproducibility in AI. AAAI 32(1) | 10.1609/aaai.v32i1.11503 | |
| Collberg & Proebsting 2016 | Repeatability in computer systems research. CACM 59(3):62–69 | 10.1145/2812803 | 수치는 TR판에서만 확인(기존 노트) |
| Raff 2019 | A step toward quantifying independently reproducible ML research. NeurIPS 2019 | arXiv 1909.06674 | |
| Hou, Xue, Zhang 2020 | Replicating anomalies. RFS 33(5):2019–2133 | 10.1093/rfs/hhy131 | |
| Jensen, Kelly, Pedersen 2023 | Is there a replication crisis in finance? JF 78(5):2465–2518 | 10.1111/jofi.13249 | |
| Felizardo et al. 2022 | RL applied to trading systems: A survey | arXiv 2212.06064 | |
| Srikantha et al. 2026 | AI and ML for stock market prediction: A systematic literature review … (2016–2026). Research Square 프리프린트 | 10.21203/rs.3.rs-11084191/v1 | 동료심사 전 |
| Prata et al. 2024 | LOB-based deep learning models for stock price trend prediction: A benchmark study. AI Review 57(5) | 10.1007/s10462-024-10715-4 | |
| Liu et al. 2022 FinRL-Meta | FinRL-Meta: Market environments and benchmarks … NeurIPS 2022 D&B | arXiv 2211.03107 | |

## 3. 방법(알고리즘·통계·도구)
| 키 | 서지(대조 결과) | 식별자 |
|---|---|---|
| Schulman et al. 2017 PPO | Proximal policy optimization algorithms | arXiv 1707.06347 |
| Mnih et al. 2016 A2C/A3C | Asynchronous methods for deep RL. ICML 2016 | arXiv 1602.01783 |
| Lillicrap et al. 2016 DDPG | Continuous control with deep RL(ICLR 2016) | arXiv 1509.02971 |
| Fujimoto et al. 2018 TD3 | Addressing function approximation error in actor-critic methods. ICML 2018 | arXiv 1802.09477 |
| Raffin et al. 2021 SB3 | Stable-Baselines3: Reliable RL implementations. JMLR 22(268):1–8 | jmlr.org v22/20-1364 |
| Ledoit & Wolf 2008 | Robust performance hypothesis testing with the Sharpe ratio. JEF 15(5):850–859 | 10.1016/j.jempfin.2008.03.002 |
| Götze & Künsch 1996 | Second-order correctness of the blockwise bootstrap for stationary observations. Ann. Stat. 24(5):1914–1933 | 10.1214/aos/1069362303 |
| Künsch 1989 | The jackknife and the bootstrap for general stationary observations. Ann. Stat. 17(3):1217–1241 | 10.1214/aos/1176347265 |
| Politis & Romano 1994 | The stationary bootstrap. JASA 89(428):1303–1313 | 10.1080/01621459.1994.10476870 |
| Andrews 1991 | HAC covariance matrix estimation. Econometrica 59(3):817–858 | 10.2307/2938229 |
| Holm 1979 | A simple sequentially rejective multiple test procedure. Scand. J. Stat. 6(2):65–70 | JSTOR 4615733(Crossref에 DOI 없음, JSTOR 페이지 응답만 확인) |
| Welch 1947 | The generalization of 'Student's' problem … Biometrika 34(1–2):28–35 | 10.1093/biomet/34.1-2.28 |
| Wilson 1927 | Probable inference, the law of succession, and statistical inference. JASA 22(158):209–212 | 10.1080/01621459.1927.10502953 |
| Cohen 1960 | A coefficient of agreement for nominal scales. EPM 20(1):37–46 | 10.1177/001316446002000104 |

## 4. 확인 못 함(인용 보류)
- **Aarnio 2025(Turku 석사논문):** 노트에 URL이 없고 Crossref·Turku 저장소 검색에서 찾지 못했다. 사용자가 출처를 찾기 전에는 인용하지 않는다.
- **Buczyński et al. 2023(Eng. Proc. 39:79):** 기존 노트에서 본문 403. 이번에도 대조하지 않았다.
- **Lavko et al.의 EFMA 2023 발표:** SSRN WP만 확인했다.
- PRUDEX-Compass의 TMLR 게재 정보, PPN의 TKDE 권호, MARS의 AAAI 쪽수, EarnMore의 WWW 쪽수, Hu & Gu의 게재처.

## 5. 결과 요약
- 표의 50건은 모두 실재하고(Götze & Künsch 1996은 심사 지적으로 추가), 서지가 노트의 표기와 맞았다. 차이는 위 비고에 적었다(Lavko 게재처, Ensemble 제목의 부제, FinRL 두 논문의 구분).
- 실재를 확인하지 못한 것은 Aarnio 1건이다(Buczyński는 대조하지 않음).

## 6. 정정·추가 (2026-11-26, 2장 반박 심사)
- **Pawar et al. 2024(arXiv 2405.01604) 정정:** 본문 확인 결과 제안 모델은 DQN, 거래비용 없음 가정, FinRL·SB3 언급 없음. "DDPG·A2C가 입력과 무관하게 거의 같은 가중치"라는 서술은 본문에 없다. 이 서술을 담은 노트(`notes/finrl_t3_o2_result.md` 62행, `notes/one_over_n_structure.md` 47행, `notes/prereg_code_audit.md` 130행, `notes/finrl_t3_o6_result.md` 73행, `notes/plan_2026-10-30.md` 24행)는 이 정정으로 대체한다. 퇴화 근거로 인용하지 않는다.
- **Li 2024(2409.08426) 확인:** 6장 "a nearly uniform portfolio is kept in the whole back-testing process … Uniform Constant Rebalanced Portfolio", 결론에 주식시장에서 UCRP와 같아졌다는 문장. 인용 가능.
- **Seyde 2021, MARS, Mohammadshafie 2024:** 초록·본문 기준으로 2장 문장 수정(`thesis/en/related_work.md`).
- **추가 후보(서지 미대조):** André & Coqueret, Dirichlet policies for reinforced factor portfolios, arXiv 2011.05381(초록: RL 포트폴리오가 1/N에 매우 가까움). Aarnio 2025(Turku 저장소 https://www.utupub.fi/bitstreams/7d12624f-27e2-4448-99c9-2520ec3009f3/download — 4절 "확인 못 함" 해제 후보, 원문 확인 필요). arXiv 2603.29086(Realistic market impact modeling for RL trading environments). FinRL 이슈 #340·#968(포트폴리오 env 입력 변경 무영향 사용자 보고).
- **2026-11-26 확인(arXiv 메타데이터·초록):** André, Eric & Coqueret, Guillaume, "Dirichlet policies for reinforced factor portfolios", arXiv 2011.05381(2020-11-10) — 초록 "RL-based portfolios are very close to the equally-weighted (1/N) allocation". Abbade, Lucas Riera & Costa, Anna Helena Reali, "Realistic Market Impact Modeling for Reinforcement Learning Trading Environments", arXiv 2603.29086(2026-03-30) — 초록 "most open-source backtesting environments assume negligible or fixed transaction costs". Mohammadshafie et al. 2407.09557 본문 II-C "Our experimentation is conducted using the FinRL environment".
- **FinRL 이슈 본문 확인(GitHub API):** #340(2021-11-12, closed) StockPortfolioEnv에서 cov_list→return_list 교체 "barely had any impact", 다음 날 수익 누설 "no impact at all"(A2C). #968(2023-04-07, open) 기술지표 포함 여부 "little to no difference"(PPO·A2C).
- **Li 2024 코드:** 부록 C가 github.com/jackieli19/PGPortfolio(Stock 브랜치)를 구현으로 명시(`notes/lit/f1/f1_recheck_log.md`). EIIE 공개 코드(PGPortfolio)를 고친 판으로 재현 → "공식 코드에서 퇴화 관찰"은 우리만의 것이 아님. 2장·6.2 문장 수정.
