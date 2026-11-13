# 재현성 선행연구 — 원문 확인 기록 (2026-11-13)

확인 방법:
- 문헌 확인 에이전트가 원문 PDF나 출판사 초록을 내려받아 읽었다. 서지는 Crossref로 대조했다.
- 핵심 인용 중 일부(★)는 Claude가 내려받은 원문 텍스트에서 다시 grep으로 확인했다.
- 대장 G1에 따라 **사용자가 인용 전에 원문을 한 번 확인한다.**

## 확인된 서지·수치

| 문헌 | 서지 | 확인된 내용 | 인용 시 주의 |
|---|---|---|---|
| Gundersen & Kjensmo | "State of the Art: Reproducibility in Artificial Intelligence", AAAI-18, DOI 10.1609/aaai.v32i1.11503 | 코드를 실행하지 않은 문서 조사. IJCAI·AAAI 400편 조사, ★실증 논문 325편 분석. 방법·데이터·실험 요인별로 변수의 20–30%만 문서화됨 | "400편 조사, 325편 분석" |
| Collberg & Proebsting | "Repeatability in Computer Systems Research", CACM 59(3):62–69, 2016, DOI 10.1145/2812803 | 601편. 코드로 뒷받침된 402편 중 ★30분 안에 빌드 32.3%, 추가 노력 포함 48.3%, 저자가 빌드된다고 답한 것까지 54.0%. 결과 검증은 하지 않음("weak repeatability"). 코드가 없으면 저자에게 메일과 독촉 | **CACM 본문은 열지 못함.** 수치는 기술보고서 TR 14-04 v2(2015)에서 확인. 인용 전 CACM 대조 필요 |
| Raff | "A Step Toward Quantifying Independently Reproducible Machine Learning Research", NeurIPS 2019, arXiv:1909.06674 | 저자 코드 없이 혼자 재구현. ★255편 중 162편(63.5%) 성공. 유의한 요인 10개(가독성 등). 코드 공개 여부는 유의하지 않음(p = 0.213). 저자 문의 50편, 응답률 52% | "몇 년 걸림"은 틀린 표현. 2012–2017년에 시도했고, ★최장 1편이 4.5년 |
| Henderson et al. | "Deep Reinforcement Learning That Matters", AAAI-18, DOI 10.1609/aaai.v32i1.11694 | 하이퍼파라미터·구조·보상 크기·시드·환경·코드베이스 민감도 | ★같은 설정으로 10회 실행해 5개씩 두 그룹으로 나눴더니 곡선이 유의하게 다름(TRPO HalfCheetah, p = 0.0016) |
| Hou, Xue & Zhang | "Replicating Anomalies", RFS 33(5):2019–2133, 2020, DOI 10.1093/rfs/hhy131 | 출판본은 이상 현상 452개. NYSE 구간점·가치가중에서 65%가 \|t\| < 1.96, t > 2.78 기준이면 82% 실패 | 447개는 NBER WP 판본 수치. 출판본 수치를 쓴다(에이전트 확인, Claude 재확인 안 함) |
| Jensen, Kelly & Pedersen | "Is There a Replication Crisis in Finance?", JF 78(5):2465–2518, 2023, DOI 10.1111/jofi.13249 | 93개국 153개 팩터. 대부분 재현된다는 결론. ★최종 재현율 82.4%(CAPM 알파 기준) | 원수익률 기준은 55.6%. WP 판본 수치(84.9% 등)와 다름 |
| ML Reproducibility Challenge | reproml.org | MLRC 2023부터 TMLR 게재가 조건이다. 이전에는 ReScience C 특별호였다. MLRC 2026은 NeurIPS 2026 공식 트랙이며 이미 마감됐다 | 2027 회차 공지는 아직 없음 |

## 이 연구와 가장 가까운 선행연구 (신규성 범위에 영향)

| 문헌 | 한 일 | 이 연구와의 차이 |
|---|---|---|
| Felizardo et al. 2022, "Reinforcement Learning Applied to Trading Systems: A Survey", arXiv:2212.06064 | RL 트레이딩 29편 리뷰. ★소스 코드 공개는 1편뿐 | 재실행 없음 |
| Srikantha et al. 2026, "AI and ML for Stock Market Prediction: A Systematic Literature Review … Reproducibility, and Evaluation Gaps (2016–2026)", Research Square 프리프린트(동료심사 전), DOI 10.21203/rs.3.rs-11084191/v1 | 주가 예측 685편의 코드 공개 감사(DRL 176편 포함). ★코드 공개 52편(7.6%) | 예측 중심, 재실행 없음. **반드시 인용하고 차별점을 밝힐 것** |
| Velay et al. 2023, "Benchmarking Robustness of DRL approaches to Online Portfolio Management", INISTA 2023, arXiv:2306.10950 | 오픈소스 DRL 알고리즘의 강건성 벤치마크 | 원논문 코드·수치를 재현하지 않음 |
| Liu et al. 2022, FinRL-Meta, NeurIPS 2022 D&B, arXiv:2211.03107 | "reproduce popular papers" | 대상이 자기 그룹의 논문이라 독립 재현이 아님 |
| Prata et al. 2024, "LOB-based deep learning models for stock price trend prediction: a benchmark study", AI Review 57, DOI 10.1007/s10462-024-10715-4 | LOB 모형 15개를 재실행해 보고 성능에 못 미침 | DRL이 아닌 예측 모형. 금융 DL 재실행의 선례 |
| Li 2024, arXiv:2409.08426 (석사논문, 이 연구 표본 P24-08) | EIIE 1편 재현 | 단일 논문 |

미확인으로 남은 것:
- Buczyński et al. 2023(Eng. Proc. 39:79): 본문 403 오류.
- TradeMaster·PRUDEX: 검색 결과로만 확인.
- Google Scholar·SSRN 직접 검색은 하지 못함.

## 신규성 서술 범위 (냉정)
- **쓸 수 있는 주장:** 포트폴리오 DRL 논문 표본에 대한 코드 가용성 깔때기와, 원저자 코드의 무수정 재실행 + 사전 등록 판정의 조합. 이번 검색에서는 직접 선례가 나오지 않았다. 다만 검색이 완전하지 않으므로 "처음"이라고 단정하지 않는다.
- **쓸 수 없는 주장:**
  - "금융 ML 코드 공개 감사가 처음": Felizardo 2022, Srikantha 2026 때문에 성립하지 않는다.
  - "금융 DL 재실행이 처음": Prata 2024 때문에 성립하지 않는다.
