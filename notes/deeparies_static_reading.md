# DeepAries 정적 읽기 기록 (코드 실행 전, 2026-10-27)

> 상태: **정적 예측**. 동적 점검(행동 주입) 전에 커밋한다. 동적 결과와 다르면 '읽기 오류'로 보고한다.
> 대상: Kim et al., "DeepAries: Adaptive Rebalancing Interval Selection for Enhanced Portfolio Selection", CIKM 2025 (applied research track), arXiv 2510.14985v1. 공식 저장소 `dmis-lab/DeepAries` @ `634f559cf4603eeb2ba7509e31319d076b21c16c` (2026-04-30). README 기여자에 제1저자 포함 → 공식층.

## 1. 비용 모형: 논문과 코드
- 논문 3장: w′(T_m) = y(T_{m−1})⊙w(T_{m−1}) / (y·w), μ(T_m) = 1 − c Σ_i |w_i(T_m) − w′_i(T_m)|, V(T_{m+1}) = μ·V·(y·w). 즉 **직전 배분의 드리프트 가중치와 새 목표의 차이**로 비용을 매긴다(2장 참조 명세와 같은 형태).
- 코드 기본 경로(`complex_fee=False`), `exp/exp_DeepAries.py` `TradingEnvironment.step` else 분기:
  - `weights_memory.append(weights)` — 매 스텝 **목표 가중치만** 추가(드리프트 가중치는 넣지 않음).
  - `weights_new = normalization(weights * (1+returns))` — **이번 목표**가 이번 구간 수익 후 드리프트한 가중치.
  - `weights_old = weights_memory[-3]` (길이 ≥3일 때) — 두 스텝 전 목표.
  - 비용 = c · Σ|w_{t−2} − drift(w_t)| · V, 값 = (V − 비용)(1 + w_t·r_t).
- **예측:** C1(설정 반영) **통과** — c가 바뀌면 보상·가치가 바뀐다. 보조 S1(크기·시점) **불일치** — 참조 비용 c·Σ|w_t − drift(w_{t−1})|와 다르다. TradeMaster의 `[-3]` 인덱싱(메모리에 [목표, 드리프트]를 번갈아 넣는 구조)과 같은 형태이나, 여기서는 목표만 넣으므로 `[-3]`이 두 스텝 전 목표를 가리킨다(추정, 계보 미확인).
  - 예측 사례 ① 같은 w를 매 스텝 유지: 참조 Σ|w − drift(w)|, 코드도 Σ|w − drift(w)| → 거의 같음(비율 ≈1).
  - 예측 사례 ② 두 포트폴리오 A, B를 번갈아: 참조 ≈ Σ|A − B|(큼), 코드 ≈ Σ|A − drift(A)|(드리프트 크기, 작음) → **비율 ≪ 0.9, 비용 과소 부과**.
  - 예측 사례 ③ 첫 두 스텝: 1스텝 `weights_old = weights` → Σ|w₁ − drift(w₁)|, 2스텝 `[-3]`=초기 영벡터 → Σ|drift(w₂)| = 1 → 현금에서 첫 매수 비용(c·1)이 **한 스텝 늦게** 부과.
- `complex_fee=True` 분기: Jiang 2017 반복식으로 μ를 구하나 `self.w_old = w_new`(μ·목표, 드리프트 전)를 저장 → 드리프트 무시. 논문 실험은 기본 경로로 추정(근거: 기본값, README 명령에 플래그 없음).
- 비용률: 코드 기본 `--fee_rate 0.0001`(0.01%) = 논문 5.5절 "baseline fee of 0.01%". 논문 3장 예시 0.002는 예시.

## 2. 시작 상태(C3)
- `reset()`: `w_old = 0`, `a0_old = 1` → 현금 시작. 학습·검증·백테스트 모두 같은 `reset`. 정책 입력에 직전 보유 없음(상태 = 시장 텐서) → 무상태 정책. 시작 상태 효과는 첫 매수 비용 1회(위 ③ 때문에 한 스텝 늦게) 수준으로 예측.

## 3. 그 밖의 평가 조건
- **보상 형성에 사후 정보:** 학습 보상에 `optimal_horizon_index = argmax_h (w·r_h)`(실현된 미래 수익으로 고른 최적 구간)와 일치하면 ×1.2, 아니면 ×0.8. 논문 식 (2)에 명시. 학습 신호에만 쓰이고 백테스트에는 없음 → 미래 정보 누출 아님(특권 보상).
- **라벨 시점:** 입력 = [idx, idx+seq_len) 날짜(마지막 날 제외), 수익 = close_{d+h}/close_d − 1 (d = idx+seq_len). 누출 없음(오히려 하루 지연).
- **수익 기준:** `close`(yfinance `auto_adjust=False` → 분할 조정, 배당 미포함). 비교 지수 ^DJI도 가격지수라 같은 기준.
- **종목 집합:** `complete_dj30_tickers.csv` 27종목 — 2020년대 구성 종목 목록을 2000년부터 적용(사후 선정). WBA(2024-02 편출), INTC(2024-11 편출) 포함, AMZN·CRM·AMGN·HON·V·NVDA·SHW 등 미포함. `num_stocks=20` 상위 k 선택.
- **모델 선택:** 논문 "10 independent trials ... report the test results corresponding to the run with the lowest validation loss". 검증 손실 = 가치 손실 + β·예측 손실(수익 아님). 학습 중 `vali()`가 테스트 세트도 평가해 로그에 남기나 선택에는 쓰지 않음.
- **분할:** 논문은 "provided in our interactive demo"라 했으나 데모(deep-aries.github.io)에는 "Evaluation begins on January 1, 2021"만 있음. 코드 기본: 학습 < 2020-12-31, 검증 ~2021-12-31, 테스트 ≥ 2021-12-31 ~ 데이터 끝(2025-02 추정). 공개 체크포인트는 학습 < 2023-10-01, 테스트 2024 → **논문 Table 1과 다른 분할**.
- **학습 epoch:** 논문 미기재, 코드 기본 `--train_epochs 1`, early stopping patience 3.

## 4. 논문 본문 자체의 불일치 (기술 기록)
- Table 1 DJ30: DeepTrader CAGR 8.88% > DeepAries 7.90%인데 본문은 "consistently achieved the best results in CAGR (7.90%, 9.95%, 14.27%, 5.09%) ... in all markets".
- Table 1에 등가중(1/N)·buy-and-hold 바스켓 베이스라인 없음. 비교 대상은 지수, CSM, BLSW, EIIE, DeepTrader, DeepClair.

## 5. 재현 목표로 쓸 수치(사전 고정)
- 논문 Table 1 DJ30 DeepAries: CAGR 7.90%, SR 0.130, SoR 0.211, CR 0.577, MDD 13.67%. 지수: CAGR 6.15%, MDD 21.94%.
- 재현 설정은 코드 기본 분할·기본 하이퍼파라미터·fee 0.0001로 고정한다(논문에 분할이 없으므로 이것이 가장 직접적인 공식 설정). SR 정의(연율화 여부)는 논문에 없어 CAGR·MDD를 1차 비교 지표로 한다.
