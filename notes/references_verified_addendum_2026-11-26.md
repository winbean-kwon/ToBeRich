# 참고문헌 추가분 — 서지 실존 대조 (2026-11-26, Claude)

> 범위: 영어 초안 3~5·8장 개정에서 새로 들어온 인용 29건(PPO·SB3는 `references_verified_2026-11-25.md`에서 확인됨 → 제외).
> 방법: arXiv API(`export.arxiv.org/api/query`), Crossref API(`api.crossref.org/works/{DOI}`, 서지 검색), 출판처 메타데이터(JMLR, NeurIPS proceedings, PMLR), 웹 검색(ICLR 가상 포스터·OpenReview 서지, RePEc 초록). OpenReview API·DBLP·ACM DL·ScienceDirect·Springer는 봇 차단으로 직접 조회 못 함.
> **확인한 것:** 제목·저자·연도·게재처가 실제와 같다. **확인하지 않은 것:** 별도 표기가 없으면 인용 내용. 1~3, 28번 내용은 끝의 "내용 메모"를 본다.

## 1. 금융 RL·포트폴리오
| 키 | 서지(대조 결과) | 식별자 | 비고 |
|---|---|---|---|
| Qin 2024 EarnHFT | Qin, Sun, Zhang, Xia, Wang, An(6인). EarnHFT: Efficient hierarchical reinforcement learning for high frequency trading. AAAI 2024, 38(13):14669–14676 | 10.1609/aaai.v38i13.29384; arXiv 2309.12891 | 일치 |
| Jeon 2024 FreQuant | Jeon, Park, Park, Kang. FreQuant: A reinforcement-learning based adaptive portfolio optimization with multi-frequency decomposition. KDD 2024, 1211–1221 | 10.1145/3637528.3671668 | 일치. arXiv판 없음. 4번째 저자 U Kang |
| Choi 2024 DeepClair | Choi, Kim, Gim, Lee, Kang. DeepClair: Utilizing market forecasts for effective portfolio selection. CIKM 2024, 4414–4422 | 10.1145/3627673.3680008; arXiv 2407.13427 | 일치 |
| Wang 2021 HRPM | Rundong Wang, Hongxin Wei, Bo An, Zhouyan Feng, Jun Yao. Commission fee is not enough: A hierarchical reinforced framework for portfolio management. AAAI 2021, 35(1):626–633 | 10.1609/aaai.v35i1.16142 | 일치. 제목에 "HRPM" 없음 — 본문 약칭 |
| Zha 2022 | Zha, Dai, Xu, Wu. A hierarchical reinforcement learning framework for stock selection and portfolio. IJCNN 2022, 1–7 | 10.1109/IJCNN55064.2022.9892378 | 일치. 제목은 Crossref 기준("...and Portfolio"로 끝남) |
| Wang 2021 DeepTrader | Zhicheng Wang, Biwei Huang, Shikui Tu, Kun Zhang, Lei Xu. DeepTrader: A deep RL approach for risk-return balanced portfolio management with market conditions embedding. AAAI 2021, 35(1):643–650 | 10.1609/aaai.v35i1.16144 | 일치. HRPM의 Wang(Rundong)과 다른 사람 — 참고문헌 목록에서 2021a/2021b 구분 필요 |
| Li 2023 LSRE-CAAN | Jiahao Li, Yong Zhang, Xingyu Yang, Liangwei Chen. Online portfolio management via deep reinforcement learning with high-frequency data. Information Processing & Management 60(3):103247, 2023 | 10.1016/j.ipm.2022.103247 | 제목·게재처 확인(초안에 제목·게재처 없었음). LSRE-CAAN은 논문의 방법 이름(웹 검색·저자 코드 저장소 기준, 출판처 본문 미열람) |
| Wei 2025 MoEDRLPM | Ziqiang Wei, Deng Chen, Yanduo Zhang, Dawei Wen, Xin Nie, Liang Xie. Deep reinforcement learning portfolio model based on mixture of experts. Applied Intelligence 55(5), 2025 | 10.1007/s10489-025-06242-6 | 서지 일치. 약칭 "MoEDRLPM"이 논문에 쓰이는지 **미확인**(Springer 차단). 논문번호(article no.) 미확인 |
| Gort 2022 | Gort, Liu, Sun, Gao, Chen, Wang(6인). Deep reinforcement learning for cryptocurrency trading: Practical approach to address backtest overfitting | arXiv 2209.05559 | 서지 일치. 게재처 **미확인**: arXiv에 journal-ref 없음, Crossref에 학회판 없음. 2차 자료는 ICAIF'22 워크숍·AAAI'23 발표를 말하나 출판 기록 못 찾음 → arXiv로 인용 |

## 2. 예측 모델·학습 기법
| 키 | 서지(대조 결과) | 식별자 | 비고 |
|---|---|---|---|
| Ansari 2024 Chronos | Ansari, Stella, Turkmen 외(18인). Chronos: Learning the language of time series. TMLR 2024 | arXiv 2403.07815; OpenReview gerNCVqqtR | TMLR 게재 확인(OpenReview "Accepted by TMLR") |
| Wu 2020 MTGNN | Zonghan Wu, Pan, Long, Jiang, Chang, Zhang. Connecting the dots: Multivariate time series forecasting with graph neural networks. KDD 2020, 753–763 | 10.1145/3394486.3403118 | 일치 |
| Liu 2024 iTransformer | Liu, Hu, Zhang, Wu, Wang, Ma, Long. iTransformer: Inverted transformers are effective for time series forecasting. ICLR 2024 | arXiv 2310.06625 | 일치(OpenReview 서지 ICLR 2024 spotlight) |
| Nie 2023 PatchTST | Nie, Nguyen, Sinthong, Kalagnanam. A time series is worth 64 words: Long-term forecasting with transformers. ICLR 2023 | arXiv 2211.14730 | 일치(arXiv 주석 "Accepted by ICLR 2023") |
| Fan & Shen 2024 StockMixer | Jinyong Fan, Yanyan Shen. StockMixer: A simple yet strong MLP-based architecture for stock price forecasting. AAAI 2024, 38(8):8389–8397 | 10.1609/aaai.v38i8.28681 | 일치 |
| Kim 2022 RevIN | Taesung Kim, Jinhee Kim, Tae, Park, Choi, Choo. Reversible instance normalization for accurate time-series forecasting against distribution shift. ICLR 2022 | OpenReview cGDAkQo1C0p | ICLR 2022 포스터 페이지로 확인. arXiv판 없음. 저자 코드 BibTeX는 연도 2021로 적음 → 2022로 통일 |
| Hu 2022 LoRA | Hu, Shen, Wallis, Allen-Zhu, Li, Wang, Wang, Chen(8인). LoRA: Low-rank adaptation of large language models. ICLR 2022 | arXiv 2106.09685; OpenReview nZeVKeeFYf9 | 일치 |
| Gu & Dao 2023 Mamba | Albert Gu, Tri Dao. Mamba: Linear-time sequence modeling with selective state spaces | arXiv 2312.00752 | 일치. 이후 COLM 2024 게재(OpenReview 서지). arXiv 2023 인용도 가능하나 COLM 2024 표기를 권함 |
| Ke 2017 LightGBM | Ke, Meng, Finley, Wang, Chen, Ma, Ye, Liu(8인). LightGBM: A highly efficient gradient boosting decision tree. NeurIPS 30, 2017 | NeurIPS proceedings 6449f44a… | 일치(출판처 메타데이터) |
| Cuturi & Blondel 2017 | Soft-DTW: A differentiable loss function for time-series. ICML 2017, PMLR 70:894–903 | arXiv 1703.01541 | 일치 |
| Tavenard 2020 tslearn | Tavenard, Faouzi, Vandewiele 외(11인). Tslearn, a machine learning toolkit for time series data. JMLR 21(118):1–6, 2020 | jmlr.org/papers/v21/20-091 | 일치 |
| Mysore 2021 CAPS | Mysore, Mabsout, Mancuso, Saenko. Regularizing action policies for smooth control with reinforcement learning. ICRA 2021, 1810–1816 | 10.1109/ICRA48506.2021.9561138; arXiv 2012.06644 | 일치. 제목에 "CAPS" 없음 — 본문 방법 이름 |

## 3. RL 기초
| 키 | 서지(대조 결과) | 식별자 | 비고 |
|---|---|---|---|
| Mnih 2015 DQN | Mnih, Kavukcuoglu, Silver 외. Human-level control through deep reinforcement learning. Nature 518(7540):529–533 | 10.1038/nature14236 | 일치 |
| van Hasselt 2016 | Van Hasselt, Guez, Silver. Deep reinforcement learning with double Q-learning. AAAI 2016, 30(1) | 10.1609/aaai.v30i1.10295 | 일치. 쪽수는 Crossref에 없음(원 proceedings 2094–2100) |
| Sutton 1999 options | Sutton, Precup, Singh. Between MDPs and semi-MDPs: A framework for temporal abstraction in reinforcement learning. Artificial Intelligence 112(1–2):181–211 | 10.1016/S0004-3702(99)00052-1 | 일치 |

## 4. 금융 방법론·평가
| 키 | 서지(대조 결과) | 식별자 | 비고 |
|---|---|---|---|
| Bailey & López de Prado 2014 | The deflated Sharpe ratio: Correcting for selection bias, backtest overfitting, and non-normality. JPM 40(5):94–107 | 10.3905/jpm.2014.40.5.094 | 일치 |
| Bailey 2016/2017 PBO | Bailey, Borwein, López de Prado, Zhu. The probability of backtest overfitting. Journal of Computational Finance 20(4) | 10.21314/JCF.2016.322 | Crossref 발행일 2016-09(온라인), 권호 없음. eScholarship는 20(4). 흔히 인용되는 쪽수 39–69는 **미확인**. 연도는 2017(권호 기준) 또는 2016(온라인) 중 하나로 통일 |
| Black & Litterman 1992 | Global portfolio optimization. FAJ 48(5):28–43 | 10.2469/faj.v48.n5.28 | 일치 |
| Ledoit & Wolf 2004a | Honey, I shrunk the sample covariance matrix. JPM 30(4):110–119 | 10.3905/jpm.2004.110 | 일치. 표본 공분산을 단일 지수/상관 상수 목표로 축소 — **실무 포트폴리오 공분산 축소 인용에 이쪽이 맞다** |
| Ledoit & Wolf 2004b | A well-conditioned estimator for large-dimensional covariance matrices. JMVA 88(2):365–411 | 10.1016/S0047-259X(03)00096-4 | 일치. 항등행렬 목표 축소(sklearn `LedoitWolf`가 구현하는 것). 코드에서 sklearn `LedoitWolf`를 썼다면 이쪽을 인용 |
| Anderson 2012 | Anderson, Bianchi, Goldberg. Will my risk parity strategy outperform? FAJ 68(6):75–93 | 10.2469/faj.v68.n6.7 | 시작일 민감도 인용 후보 1(내용 메모 참고) |
| Hoffstein 2019 | Hoffstein, Sibears, Faber. Rebalance timing luck: The difference between hired and fired. Journal of Index Investing 10(1):27–36 | 10.3905/jii.2019.1.070; SSRN 10.2139/ssrn.3319045 | 시작일·리밸런싱 시점 민감도 후보 2 |
| Braun 2023 | Braun, Hoffstein, Israelov, Nze Ndong. The hidden cost in costless put-spread collars: Rebalance timing luck. Journal of Alternative Investments 26(2):60–74 | 10.3905/jai.2023.1.196 | 후보 3(옵션 전략, 부차적) |
| Hoffstein 2020 | Hoffstein, Faber, Braun. Rebalance timing luck: The (dumb) luck of smart beta | SSRN 10.2139/ssrn.3673910 | 동료 심사 게재 못 찾음 → SSRN WP |

## 내용 메모(초록·본문 수준)
- **EarnHFT(1):** 초록 — 1단계에서 "동적 계획법으로 최적 행동가치를 계산한 Q-teacher", 3단계 분 단위 라우터가 초 단위 에이전트 풀에서 선택. 초록은 "6개 기준선, 6개 지표에서 크게 앞섬, 2위 대비 수익성 30%"라고 씀. 본문(arXiv HTML, Table 1): 크립토 데이터 4개(BTC/TUSD, BTC/USDT, ETH/USDT, GALA/USDT), 기준선 6개는 PPO, DRA, DQN, CDQNRP, MACD, IV. → "PPO·DQN 기준선을 4개 크립토 데이터에서 앞섬"과 "DP 교사 Q*" 모두 **확인**. 단, "앞섬"은 저자 보고이며 모든 데이터·지표에서 일관되게 앞서는지는 표를 직접 대조하지 않았다(**미확인**).
- **FreQuant(2):** 서지만 확인. ACM DL 차단, arXiv판 없음, 공개 요약은 초록뿐(DFT 주파수 분해, Frequency State Encoder, Multi-Event Fusion Network). **top-K 선택 메커니즘: 미확인** — 사용자가 본문(KDD 판)으로 확인 필요.
- **DeepClair(3):** 초록 — 사전 학습 transformer 예측 모델 + DRL 포트폴리오, LoRA로 미세 조정. 본문(arXiv HTML): 점수 상위 자산 롱·하위 자산 숏 선택(비선택 자산 가중치 0), 시장 점수 모듈이 롱/숏 비율 ρ_t를 출력(롱 ρ_t, 숏 1−ρ_t). LoRA는 FEDformer 인코더 각 블록에 적용. → 노출(비율)·포지션 선택, LoRA 사용 **확인**. 데이터: Nasdaq·Dow Jones 시총 상위 26종목(1992~), 기준선 EIIE·HADAPS·DeepTrader 등.
- **시작일 민감도(28):** 10.2469/faj.v68.n6.7은 Anderson, Bianchi, Goldberg(2012) "Will my risk parity strategy outperform?"(FAJ 68(6):75–93). 초록(RePEc) 첫 번째 결론: "Even over periods lasting decades, the start and end dates of a backtest can have a material effect on results." → 백테스트 결과가 시작·종료일에 민감하다는 동료 심사 문헌으로 **확인**. 다만 대상은 위험 균형 등 정적 배분 전략(1926–2010 미국 자료)이지 RL이 아니다. 보완 후보: Hoffstein, Sibears, Faber(2019, JII) — 같은 전략이라도 리밸런싱 날짜(일정 오프셋)만 바꾸면 성과가 크게 달라지는 "rebalance timing luck"을 이론화하고, 리밸런싱 날짜를 엇갈린 N개 포트폴리오를 등가중으로 보유하면 줄어든다고 제시(초록·2차 요약 기준, 본문 미열람). 초기 포트폴리오의 경로 의존성 자체를 다룬 동료 심사 문헌은 이번 검색에서 찾지 못했다(**미확인**).
