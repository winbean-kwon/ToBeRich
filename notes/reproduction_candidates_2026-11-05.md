# 추가 재현 후보 검토 + 가까운 선행 작업 (2026-11-05)

> 상태: 탐색적 검토. 반박 심사 1회 반영. 아직 사전 등록 아님 — 후보 선정 후 각 후보별 사전 등록을 따로 쓴다.
> 초점: **출판 DRL 포트폴리오 방법의 보고 성과가 공식 코드로 재현되는가.** 거래비용은 후보 선정 기준이 아니다(부록에만 기록).

## 0. 요약
- 목표: 재현 3편 → 4~6편, 돌리지 못한 논문은 깔때기 표(코드 공개 → 실행 가능 → 재현)로 결과화(Ferrari Dacrema et al. 2019 형식).
- 1순위 후보 **MARS (AAAI 2026)**, 2순위 **EarnMore (WWW 2024)**, 3순위 **SmartFolio (IJCAI 2025)**. DeepClair는 데이터 구축 부담으로 후순위.
- 가까운 선행 작업: Liangzhi Li의 공개 비심사 아카이브 `quant-papers-vs-baselines`. DRL 포트폴리오 논문의 **보고 수치 대비 재현 판정은 하지 않았음**(예측 모델에 대해서만 함). 차별화 필요.

## 1. 후보별 재현 가능성 (재현 관점)
기준: (1) 공식 코드 (2) 원 데이터 입수 (3) 보고 수치가 명확한 표 (4) 보고 수치를 낸 실행 조건(시드·체크포인트·선택 규칙)이 복원 가능한가 (5) Colab 시간.

| 순위 | 후보 | 공식 코드 | 원 데이터 | 비교할 보고 수치 | 실행 조건 복원 | 비고 |
|---|---|---|---|---|---|---|
| 1 | MARS (AAAI 2026, arXiv 2508.01173) | github.com/jiayiderekchen/MARS (2025-07 생성) | DJI 2024 시나리오 번들(train 2018–22, val 2023, test 2024) | Table 2, DJI 2024: Sharpe 2.84, 연수익 31.19%, MDD −5.39%(시드 42 단일 실행) | 체크포인트 포함(시드 123, ep130, validation-only BMID 선택). 시드가 논문과 다름 | 저자가 2026-07-10 커밋 c56d61a "Fix causal safety labels and add BMID selector"로 기본 경로를 바꾸고 이전(legacy) 경로 삭제. 논문 v2(2025-12)에는 언급 없음. 테스트 1년 → 검정력 낮음 |
| 2 | EarnMore (WWW 2024) | github.com/DVampire/EarnMore | DJ30 데이터 번들(~35MB) | 논문 표(확인 필요) | 미확인 | qlib 소스 설치, PyTorch 1.13 고정. 기존 계획(시드당 10 GPU시간 파일럿 기준) 유지 |
| 3 | SmartFolio (IJCAI 2025, p.1054) | github.com/ChloeWenyiZhang/SmartFolio | CSI300 전처리 pkl 포함(전체 데이터 ~520MB; nd100/sp500은 원시 CSV만) | CSI300 2024: ARR 0.491, SR 1.777(3회 평균) | 미확인 | 디스크상 CSI300만 현실적. torch_geometric·sb3 필요 |
| 4 | DeepClair (CIKM 2024) | github.com/jkcost/Deepclair | 미포함(.npy 직접 생성 필요) | Table 2·3 | Fedformer 체크포인트만 포함 | wandb 의존. 56편 조사의 "코드 미기재"는 정정 필요 |

깔때기 표로 갈 것:
- ReCAP (KDD 2026): 공식 저장소가 README에서 "minimum runnable implementation, rather than a complete replication", 학습 단계 축소를 명시 → "코드 공개 – 부분 구현(저자 명시)".
- LSRE-CAAN (IP&M 2023): 저장소에 모델 파일 1개뿐(학습·환경·데이터 없음) → "코드 공개 – 실행 불가".
- CLRS (IJCAI 2023): 논문이 링크한 github.com/sophialien/FinTech-DPM 이 404 → "링크 사망".
- FreQuant, MetaTrader(CIKM 2022), HRPM, SARL, AlphaStock, RiskBound: 공식 코드 확인 안 됨.

### MARS 재현 설계 초안 (사전 등록 전, 확정 아님)
- (a) 번들 체크포인트 그대로 test 평가 → 보고 수치와 대조.
- (b) 현재(수정 후) 코드로 다중 시드 처음부터 학습 → 보고 수치 분포 내 위치.
- (c) c56d61a 이전 코드로 다중 시드 학습 → 수정 전후 차이.
- 판정 기준·시드 수·선택 규칙은 실행 전 별도 사전 등록에 고정. 1년 테스트라 "구분 안 됨"은 정보량이 적다는 점을 판정 문구에 명시.

## 2. 가까운 선행 작업: Liangzhi Li `quant-papers-vs-baselines`
- 위치: huggingface.co/datasets/Liangzhi-Li/quant-papers-vs-baselines-data (2026-10-09 생성, 파일 74,735개, README "Private archive", license other). 원 GitHub conscienceli/quant-papers-vs-baselines 는 404. 논문·프리프린트는 웹 검색·GitHub에서 찾지 못함(Google Scholar·SSRN 직접 조회는 안 함).
- 성격: ~14개 LLM 에이전트가 병렬로 수행(AGENT_GUIDE.md). 질문은 "각 출판 방법이 단순 기준선(B&H, EW, ERC 등)을 비용 후 표본 외에서 개선하는가". 1~2라운드는 개인 14자산 하네스, 3라운드는 NDX100/SP500/CSI300, dev 2012–2024 / holdout 2025-01~2026-09 1회 읽기, 사전 규칙(R3_PREREG). 후보 199편 + untestable 120편.
- 보고 수치 재현: `r3_results/final/cn_reproduction.csv`(99행; yes 17, partly 10, no 1, 보고값 없음 71) — **CSI300 예측 모델(Qlib 기준선, MASTER, AlphaGen 등)만**. DRL 포트폴리오 행 없음.
- DRL 포트폴리오 겹침: DeepAries(공식 코드), EarnMore·SmartFolio(PyTorch 재작성), MARS(“공식 코드 없음”으로 자체 구현 — 실제로는 공식 저장소 있음), ReCAP(공식 최소 저장소, 평가 함수의 미래 정보 사용 지적). FinRL·AlphaMix+·MASA 없음.
- DeepAries 결과(그들의 설정, 단일 실행): dev Sharpe NDX100 0.72 vs EW 0.85, DV30 0.80 vs 0.81; holdout 1.14 vs 0.96, 1.52 vs 0.83. eff_n≈20·max_w≈0.05(사실상 상위 20 등가중). 그들 규칙상 dev 우위가 없어 "n.a.". 약 1.7년 holdout이라 차이는 통계적으로 구분 어려움.

### 우리와의 차이 (관련 연구 절에서 쓸 내용)
- 그들: 새 유니버스·새 기간으로 옮겨 단순 기준선과 비교, 다수 자체 구현, 비심사.
- 우리: DRL 포트폴리오 방법을 공식 코드·원 설정으로 돌려 **원 논문 보고 수치 대비 재현 여부**를 사전 등록 기준으로 판정.
- 인용은 데이터셋으로(URL, 커밋, 접근일). 그들의 발견(예: ReCAP 평가 누수)을 우리 발견처럼 쓰지 않는다.

## 3. 쓰면 안 되는 문장
- "보고 수치 재현 판정을 한 최초/유일 연구" — 위 아카이브가 예측 모델에 대해 함.
- "DRL 포트폴리오 방법은 1/N을 이기지 못한다"는 일반화 — 우리 결과는 원 데이터·원 설정 한정. 위 아카이브 DeepAries holdout이 반례 후보.
- "MARS 결과는 레이블 누수 때문" — 논문 수치가 수정 전 경로에서 나왔는지 미확인.
- "선행연구 없음" — "짧은 검색으로 찾지 못함"으로.

## 4. 기타 관련 문헌(반박 심사가 찾은 것, 자체 구현·일반 알고리즘 비교)
Velay et al. 2023 (arXiv 2306.10950), arXiv 2011.05381, Durall 2022 (arXiv 2208.07158). 특정 DRL 포트폴리오 논문의 공식 코드를 보고 수치와 대조한 출판물은 짧은 검색으로 찾지 못함.

## 5. 외부 LLM(Gemini) 조사 결과의 신뢰도
존재하지 않는 저장소(FinTech-DPM)를 "직접 검증"으로 기재, 실행 시간·체크포인트 등 미확인 서술, "분야 최초" 과장. 쓸모 있던 것은 각주의 Liangzhi Li 링크. 외부 LLM 조사 결과는 항목별 직접 확인 후에만 사용.

## 부록: 비용 관련 관찰 (후보 선정 기준 아님)
MARS 0.1% 차감(config.py:25, main.py:264–268), DeepClair fee=0.001 구현, SmartFolio env에 비용 항 없음(크기 미측정).
