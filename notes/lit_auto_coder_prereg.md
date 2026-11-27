# 사전 등록 — 문헌 56편 시작 보유 조사의 자동 독립 재코딩 (2026-11-27, 코딩 전)

> 목적: 1장 기여 2와 5.5의 문헌 조사(`notes/lit/lit_survey_merged.csv`, 1인 코딩)의 재현성을 일부 점검한다. 사람 두 번째 코더는 없다.
> 표본: 56편 중 원문 접근(`access` ∈ full_text, full_text+code) 54편에서 `random.seed(20261127); random.sample(sorted(ids), 15)`. 표본 목록은 `notes/lit/lit_auto_coder_sample.csv`(id·제목·1저자·연도·게재처·식별자만, 코딩 값 없음).
> 코더: 새 맥락의 에이전트(언어 모델). 이 문서의 "항목 정의"와 표본 목록 두 파일만 읽는다(기존 코딩·결과 미열람). 논문 원문(arXiv·게재처)만 본다. 코드는 보지 않는다(본문 기준 항목만).

## 항목 정의 (원 조사의 열 의미 그대로)
- **stateful**: 정책 입력에 직전 포트폴리오 가중치(또는 보유)가 들어가거나, 정책 출력에 명시적 관성(평활·EMA 등 직전 가중치와의 혼합)이 있다 → True/False.
- **init_in_paper**: 시험(평가) 구간을 시작할 때의 포트폴리오 보유를 본문(부록 포함)이 밝힌다 → True/False.
- **test_initial_holding**: 밝혔다면 무엇인가 → cash / equal / carried_over(직전 구간 보유를 이어받음) / random / other / unspecified.
- **eval_warmup**: 평가 구간 성과를 재기 전에 정책을 돌려 보유를 데우는(warm-up, burn-in) 절차가 평가에 있다(학습용 워밍업은 제외) → True/False.
- **init_sensitivity**: 시작 보유를 바꿔 결과의 민감도를 보고한다 → True/False.

## 지표 (고정)
- 항목별 원일치율(15편)과 이진 항목의 Cohen κ. test_initial_holding은 6범주 원일치율.
- 주된 관심: eval_warmup·init_sensitivity에서 자동 코더가 True를 찾는가(원 조사는 56편 모두 False). True가 나오면 근거 위치를 적고, 원 코딩과 대조한 결과를 그대로 보고한다(최종 코딩은 바꾸지 않되 불일치를 기록).
- 보고: "사람 두 번째 코더가 아니라 자동 재코딩"이라고 쓴다.
