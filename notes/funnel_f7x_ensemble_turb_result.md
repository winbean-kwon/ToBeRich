# F7x Ensemble 난류 문턱 반사실 — 결과 (2026-11-25, 탐색적)

> 사전 등록 `notes/funnel_f7x_ensemble_turb_prereg.md`(034c734). 판정 스크립트 sha256 1c4a89a3…23b1(사전 등록 커밋과 같음, 서버 clone도 같음). 2026-11-25 18:37 KST 서버 WSL에서 1회 실행. 출력 `replication/funnel_f7x_ensemble_turb/judge_result.json`(서버 사본 sha256 02f46515…d10b). F7 Ensemble 주 판정(부분 재현)은 바꾸지 않는다. 깔때기 집계에 넣지 않는다.

## 1. 실행
- 17회 모두 첫 시도에 `status ok`: C1~C5, T1~T5, O1~O5, R1, R2. 2026-11-24 23:52 재시작 뒤 끝은 11-25 18:3x KST다.
- 문턱은 조건 안의 실행끼리 모두 같았다(`thresholds_identical_across_runs` 4/4).
  - C: 18사이클 모두 140이다.
  - T: 사이클별 130.19 또는 96.08이다.
- 환경: `pip_freeze.txt`의 gym 0.15.3, tensorflow 1.15.2, stable-baselines 2.10.2가 F4 설치 기록(`~/f4work/ensemble/out/install_versions.log`)과 같다.

## 2. 사전 판정(4절)
지표는 F7과 같은 앙상블 Sharpe(1,097행)이다. 대비 값은 평균 차이와 Welch 95% 구간이다.

| 대비 | 차이 | 95% 구간 | 범주 |
|---|---|---|---|
| **C − P(주)** | −0.223 | [−0.443, −0.003] | **차이 있음(낮음)** |
| T − P(보조) | −0.217 | [−0.574, +0.140] | 구분 안 됨 |
| O − P(보조) | −0.737 | [−0.954, −0.520] | 차이 있음(낮음) |

- 실행별 Sharpe:
  - P: 1.176, 1.017, 1.012, 0.992, 0.845(평균 1.008)
  - C: 0.978, 0.795, 0.570, 0.924, 0.660(평균 0.785)
  - T: 1.019, 0.294, 0.924, 0.768, 0.949(평균 0.791)
  - O: 0.276, 0.001, 0.334, 0.466, 0.279(평균 0.271)
- **점검 R:** R1 0.889, R2 0.984로 둘 다 P 범위(0.845~1.176) 안이다. "시점 차이 가능" 표시는 하지 않는다.
- **기술(대비 아님):** C·T·O 평균은 모두 F7 R1 폭 [0.885, 1.715] 밖이다. Sharpe > 1.12인 실행은 셋 다 0개다.

**고정 해석 문장(5절 그대로)**
1. "기간별 문턱 덮어쓰기를 없애고 코드의 첫 값 140을 전 기간에 쓰면 Sharpe가 0.22만큼 낮아졌다(95% 구간 [−0.44, −0.003])." 문턱 선택에 대한 민감도로만 쓴다.
2. "저자의 출판 후 분위수 규칙으로 바꾸면, 5회씩의 실행으로는 Sharpe 차이를 구분하지 못했다(차이 −0.22, 95% 구간 [−0.57, +0.14]). T의 실행 간 분산이 커서(SD 0.29) 약 0.5 미만의 차이는 이 설계로 배제하지 못한다."
3. "이 코드에서 난류 규칙을 끄면 Sharpe가 0.74만큼 낮아졌다(95% 구간 [−0.95, −0.52])." 난류 규칙의 기여 크기로만 쓴다.

## 3. 보조(4.1, 판정 아님)
| 조건 | 누적 | 연수익 | 변동성 | Sharpe | MDD | 수익 0인 날(1,097행 중) |
|---|---|---|---|---|---|---|
| P | 38.3% | 7.7% | 7.7% | 1.01 | −7.7% | 374.8 |
| C | 42.9% | 8.5% | 11.2% | 0.79 | −15.6% | 138 |
| T | 27.5% | 5.7% | 7.3% | 0.79 | −6.9% | 421.6 |
| O | 17.3% | 3.6% | 20.6% | 0.27 | −41.1% | 17 |
| R | 34.7% | 7.1% | 7.6% | 0.94 | −7.5% | 378 |

## 4. 냉정한 해석(반박 심사 반영)
- **주 대비는 약한 근거다.** 범주는 사전 판정대로 "차이 있음(낮음)"이다.
  - 구간 상한이 −0.003이다.
  - C나 P에서 한 회만 빼면 10개 조합 중 7개에서 구간이 0을 포함한다(심사 재계산).
  - 차이(0.22)가 사전 MDE(약 0.24)보다 작다.
  - 탐색적으로 P에 R 2회를 합치면 [−0.413, +0.009]다.
- **보조 지표(서술, 경로 분리 아님).** 보조표 값은 실행별 지표의 평균이다.
  - C는 수익 0인 날이 375일에서 138일로 줄었다.
  - 변동성(+3.6%p, [3.1, 4.1])과 MDD(−8.0%p, [−11.7, −4.2])는 모든 실행에서 컸다.
  - 누적수익 차이(+4.6%p, [−8.9, +18.2])는 구분되지 않았다.
  - 이것은 Sharpe 감소와 일관된 기술일 뿐이다. 문턱은 검증 환경의 모델 선택에도 들어가므로 어느 경로인지 분리하지 못한다.
- **O 대비는 고정 문장 그대로만 쓴다:** "이 코드에서 난류 규칙을 끄면 Sharpe가 0.74 낮아졌다(95% 구간 [−0.95, −0.52])." 기여 비율("대부분")은 주장하지 않는다. O는 절제라서 모델 선택과 경로가 함께 바뀐다. 시험 구간에 2020년 3월 폭락이 있다는 점도 함께 적는다.
- **보고값과의 관계:** C·T·O 중 어느 것도 보고값 1.30에 가까워지지 않았다. 보고값과 우리 값 차이의 원인은 이 실험으로 설명되지 않는다.
- **선행 기록(심사):** 원 논문 SSRN 판 부록 목차에 "문턱 120 대 140의 Sharpe t-검정으로 최적 문턱 결정"과 "VIX를 쓰고 난류 지수가 없는 앙상블"이 있다. 저자가 문턱을 Sharpe로 조정한 기록이다. 수치와 C(140)와의 관계는 본문을 읽고 확인해야 한다(미확인). 제3자가 하드코딩 문턱의 민감도를 독립 측정한 사례는 찾지 못했다.

**논문 문단(심사 권장안):** "Replacing the period-specific turbulence thresholds in the released code (140, lowered to 100 and 90 in later trading periods) with the code's initial value of 140 throughout lowered the ensemble's Sharpe ratio by 0.22 on average over five runs per condition (Welch 95% CI [−0.44, −0.003]). This interval barely excludes zero, and the difference is below the minimum detectable effect of the design (≈0.24), so we treat it as weak evidence of sensitivity to the threshold choice. Under the constant threshold, the number of zero-return days fell from 375 to 138 of 1,097, and annualized volatility (+3.6 pp) and maximum drawdown were larger in every run, whereas cumulative return did not differ distinguishably. Because the threshold also enters the validation environment used for model selection, these differences cannot be attributed to a single mechanism. Using the authors' later quantile-based rule did not yield a distinguishable difference (−0.22, [−0.57, 0.14]), although differences below roughly 0.5 cannot be excluded given its higher run-to-run variance. Disabling the turbulence rule entirely lowered the Sharpe ratio by 0.74 ([−0.95, −0.52]). None of these variants approached the reported Sharpe ratio of 1.30."

## 5. 쓰지 않는 것(사전 등록 5·0절)
- "재현됐다/재현 실패", "누설이 확인됐다", "주된 원인", "문턱이 성과를 부풀렸다"는 쓰지 않는다. C − P가 "낮음"이어도 원인을 분리한 것이 아니기 때문이다.
- 저자가 논문에 어떤 문턱을 썼는지, 문턱을 시험 구간을 보고 정했는지는 판단하지 않는다.

## 6. 한계
- P는 2026-11-11~12에 돌았고, C·T·O는 11-24~25에 돌았다. 동시 대조가 아니다. R 2회가 P 범위 안이라는 것은 점검일 뿐이다.
- 조건당 5회다. 주 대비는 한 회만 빼도 10개 조합 중 7개에서 범주가 "구분 안 됨"으로 바뀐다.
- 난류 지수는 코드대로 가격 수준으로 계산했다. 논문 정의(수익률)와 다르다.
- T 규칙은 시험 구간이 끝난 뒤에 만들어졌다.
- 다중성 보정은 하지 않았다(주 대비 1개).
