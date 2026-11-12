# F1 수동 확인 목록 (2026-11-05)

자동 검색(arXiv 본문 링크, GitHub 검색)으로 공식 코드를 찾지 못했거나 확인이 필요한 논문이다. 각 논문에 대해 아래를 확인하고 `결과` 칸을 채운다.

- 확인할 곳: 논문 PDF 본문·각주(“code”, “github”, “available”), 학회 페이지의 supplementary, 1저자·교신저자 GitHub·개인 홈페이지, Papers with Code(현재 Hugging Face 이전).
- 공식으로 인정: 저자 본인·저자 조직 계정이거나 논문이 가리키는 저장소. 제3자 재구현은 “제3자만”.
- 결과 표기: `찾음: URL` / `제3자만: URL` / `링크 사망` / `없음`.

> **Claude 사전 확인(2026-11-10):** arXiv 전문 PDF의 링크·"code available" 문장, Hugging Face 논문 페이지(Papers with Code 후속), GitHub API(저장소 README·CITATION·소유자), 웹 검색으로 확인했다. "(약한 확인)"은 원문 PDF를 보지 못한 것이다. 사용자는 굵게 표시한 항목과 "(약한 확인)"만 보면 된다.

## A. 확인 필요(후보 있음)

| ID | 논문 | 무엇을 확인 | 결과 |
|---|---|---|---|
| Y25-02 | HARLF | 논문 3.4절의 Colab 노트북 링크가 열리는지, 학습·평가 코드인지 | 찾음(2026-11-12 정정): 각주 1 https://colab.research.google.com/drive/1DLQIooP7kNYHztQ7tHu5eO9NPNDPxIrY , 2 https://colab.research.google.com/drive/1FPX9_8z0X39Pg3tf1bSvoByEWbbQ_juF , 3 https://colab.research.google.com/drive/1SbKGmPLjF2DAKkNwEYdfc_2lS2KWMySi 모두 로그인 없이 열림. 11-10 "링크 사망"은 PDF 텍스트의 밑줄(_)이 공백으로 추출된 주소로 연 오류. 학습·평가(PPO·SAC·DDPG·TD3 하위·메타·슈퍼 에이전트, 백테스트)는 2번에만 있고 감성 입력은 `np.random.uniform` 시뮬레이션. 3번(논문 설명: 학습 포함 전체 파이프라인)은 셀 12개로 감성 추출뿐(사용자 확인). 실제 감성→관측 벡터 연결 코드 없음 → F2 비고 |
| SQ-SCR | Scenario-Context Rollout (KDD 2026) | edrtfu531/rlscr1 이 이 논문 코드인지(README·논문 대조) | 찾음: https://github.com/edrtfu531/rlscr1 (2026-11-12) — KDD 2026 최종판(사용자 제공 PDF) 1쪽(논문집 쪽 번호 150) 왼쪽 단 아래 "Resource Availability"가 이 저장소와 Zenodo 보관본(10.5281/zenodo.20410374)을 명시, ACM Artifacts Available 배지. arXiv v1에는 링크 없음. 저장소·Zenodo 2026-11-12 열림 |
| SUP-CLRS | CLRS (IJCAI 2023) | BlackBoxOperator/FinTech-DPM 소유자가 저자(Lien, Li, Wang) 중 하나인지 | 링크 사망(사본만, 2026-11-12 정정): 논문이 가리키는 sophialien/FinTech-DPM 404. BlackBoxOperator/FinTech-DPM은 README에 "official implementations"가 적힌 사본(포크 아님, 2023-08-10 생성)이지만 계정 이름·소속이 비어 있어 저자 계정 확인 불가. 11-10의 "찾음"은 Claude 사전 확인이었고 기준 미충족 |
| P24-08 | DRL framework (Waterloo) | jackieli19 계정이 저자 본인인지 | 찾음: https://github.com/jackieli19/PGPortfolio/tree/Stock (2026-11-12) — arXiv 2409.08426v1(사용자 제공 PDF) 부록 C 첫 문단(논문 쪽 번호 44)이 구현 저장소로 명시. PGPortfolio 포크. 저장소·Stock 브랜치 2026-11-12 열림 |

## B. 찾지 못함

| ID | 연도 | 논문 | 1저자 | 결과 |
|---|---|---|---|---|
| jiang2017crypto | 2017 | Cryptocurrency Portfolio Management with Deep Reinforcement Learning | Zhengyao Jiang | (Claude 사전 확인 2026-11-10) 없음: arXiv 1612.01277 본문·HF에 링크 없음. 같은 저자의 PGPortfolio는 다른 논문(1706.10059) 코드 |
| wang2019alphastock | 2019 | AlphaStock: A Buying-Winners-and-Selling-Losers Investment Strategy using Interpretable Deep Reinforcement Attention Networks | Jingyuan Wang | (Claude 사전 확인 2026-11-10) 제3자만: FinOL 라이브러리 재구현(finol.readthedocs.io). arXiv 1908.02646 본문에 링크 없음 |
| ye2020sarl | 2020 | Reinforcement-Learning Based Portfolio Management with Augmented Asset Movement Prediction States | Yunan Ye | (Claude 사전 확인 2026-11-10) 없음: arXiv 2002.05780 본문에 링크 없음 |
| yu2019modelbased | 2019 | Model-based Deep Reinforcement Learning for Dynamic Portfolio Optimization | Pengqian Yu | (Claude 사전 확인 2026-11-10) 없음: arXiv 1901.08740 본문은 외부 도구(ibm-research-tokyo/dybm)만 인용, 논문 자체 코드 없음 |
| park2020dqn | 2020 | An intelligent financial portfolio trading strategy using deep Q-learning | Hyungjun Park | (Claude 사전 확인 2026-11-10) 없음: arXiv 1907.03665 본문에 링크 없음 |
| benhamou2020bridging | 2020 | Bridging the gap between Markowitz planning and deep reinforcement learning | Eric Benhamou | (Claude 사전 확인 2026-11-10) 없음: arXiv 2010.09108 본문에 링크 없음 |
| W21_HRPM | 2021 | Commission Fee is not Enough: A Hierarchical Reinforced Framework for Portfolio Management | Rundong Wang | 없음(사용자 제공 PDF, Claude 판독 2026-11-12, arXiv 2012.12620v2 전문: 링크 없음, 데이터 출처 wind.com.cn만) |
| W22_MetaTrader | 2022 | MetaTrader: An Reinforcement Learning Approach Integrating Diverse Policies for Portfolio Optimization | Hui Niu | (Claude 사전 확인 2026-11-10) 없음: arXiv 2210.01774 본문은 qlib·stockstats만 인용 |
| W22_MSPM | 2022 | MSPM: A modularized and scalable multi-agent reinforcement learning-based system for financial portfolio management | Zhenhan Huang | (Claude 사전 확인 2026-11-10) 제3자만: https://github.com/oft2026/mspm ("Unofficial PyTorch reproduction"). arXiv 2102.03502 본문은 mlfinlab만 인용 |
| W21_PigorschSchafer | 2021 | High-Dimensional Stock Portfolio Trading with Deep Reinforcement Learning | Uta Pigorsch | (Claude 사전 확인 2026-11-10) 없음: arXiv 2112.04755 본문에 링크 없음 |
| W21_LFSS | 2021 | Deep Reinforcement Learning for Portfolio Optimization using Latent Feature State Space (LFSS) Module | Kumar Yashaswi | 없음(사용자 제공 PDF, Claude 판독 2026-11-12, arXiv 2102.06233v1 전문: 링크 없음) |
| W22_PretoriusVanZyl | 2022 | Deep Reinforcement Learning and Convex Mean-Variance Optimisation for Portfolio Management | Ruan Pretorius | (Claude 사전 확인 2026-11-10) 없음: arXiv 2203.11318 본문에 링크 없음(F1 자동 검색의 FinRL·cvxportfolio는 의존 라이브러리) |
| W21_Benhamou_crisis | 2021 | Detecting and adapting to crisis pattern with context based Deep Reinforcement Learning | Eric Benhamou | (Claude 사전 확인 2026-11-10) 없음: arXiv 2009.07200 본문에 링크 없음 |
| P24-03 | 2024 | FreQuant: A Reinforcement-Learning based Adaptive Portfolio Optimization with Multi-frequency Decomposition | Jihyeong Jeon | (Claude 사전 확인 2026-11-10) 없음(약한 확인): 웹 검색에 코드 없음, 원문 PDF 미확인 |
| P24-04 | 2024 | Combining Transformer based Deep Reinforcement Learning with Black-Litterman Model for Portfolio Optimization (BDA) | Ruoyu Sun | 없음(사용자 제공 PDF, Claude 판독 2026-11-12, arXiv 2402.16609v1: "Data availability"가 코드를 "교신저자에게 합리적 요청 시 제공"으로만 명시 — 공개 코드 아님. 각주 qlib 링크는 라이브러리) |
| P24-05 | 2024 | Hierarchical Reinforced Trader (HRT): A Bi-Level Approach for Optimizing Stock Selection and Execution | Zijie Zhao | (Claude 사전 확인 2026-11-10) 없음: arXiv 2410.14927 본문에 링크 없음 |
| P24-06 | 2024 | Deep Reinforcement Learning and Mean-Variance Strategies for Responsible Portfolio Optimization | Fernando Acero | (Claude 사전 확인 2026-11-10) 없음: arXiv 2403.16667 본문에 링크 없음 |
| P24-07 | 2024 | Markowitz Meets Bellman: Knowledge-distilled Reinforcement Learning for Portfolio Management | Gang Hu | 없음(사용자 제공 PDF, Claude 판독 2026-11-12, arXiv 2405.05449v1 전문: github·code 링크 없음) |
| P24-09 | 2024 | Portfolio Management using Deep Reinforcement Learning | Ashish Anil Pawar | (Claude 사전 확인 2026-11-10) 없음: arXiv 2405.01604 본문에 링크 없음 |
| Y25-04 | 2025 | Reinforcement Learning-Based Cryptocurrency Portfolio Management Using Soft Actor–Critic and Deep Deterministic Policy Gradient Algorithms | Kamal Paykan | (Claude 사전 확인 2026-11-10) 없음: arXiv 2511.20678 본문에 링크 없음 |
| Y26-01 | 2026 | Regime-Aware Portfolio Management via Retrieval-Augmented LLM-Guided Expert Switching | Ahmad Asadi | (Claude 사전 확인 2026-11-10) 없음: arXiv 2608.28252 본문에 링크 없음 |
| Y25-05 | 2025 | MTS: A Deep Reinforcement Learning Portfolio Management Framework with Time-Awareness and Short-Selling | Fengchen Gu | (Claude 사전 확인 2026-11-10) 없음: arXiv 2503.04143 본문에 링크 없음 |
| Y25-06 | 2025 | MIGT: Memory Instance Gated Transformer Framework for Financial Portfolio Management | Fengchen Gu | (Claude 사전 확인 2026-11-10) 없음: arXiv 2502.07280 본문에 링크 없음 |
| Y25-07 | 2025 | Hybrid LSTM and PPO Networks for Dynamic Portfolio Optimization | Jun Kevin | (Claude 사전 확인 2026-11-10) 없음: arXiv 2511.17963 본문에 링크 없음 |
| Y25-08 | 2025 | SAMP-HDRL: Segmented Allocation with Momentum-Adjusted Utility for Multi-agent Portfolio Management via Hierarchical Deep Reinforcement Learning | Xiaotian Ren | (Claude 사전 확인 2026-11-10) 없음: arXiv 2512.22895 본문에 링크 없음 |
| Y25-09 | 2025 | FR-LUX: Friction-Aware, Regime-Conditioned Policy Optimization for Implementable Portfolio Management | Zhang Jian'an | (Claude 사전 확인 2026-11-10) 없음: arXiv 2510.02986 본문에 링크 없음 |
| Y25-10 | 2025 | Reinforcement-Learning Portfolio Allocation with Dynamic Embedding of Market Information | Jinghai He | (Claude 사전 확인 2026-11-10) 없음: arXiv 2501.17992 본문·HF에 링크 없음 |
| Y26-02 | 2026 | Deep Reinforcement Learning Framework for Diversified Portfolio Management Across Global Equity Markets | Kamil Kashif | (Claude 사전 확인 2026-11-10) 없음: arXiv 2605.17307 본문에 링크 없음 |
| Y26-04 | 2026 | When News Gets Old: Portfolio Allocation with Reinforcement Learning and Large Language Models | Bolin Song | (Claude 사전 확인 2026-11-10) 없음: arXiv 2610.30564 본문에 링크 없음 |
| SQ-DPSRRL |  | DPS-RRL (AAAI SA 2020) |  | (Claude 사전 확인 2026-11-10) 없음(약한 확인): 2쪽 학생 초록, 웹 검색에 코드 없음, PDF 미확인 |
| SQ-ALRL |  | Augmented Lagrangian RL (AAAI SA 2025) |  | (Claude 사전 확인 2026-11-10) 없음(약한 확인): 학생 초록, 웹 검색에 코드 없음, PDF 미확인 |
| SQ-XPM |  | XPM (CIKM 2021) |  | (Claude 사전 확인 2026-11-10) 없음(약한 확인): 웹 검색에 코드 없음, ACM 원문 미확인 |
| SQ-DGDRL |  | DGDRL (CIKM 2024) |  | (Claude 사전 확인 2026-11-10) 없음(약한 확인): 웹 검색에 코드 없음, ACM 원문 미확인 |
| SQ-APTS |  | Automated portfolio trading RRL (ICAIF 2021) |  | (Claude 사전 확인 2026-11-10) 없음: arXiv 2110.05299 본문에 링크 없음 |
| SQ-ObjDriven |  | Objective Driven (ICAIF 2022) |  | (Claude 사전 확인 2026-11-10) 없음(약한 확인): 웹 검색에 코드 없음, ACM 원문 미확인 |
| SQ-Regret |  | Regret-Optimized (ICAIF 2025) |  | (Claude 사전 확인 2026-11-10) 없음: arXiv 2502.02619 본문은 arch 라이브러리만 인용 |
| SQ-MAPS |  | MAPS (IJCAI 2020) |  | 없음(사용자 제공 PDF, Claude 판독 2026-11-12, arXiv 2007.05402v1 전문: 링크 없음. 1저자 Jinho Lee 확인) |
| SQ-TwoLevel |  | Two-level RL ambiguous MV (IJCAI 2020; F0 보류) |  | (Claude 사전 확인 2026-11-10) 없음: IJCAI 공개 PDF 본문에 링크 없음 |


## C. 무작위 표본 감사(2026-11-12)

B의 "없음" 판정 30편 중 시드 20261111로 뽑은 5편(P24-07, SQ-MAPS, W21_LFSS, P24-04, W21_HRPM)을 사용자가 PDF로 받아 주었고 Claude가 판독했다. 5편 모두 기존 판정과 같다(불일치 0/5). 사전 규칙(`notes/claim_ledger.md` F)대로 B 전체 재확인은 하지 않는다. 한계: 표본 5편의 0/5는 오판율이 낮다는 약한 근거일 뿐이다(오판율 30%여도 5편 모두 맞을 확률 약 17%).
