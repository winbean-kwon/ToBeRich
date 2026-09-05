# 졸업 프로젝트 — 시계열 백본 + 강화학습 기반 포트폴리오 운용

> **논문 제목(확정)**: *포트폴리오 배분을 위한 계층적 강화학습에서의 과적합 진단: 세 시장에 걸친 실패 모드 캐스케이드와 일관성 우선 강건성 방법론*
> (*Diagnosing Overfitting in Hierarchical Reinforcement Learning for Portfolio Allocation: A Failure-Mode Cascade and Consistency-First Robustness Methodology Across Three Markets*)
>
> 한양대학교 데이터사이언스학과 졸업 프로젝트 (2026. 4 ~ 11), 시계열/RL 파트 담당: 권승빈
> 투고 목표: KDD Applied Data Science 트랙 / ACM ICAIF (2027 사이클)

---

## 1. 한 줄 요약

EarnHFT(Qin et al., AAAI'24)라는 논문은 원래 자산 하나, 포지션도 몇 단계 안 되는 세팅에서 계층적 강화학습(HRL)으로 고빈도 트레이딩을 하는 방법을 제안한다. 이 프로젝트는 그 구조를 44개 종목짜리 연속 포트폴리오 배분 문제로 옮기면 무슨 일이 벌어지는지 실제로 해본 기록이다. 옮기는 과정에서 거래비용 드래그, 학습에 관성을 내장했을 때의 알파 파괴, 전문가 풀의 다양성 붕괴, 라우터의 상수함수 붕괴까지 실패가 하나씩 순서대로 나타났고, 그때마다 원인을 진단하고 다음 버전으로 고쳐나갔다. 그 과정에서 헤드라인 테스트 성적만 봐서는 안 보이는 과적합을 잡아내는 검증-테스트 일관성 진단법을 만들게 됐는데, 그래서 이 프로젝트는 새로운 알고리즘을 제안하는 논문이라기보다 실패 사례 연구이자 진단 방법론에 가깝다.

여러 번의 시행착오 끝에 실제로 배포한 건 라우터도 없이, β=-30이라는 전문가 하나에 추론 시점 관성 스무딩(α=0.01)만 얹은 아주 단순한 구성이다. 지금까지 시험해본 10개 구성 중 검증(2025년 4분기)과 테스트(2026년 상반기) 양쪽에서 모두 플러스 성과를 내면서 그 격차도 가장 작은 건 이것 하나뿐이었고, 지금 바이낸스 실계좌에 실제로 붙어서 돌아가고 있다.

---

## 2. 프로젝트 구조 (트랙 2개 + 논문)

| 트랙 | 위치 | 상태 | 요약 |
|---|---|---|---|
| **① KOSPI 시계열 백본 트랙** | 저장소 루트 (`*.ipynb`, `*.py`, `data/`) | 완료 (2026-04 ~ 06) | 781종목 일봉 수집 → RevIN 패치 시퀀스 → FFT/DWT 주파수 피처 → DTW 클러스터링(K=5) → 백본 7종 비교 → **Chronos + MTGNN 하이브리드** 확정 → 일봉 PPO(실패, 등가중 대비 +0.28% vs +34.33%) |
| **② 크립토 HRL 트랙 (메인)** | `crypto/` | 완료·실계좌 배포 (2026-07 ~ 08) | Binance 44종목 5분봉 백필 → 하이브리드 백본 이식 → 단일 PPO 실패(−75.68%) → **EarnHFT 계층 구조 v1~v4 캐스케이드** → 라우터 붕괴 진단 → β=-30 단독 배포 + 강건성 검증 총망라 |
| **③ 논문화** | `paper/` | 초고 완성·10라운드 외부 비평 반영 (2026-07-29 ~ 08-19) | `DRAFT.md`(영문) / `DRAFT_KR.md`(국문) 초록~결론 1차 완성, 그림 2개, ablation 표, 관련연구 서지 확정 |

---

## 3. 아키텍처 (최종 배포 구성)

크립토 트랙의 최종 배포 시스템을 그림으로 그려보면 아래와 같다. 라우터(Stage C)는 4장에서 이야기하듯 결국 상수함수로 무너진 게 확인돼서 최종 구성에서는 빼버렸다 — 그래서 지금 실제로 돌아가고 있는 건 Stage A도, Stage B의 나머지 세 전문가도 없이 β=-30 전문가 하나와 그 위에 얹은 스무딩뿐이다.

```
시장 데이터 (Binance 5분봉 OHLCV, 44종목)
        │
        ▼
[백본]        Chronos(T5, 시간축 인코더) + MTGNN(자산 그래프) 하이브리드
              → 종목 × 30분 스텝 단위 64차원 임베딩
        │
        ▼
[Stage A]     레짐 분할 (시장 국면 분류) ─ 설계상 존재, 최종 배포는 β 고정이라 미사용
        │
        ▼
[Stage B]     전문가 풀 — 위험선호도 β ∈ {−90, −30, 30, 90} 조건부 PPO 4개
              행동공간: top-K(=10) 희소 종목선택 + 리스크게이트 ρ
              (FreQuant의 희소선택 + DeepClair의 리스크게이트를 저수준 행동공간에 이식)
        │
        ▼
[Stage C]     라우터 (DQN, 상황별 전문가 선택)  ✕ 최종 배포에서 제거 — 4장 참고
        │
        ▼
[배포 정책]    β = −30 전문가 단독 실행 (라우터 없음)
        │
        ▼
[추론 후처리]  지수 스무딩: w_new = (1−α)·w_old + α·softmax(action), α = 0.01
              (재학습 없이 추론 시점에만 적용 — 4.2절 참고)
        │
        ▼
실계좌 주문 실행 (Binance REST API, 30분 리밸런싱 주기)
```

### 3.1 컴포넌트 ↔ 코드 대응

| 구성요소 | 역할 | 코드 위치 |
|---|---|---|
| 시계열 백본 | Chronos+MTGNN 하이브리드 임베딩 생성 | `crypto/models/hybrid_model.py`, `crypto/notebooks/crypto_hybrid_model_colab.ipynb` |
| Stage A (레짐 분할) | 시장 국면 분류 (최종 배포 미사용) | `crypto/market_segmentation.py` |
| Stage B (전문가 풀) | β-조건부 PPO, top-K+게이트 행동공간 | `crypto/notebooks/crypto_hrl_earnhft_colab.ipynb` (§13, `SparseGatedCryptoPortfolioEnv`) |
| Stage C (라우터) | DQN, 최종 배포 미사용 | 위 노트북 §13-I, §22 (붕괴 진단·DDQN 재검증) |
| 배포 어댑터 | β=-30 로드 + 스무딩 적용 | `crypto/inference/policy_v4.py` |
| 실거래 루프 | 30분 주기 리밸런싱 실행 | `crypto/live_trading_loop_binance.py`, `crypto/broker/` |

---

## 4. 시행착오: 실패 모드 캐스케이드

크립토 트랙에서 실제로 있었던 일은 결국 이거다 — 단순한 방법을 하나 시도하고, 왜 안 되는지 알아내고, 고치고 나면 또 다른 문제가 나타나고, 다시 고치고. 날짜별로 정확한 기록은 `RL_PIVOT_SUMMARY.md` · `crypto/PROGRESS.md` · `paper/FINDINGS_LOG.md`에 있으니, 여기서는 그 흐름만 순서대로 풀어본다.

### 4.0 배경 — 단일 정책이 반복적으로 실패한다

제일 먼저 시도한 건 그냥 단일 PPO 하나에 포트폴리오 비중 결정을 전부 맡기는 거였다. 그런데 KOSPI에서도(일봉, +0.28% vs 등가중 +34.33%), 크립토에서도(30분봉, −75.68% vs 등가중 +2.66%) 똑같이 참패했다. 서로 다른 두 시장에서 독립적으로 같은 방식이 실패하니, 이건 단일 정책 자체의 한계라고 보고 계층 구조 쪽으로 방향을 틀었다.

### 4.1 v1 — EarnHFT 직접 이식

그래서 EarnHFT 논문의 구조를 그대로 가져왔다. 위험선호도 β별로 보상만 다르게 줘서 성향이 다른 전문가 4개를 만들고, 그 위에 라우터를 얹으면 등가중 정도는 이길 줄 알았다. 그런데 테스트해보니 비용 차감 후 −32.24%로 또 참패였다. 이상해서 비용을 빼고 다시 계산해봤더니, 비용 전 알파는 오히려 **+12.6%로 이미 등가중을 이기고 있었다** — 즉 신호는 있는데, 30분마다 리밸런싱하면서 나가는 거래비용(스텝당 턴오버 5.4%, 누적 드래그 −39.8%)이 그 알파를 전부 태우고 있었던 거다. 재학습 없이 추론 시점에서 관성(스무딩)만 걸어봤더니 비용 후 **+11.05%**로 완전히 뒤집혔다 — 지금도 총수익만 놓고 보면 가장 높은 구성이다. 여기서 얻은 교훈은 단순했다: 거래비용은 거의 항상 1차 용의자다.

### 4.2 추론 시점 관성 vs 학습 시점 관성

스무딩이 이렇게 잘 먹히니까, 아예 학습 단계에서부터 관성을 넣으면 더 낫지 않을까 싶었다(v2). 그런데 결과는 정반대였다 — 비용 후 수익은 −3.58%로 떨어졌고, 심지어 비용 전 알파마저 12.6%에서 0.92%로 거의 사라져버렸다. 이유를 따져보니, 관성을 학습 환경 안에 넣으면 지금 한 행동과 나중에 받는 보상 사이의 연결이 흐려져서 PPO가 뭘 잘했고 뭘 못했는지 구분(credit assignment)을 못 하게 되는 거였다. 그래서 원칙을 하나 세웠다 — **학습은 전권(α=1)으로 하고, 관성은 실행 단계에서만 건다.** (참고로 로봇 제어 쪽 CAPS(ICRA'21)라는 논문은 정확히 같은 방식을 학습에 넣어서 성공했다고 보고한다 — 도메인에 따라 정반대 결과가 나올 수 있다는 재미있는 대조 사례다.)

### 4.3 v3 — 더 충실한 재구현조차 다양성 엔진이 없다

이번엔 EarnHFT 원문에 더 충실하게 다시 구현해봤다. 현금을 액션에 포함시키고, 논문처럼 검증 구간 성적으로 후보를 엄격하게 골라내는 절차까지 갖췄다. 그런데 결과를 보니 20개 후보의 레짐별 성적이 서로 1%p도 차이가 안 났다 — 사실상 다 똑같은, 균등가중에 가까운 정책으로 수렴해버린 거다. 현금이라는 액션 자체를 거의 쓰지 않고 있었다. 혹시 우리 구현이 잘못된 건가 싶어서 EIIE, LSRE-CAAN이라는 다른 논문 아키텍처 두 개도 똑같은 방식으로 옮겨봤는데, 둘 다 마찬가지로 균등가중에 수렴했다. 세 번이나 반복되니 이건 구현 실수가 아니라 방식 자체의 문제라고 확신했다. 원인을 파보니, EarnHFT의 "다양성"은 사실 Stage I(동적계획법 기반 Q-teacher)이 β를 직접 정답 신호로 주입해주기 때문에 생기는 것이었다. β를 그냥 데이터 샘플링 우선순위 정도로만 쓰면 목적함수 자체는 그대로라서, 연속적인 액션 공간에서는 다양성이 저절로 생기지 않는다. 문제는 우리처럼 44개 종목을 다루는 규모에서는 이 DP 계산 자체가 경우의 수 폭발로 애초에 불가능하다는 거였다.

### 4.4 v4 — 구조적 행동공간 변경으로 다양성 복원

그래서 Q-teacher 없이 다양성을 만들 다른 방법을 고민했다. 44차원 연속 softmax로 아무 종목이나 원하는 비율로 담게 하는 대신, top-10 종목만 골라 그 안에서만 배분하게 하고(FreQuant 방식), 종목 선택과는 별개로 리스크 노출 자체를 조절하는 게이트 ρ를 하나 더 두었다(DeepClair 방식). 이번엔 통했다 — β별 평균 ρ가 0.109에서 0.545까지 뚜렷이 갈라졌고, 테스트 기간 동안 44개 종목 중 33개가 순환하며 선택됐다. 다만 스무딩을 걸지 않은 원본 정책 자체는 비용 전 알파가 −0.60%로 v1보다 오히려 약했다. 여기에 v1과 똑같은 추론 스무딩(α=0.01)을 적용했더니 비용 후 **+8.26%, Sharpe 2.168, MDD −5.22%** — 총수익은 v1+스무딩보다 낮지만 리스크 지표는 훨씬 좋아졌다.

### 4.5 "매칭" 라우터와 그 붕괴

다양성이 생겼으니 이제 라우터를 제대로 학습시켜보기로 했다. 라우터 학습 때 쓰는 "에피소드 진행률" 입력을 실제 서빙 환경과 맞춰줬더니 성적이 확 좋아졌다(Sharpe 2.168 → 3.046) — 처음엔 성공한 줄 알았다. 그런데 혹시나 해서 라우터를 떼고 β=30 하나만 단독으로 돌려봤더니, 수익률이고 샤프비율이고 **소수점까지 완전히 똑같이** 나왔다. 라우터가 상황을 보고 판단한 게 아니라, 그냥 β=30 하나만 계속 고르고 있었던 거다. 다행히 라우터를 떼기 전에 각 전문가의 비중 변화 궤적이 실제로 서로 다르다는 걸 따로 확인해뒀던 터라, "다양성이 또 무너진 거냐"와 "다양성은 있는데 라우터가 무시한 거냐"를 구분할 수 있었다 — 후자였다. 혹시 DQN 특유의 과대추정 편향 때문인가 싶어 DDQN으로 바꿔 재학습해봤는데도 똑같이 무너졌다 — 알고리즘 탓은 아니었다.

### 4.6 어느 전문가인가 — 검증/테스트 일관성으로 재선정

그럼 라우터가 그렇게까지 고집했던 β=30은 정말 좋은 전문가였을까? 검증 구간(2025년 4분기) 샤프비율을 보니 겨우 0.025였는데, 테스트 구간(2026년 상반기)에서는 3.046까지 치솟았다. 낙차가 너무 커서, 우연히 테스트 구간 시장 상황과 잘 맞아떨어진 것뿐일 가능성이 컸다. 그래서 라우터 없이 네 개 β를 전부 검증·테스트 양쪽에서 하나씩 비교해봤다. **β=-30만 유일하게 검증 1.314, 테스트 1.156으로 양쪽 다 견조하고 일관됐다.** 그래서 최종적으로 라우터를 완전히 걷어내고, β=-30 하나에 추론 시점 스무딩(α=0.01)만 얹은 걸 배포 정책으로 확정했다.

### 4.7 배포 후 강건성 재확인

이 결론이 우연이 아닌지 확인하려고 할 수 있는 건 다 해봤다. 시드를 6개에서 16개로 늘려 재학습해도, 다중 시도를 보정하는 DSR을 적용해도, 데이터 유출 없이 처음부터 다시 학습시켜도, top-K나 거래비용을 이리저리 바꿔봐도, 심지어 KOSPI·미국주식·과거로 거슬러 올라간 point-in-time 유니버스에서 다시 검증해봐도 결론은 바뀌지 않았다(앙상블만 예외적으로 오히려 나빠져서, 이건 부정적 결과로 남겨뒀다). 자세한 수치는 5.3·5.4절 참고.

---

## 5. 핵심 결과 (정량 요약)

### 5.1 구성별 성과 비교 (크립토 44종목, 테스트 2026 H1, TC 0.1%)

4장 서사에서 나온 각 버전의 실제 수치다.

| # | 구성 | 라우터 | 스무딩 | 순수익 | Sharpe | MDD |
|---|---|---|---|---|---|---|
| 0 | 등가중 벤치마크 | — | — | +2.66% | 0.367 | −40.09% |
| 1 | 단일 PPO (계층 없음) | — | — | **−75.68%** | −4.209 | −79.04% |
| 2 | v1: EarnHFT 직접 이식 | DQN | — | −32.24% | −1.107 | −50.04% |
| 3 | v1 + 추론 시점 스무딩 | DQN | α=0.01 | +11.05% | 0.638 | −36.47% |
| 4 | v2: 학습에 스무딩 내장 | DQN | 내장 | −3.58% | — | — |
| 5 | v3: 현금 행동 + 검증기반 선별 | DQN | — | +0.68% | 0.301 | −40.2% |
| 6 | v4 원본: top-K + 리스크게이트 | DQN | — | −0.60% (비용 전) | −7.107 | −23.61% |
| 7 | v4 + 스무딩 | DQN | α=0.01 | +8.26% | 2.168 | −5.22% |
| 8 | v4 매칭 라우터 | DQN(**상수함수 붕괴**) | α=0.01 | +7.48% | 3.046 | −3.33% |
| 9 | **β=-30 단독 (배포)** | **없음** | α=0.01 | **+5.66%** | **1.156** | −7.43% |

### 5.2 일관성 우선 기준: 검증(2025 Q4) vs 테스트(2026 H1)

| 전략 | 테스트 수익 | 테스트 Sharpe | 검증 Sharpe | \|검증−테스트\| 격차 |
|---|---|---|---|---|
| 등가중 | +2.75% | 0.370 | −0.436 | 0.806 |
| 매수후보유 | +19.00% | 0.848 | −0.554 | 1.402 |
| 횡단면 모멘텀 top-10 | **+106.04%** | 2.443 | −0.298 | **2.742 (최대)** |
| MVO (Ledoit-Wolf) | −9.10% | −0.129 | −0.437 | 0.308 |
| 리스크 패리티 | −13.60% | −0.419 | −0.423 | 0.003 (최소, 단 양 구간 모두 음수) |
| EIIE (2017) | +0.18% | 0.275 | −0.969 | 1.244 |
| LSRE-CAAN (2023) | +1.78% | 0.332 | −0.962 | 1.294 |
| **β=-30 RL (배포)** | +5.66% | 1.156 | **1.314** | **0.158 (양의 성과 중 최소)** |

- 모멘텀은 raw 수익률 20배지만 검증에서 참패 → 테스트에서만 터진 전형적 과적합 패턴.
- 리스크 패리티는 격차 최소지만 두 구간 다 마이너스 → "격차 작음 ≠ 좋은 정책"의 반증.
- 성공 기준 = **격차 작음 AND 양 구간 모두 양(+)** — 이 기준을 통과한 건 배포 정책뿐.

### 5.3 강건성 검증 목록 (전부 실행·논문 반영 완료)

| 검증 | 결과 |
|---|---|
| 다중 시드 (N=6 → 16) | 방향성 전 시드 재현, 크기는 시드 의존(σ=0.896). 배포 seed=42가 valid Sharpe 최대(1.314)·낙차 최소 |
| Deflated Sharpe Ratio | seed=42 0.447 (N=16) — 관습적 유의수준 미달, N을 3배 늘려도 결론 불변 |
| 블록 순열검정 (valid/test 격차) | β=30 p=0.282로 4β 중 최소(방향 일치) — 유의수준 미달, 검정력 한계 명시 |
| 클린 valid 재학습 (유출 없음) | +7.83% / Sharpe 1.393 — 배포보다 좋음, "valid 노출이 성능 부풀렸다" 우려 기각 (배포는 test 편향 방지 위해 불변) |
| 앙상블 (6시드 비중평균) | 격차 1.098로 오히려 악화 — 부정적 결과 |
| top-K 스윕 {5,7,10,15} | K=10만 격차 0.2 미만. 확신도 로짓 IC≈0 (종목 선택력은 없음, 부정적 결과) |
| TC 스윕 5~20bp | 비용 0.5~2배에서도 결론 불변 |
| DDQN 라우터 재학습 | 동일 상수함수 붕괴 재현 → 과대추정 편향 아님 확정 |
| λ-스윕 (β를 목적함수에 직접 주입) | 스피어만 ρ +0.4 → −0.8 단조 개선 — "채점 기준이 β마다 달라야 다양성이 생긴다" 진단 확인 |

### 5.4 다중 마켓 분석

| 시장 | 설계 | 결과 |
|---|---|---|
| KOSPI 5클러스터 (일봉) | 최종 레시피 축소 이식 (β풀 + 스무딩, top-K 제외) | valid 최선 후보(β=90, α=0.3, Sharpe 1.477)가 test에서 0.137로 참패 → **진단 기준이 배포 후보를 사전에 걸러냄** |
| 미국 S&P500 44종목 | 원시 가격윈도우 | 단일 PPO가 등가중과 동률 — 극적 실패 미재현 |
| 미국 S&P500 (confound 통제) | 같은 시장, Chronos 임베딩으로만 교체 | 턴오버 24배 급증·Sharpe 하락 → **architecture가 실패의 방향, market/레짐이 정도를 설명** |
| 크립토 point-in-time 13종목 (2021~) | 다년 walk-forward | 5개 관측치 전부 격차 >1.6 실패 — 다양성 정상이었는데도 실패 (한계로 정직하게 보고) |

---

## 6. 핵심 교훈 (반복 확인된 것)

1. 거래비용은 거의 항상 제일 먼저 의심해봐야 한다. "실패"라고 생각했던 것 대부분이 사실은 알파가 없어서가 아니라 회전을 억제하지 못해서였다 — 44종목 트랙의 v1도, BTC 트랙의 v1도 똑같았다.
2. 학습은 전권(α=1)으로 시키고, 관성은 실행 단계에서만 걸어야 한다. 추론 시점 스무딩이나 κ 히스테리시스는 잘 통했지만, 학습 환경 자체에 관성을 넣는 순간(v2) credit assignment가 무너졌다.
3. EarnHFT의 "다양성"은 사실 Stage I의 DP 기반 Q-teacher에서 나오는 것이었다. 포트폴리오 규모에서는 이 DP 계산 자체가 불가능하니, 행동공간을 구조적으로 제약(top-K + 게이트)해서 다양성을 억지로라도 만들어줘야 했다.
4. 라우터는 붕괴할 수 있고, 붕괴해도 헤드라인 성적은 오히려 더 좋아 보일 수 있다. 그래서 라우터를 떼고 단독으로 돌려본 결과를 소수점까지 비교해보는 걸 습관처럼 해야 한다 — 그 전에 전문가들의 궤적 다양성부터 따로 확인해둬야 "다양성이 없어서"인지 "라우터가 무시해서"인지 구분할 수 있다.
5. 중요한 건 "얼마 벌었나"가 아니라 "일관되게 버는가"다. 검증-테스트 격차와, 두 구간 모두 플러스인지를 같이 봐야 한다. DSR(다중 시도 보정)과 격차 진단(기간 편향 진단)은 서로 다른 걸 잡아내는 도구라 하나가 다른 하나를 대체하지 못한다.

---

## 7. 디렉토리 구조

```
졸업프로젝트/
├── README.md                          ← 이 파일
├── RL_PIVOT_SUMMARY.md                RL 트랙 서사 (증권사 연동 시도 → 크립토 HRL, 2026-07)
├── progress_report_final.md           KOSPI 시계열 파트 진행 보고서 (4~9월 단계별)
├── methodology_report.md              방법론 정리
│
│  ── KOSPI 시계열 백본 트랙 ──
├── collect_kr_stocks.py / collect_timeseries.py / collect_macro.py   데이터 수집
├── preprocess_sequences*.ipynb        RevIN + 패치 시퀀스
├── freq_features_colab.ipynb          FFT/DWT 주파수 피처 + LightGBM 검증
├── dtw_clustering_colab.ipynb         DTW K-Means (K=5) → cluster_assignments.csv
├── backbone_comparison_colab.ipynb    백본 1차 비교 → backbone_results.csv
├── extended_backbone_colab.ipynb      백본 2차 (MTGNN/Mamba/Chronos-LoRA) → backbone_results_extended.csv
├── cluster_attn_colab.ipynb           iTransformer 어텐션 분석 → cluster_attn_heatmap.png
├── hybrid_model_colab.ipynb           Chronos + MTGNN 하이브리드 → rl_embeddings.h5
├── rl_trading_colab.ipynb             KOSPI 일봉 PPO → rl_performance.csv, rl_backtest.png
├── kospi_hrl_generalization_colab.ipynb        KOSPI HRL 축소 이식 (7장)
├── us_equity_hrl_generalization_colab.ipynb    미국 S&P500 제3의 시장 (7장)
├── us_equity_embedding_confound_colab.ipynb    architecture confound 통제 실험 (7장)
├── broker/ , live_trading_loop.py, collect_minute_data_creon.py   KOSPI 분봉 실거래 시도 (중단, 보존)
├── data/                              KOSPI 데이터 (대용량은 gitignore, Drive 관리)
│
│  ── 크립토 HRL 트랙 (메인) ──
├── crypto/
│   ├── PROGRESS.md                    크립토 트랙 상세 체크포인트 (§1~10, 2026-07)
│   ├── DEPLOY_WINDOWS.md              Windows 24/7 실거래 봇 셋업 가이드
│   ├── universe.py                    거래대금 상위 USDT 현물 유니버스 산출
│   ├── collect_minute_data_binance.py 5분봉 히스토리 백필 (ccxt)
│   ├── backfill_pit_extra.py          point-in-time 추가 종목 백필 (DOT/THETA/XTZ)
│   ├── preprocess_features.py         기술지표 20개, 5분 그리드 정합화
│   ├── market_segmentation.py         레짐 분할 (Stage A)
│   ├── broker/                        Binance 클라이언트 (ccxt, 테스트넷/실계좌)
│   ├── inference/
│   │   ├── policy_v4.py               ★ 배포 정책 어댑터 (β=-30 단독 + α=0.01 스무딩)
│   │   ├── embeddings.py / features.py  라이브 추론용 피처·임베딩 파이프라인
│   ├── live_trading_loop_binance.py   ★ 30분 리밸런싱 실거래 루프
│   ├── policy_base.py
│   ├── models/
│   │   ├── hybrid_model.py, crypto_hybrid_best.pt          하이브리드 백본
│   │   └── crypto_hrl_pool_v4/agent_beta_-30.zip           ★ 배포 에이전트 (git 화이트리스트)
│   ├── data/                          features_5m/, minute_ohlcv_raw/ (gitignore), universe.csv, live_universe.json
│   └── notebooks/
│       ├── crypto_hybrid_model_colab.ipynb        백본 이식 → crypto_rl_embeddings.h5
│       ├── crypto_rl_trading_colab.ipynb          단일 PPO (실패)
│       ├── crypto_hrl_earnhft_colab.ipynb         ★ v1~v4 캐스케이드 + §14~22 진단 (메인 노트북)
│       ├── crypto_beta_robustness_colab.ipynb     다중 시드 6→16, 앙상블, DSR
│       ├── crypto_clean_valid_colab.ipynb         유출 없는 클린 valid 재학습
│       ├── crypto_baselines_colab.ipynb           B&H / 모멘텀 / MVO / 리스크 패리티
│       ├── crypto_eiie_baseline_colab.ipynb       EIIE (2017)
│       ├── crypto_lsre_caan_baseline_colab.ipynb  LSRE-CAAN (2023)
│       ├── crypto_pit_walkforward_colab.ipynb     point-in-time 다년 walk-forward
│       └── crypto_earnhft_btc_colab.ipynb         BTC 단일자산 EarnHFT 완전 이식 (병행 트랙, Stage I DP 포함)
│
│  ── 논문 ──
├── paper/
│   ├── README.md                      논문화 작업 현황 (상태표, 최신 작업 로그)
│   ├── DRAFT.md / DRAFT_KR.md         ★ 영문/국문 초고 (초록~결론, 동기화 유지)
│   ├── DRAFT_KR_easy.md               발표용 쉬운 버전
│   ├── FINDINGS_LOG.md                v1~v4 + 강건성 + 다중마켓 결과 통합 타임라인 (§0~23)
│   ├── ABLATION_TABLE.md              표 3개 (아키텍처 진화 / 최종 vs 베이스라인 / DSR)
│   ├── GAP_ANALYSIS.md                투고 전 채울 항목·우선순위·진행 상태
│   ├── RELATED_WORK.md                서지 (EarnHFT/FreQuant/DeepClair/EIIE/LSRE-CAAN/DSR/CAPS 등 확인 완료)
│   ├── MULTI_MARKET.md                KOSPI·크립토 공통 실패 패턴
│   └── figures/                       fig1 캐스케이드, fig2 valid/test 일관성 산점도 (+ generate_fig2.py)
│
├── Dockerfile / .dockerignore         Railway Worker 배포용 (crypto 실거래 루프)
└── .env.example                       KIS 인증정보 템플릿 (KOSPI 트랙 잔재)
```

---

## 8. 실행 방법

### 8.1 실험 재현 (Colab)

이 프로젝트의 관례: **Colab이 저장소를 마운트하지 않으므로 노트북마다 필요한 코드를 자기완결적으로 포함**한다. 데이터는 Google Drive `졸업프로젝트/data/`에 둔다.

크립토 트랙 순서:
1. `crypto/collect_minute_data_binance.py` → `preprocess_features.py` (로컬, `features_5m/`를 Drive에 업로드)
2. `crypto_hybrid_model_colab.ipynb` → `crypto_hybrid_best.pt`, `crypto_rl_embeddings.h5`
3. `crypto_hrl_earnhft_colab.ipynb` §1~13 (v1~v4) → §14~16 (라우터 붕괴 진단) → §17~22 (스윕·검정·DDQN)
4. 강건성 노트북들 (`crypto_beta_robustness`, `crypto_clean_valid`, `crypto_baselines`, `crypto_eiie_baseline`, `crypto_lsre_caan_baseline`)
5. 다중 마켓: `kospi_hrl_generalization`, `us_equity_hrl_generalization`, `us_equity_embedding_confound`, `crypto_pit_walkforward`

협업 패턴: Colab에서 실행 → 실행된 ipynb를 로컬에 교체 → 출력 파싱해 `paper/` 문서 갱신.

### 8.2 실거래 루프

```bash
pip install -r crypto/requirements.txt
cp crypto/.env.example crypto/.env   # BINANCE_API_KEY / SECRET / BINANCE_LIVE_MODE 설정

# dry-run (기본, 테스트넷)
python -m crypto.live_trading_loop_binance --model-dir crypto/models

# 실계좌
python -m crypto.live_trading_loop_binance --model-dir crypto/models --live
```

- 필요한 모델: `crypto/models/crypto_hybrid_best.pt`, `crypto/models/crypto_hrl_pool_v4/agent_beta_-30.zip` (둘 다 git에 포함).
- Railway 배포: 저장소를 연결하면 `Dockerfile`로 빌드, 서비스 타입 **Worker**. Windows 상시 구동은 `crypto/DEPLOY_WINDOWS.md` 참고.
- 라이브 전용 버그 이력: 프로세스 재시작 시 `prev_weights`가 등가중으로 리셋되던 문제 → 실계좌 포지션에서 역산하도록 수정(2026-07-29). `$1 미만 리밸런싱 스킵` 로직 때문에 더스트 포지션은 자동으로 안 빠질 수 있음 — 필요 시 수동 청산.

### 8.3 데이터 위치

| 파일 | 위치 | 비고 |
|---|---|---|
| `data/kospi_valid.parquet`, `sequences.h5`, `freq_features.h5`, `rl_embeddings.h5` | Drive `grad_project/data/` | gitignore |
| `crypto/data/minute_ohlcv_raw/`, `features_5m/` (2.5GB) | 로컬 + Drive `졸업프로젝트/data/crypto/` | gitignore |
| `crypto_rl_embeddings.h5`, `crypto_pit_rl_embeddings.h5` | Drive | 노트북이 생성 |
| 모델 가중치 (`agent_beta_*.zip`, 라우터, v1~v3) | Drive; 배포용만 git 화이트리스트 | `.gitignore` 참고 |

---

## 9. 문서 안내 — 어디를 읽어야 하나

| 알고 싶은 것 | 문서 |
|---|---|
| 논문 전체 서사·수치 (최신, 정본) | `paper/DRAFT_KR.md` (국문) / `paper/DRAFT.md` (영문) |
| 논문 작업 현황·남은 일 | `paper/README.md`, `paper/GAP_ANALYSIS.md` |
| 실험별 상세 수치 (Results 재료) | `paper/FINDINGS_LOG.md`, `paper/ABLATION_TABLE.md` |
| 크립토 트랙 초기 체크포인트 (7월) | `crypto/PROGRESS.md`, `RL_PIVOT_SUMMARY.md` |
| KOSPI 백본 파이프라인 상세 | `progress_report_final.md` |
| 배포 정책의 알려진 한계 | `crypto/inference/policy_v4.py` 모듈 docstring |

문서 간 최신성: `paper/` > `RL_PIVOT_SUMMARY.md` > `crypto/PROGRESS.md`. 7월 말 이후 내용은 `paper/`에만 반영돼 있다.

---

## 10. 현재 상태와 남은 일 (2026-09 기준)

**완료**
- 크립토 HRL 캐스케이드 v1~v4 + 라우터 붕괴 진단 + 강건성 검증 전 항목
- 다중 마켓(KOSPI, 미국 S&P500 + confound 통제, point-in-time walk-forward)
- 논문 초고 영/국문 완성, 제목 확정, 최종 통독 교정, 외부 비평 10라운드 반영
- 실계좌 라이브 루프 연동 (β=-30 단독, 로그 2026-07-29~31 확인)

**남은 일**
- `references.bib` / 정식 인용 스타일 변환 (투고 venue 확정 후)
- Acknowledgments, 재현성 statement
- NAV 시계열 그림 (원본 데이터 Colab 재추출 필요)
- 앙상블 격차 급증(1.098)의 정량적 해명 (시드별 top-K Jaccard 분석, 미착수)
- 미국 S&P500에 v4(top-K + 게이트) 전체 이식 (향후 과제로 명시됨)
- 졸업 프로젝트 최종 보고서·발표 (2026-11)

**의도적으로 하지 않기로 한 것**
- KOSPI 분봉/크레온/KIS 실거래 재개 (2026-07-13 중단 결정)
- KOSPI HRL 전체 캐스케이드 재이식 (부정적 결과로 유지)
- 성능 개선 목적의 앙상블·오버레이 실험 (논문 준비 항목 우선)
- 메인 트랙(NeurIPS/ICML/KDD 리서치) 투고를 위한 신규 알고리즘 개발 (ADS/ICAIF 먼저)
