# 문헌 조사 자동 독립 재코딩 — 결과 (2026-11-27)

> 사전 등록 `notes/lit_auto_coder_prereg.md`(94fd569). 표본 `notes/lit/lit_auto_coder_sample.csv`(15편), 자동 코딩 `notes/lit/lit_auto_coding.csv`, 계산 `replication/lit_auto_agreement.py` → `.json`.
> 코더: 새 맥락 에이전트, 항목 정의·표본 목록만 읽음(원 코딩 미열람), 본문만(코드 안 봄), 15편 모두 원문 확보.

| 항목 | 원일치 | κ | 원 조사 True | 자동 True |
|---|---|---|---|---|
| stateful | 14/15 | 0.857 | 9 | 10 |
| init_in_paper | 14/15 | 0.865 | 7 | 6 |
| eval_warmup | 15/15 | — (모두 False) | 0 | 0 |
| init_sensitivity | — | — | 0(원 조사 0/56) | 0 |
| test_initial_holding(범주) | 12/15 | — | | |

- 불일치: stateful·init_in_paper 모두 W21_FinRL(원 False/True, 자동 True/False). 시작 보유 범주 불일치 3편(DeepTrader, FinRL, MASA)은 원 조사가 "코드에만 있음(본문 미명시)"으로 기록한 경우로, 본문만 보는 자동 코더 정의상 unspecified다.
- 기여 2의 핵심(워밍업 0, 민감도 0)은 표본 15편에서 자동 코더도 같았다. P23-03의 "burn year"는 학습–평가 사이 공백 연도이고 평가는 현금 시작이라 워밍업이 아니라고 자동 코더가 판단했다.
- 한계: 사람 코더 아님, 같은 계열 모델, 15편.
