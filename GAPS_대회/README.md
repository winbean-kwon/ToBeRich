# 제12회 GAPS ETF 투자 대회 — 진행 현황

**팀**: 권승빈 (AI 모델 파트) + RL 팀원 + 인간 운용역  
**최종 업데이트**: 2026-05-26

---

## 대회 개요

| 항목 | 내용 |
|------|------|
| 대회명 | 제12회 GAPS ETF 투자 대회 |
| 투자 유니버스 | 188개 ETF, 10개 카테고리 |
| 위험자산 비중 | ≤ 70% (하드 제약) |
| 월 회전율 | ≥ 10% (하드 제약) |
| 리밸런싱 주기 | 월 1회, 월말 기준 |
| 거래비용 | 편도 0.1% |
| 백테스트 기간 | 2021-01 ~ 2026-05 (워밍업 12개월 제외) |

---

## ETF 유니버스 구성

### 위험자산 (5개 카테고리, 최대 70%)

| 카테고리 | ETF 수 | 대표 종목 |
|---------|--------|----------|
| FX 및 원자재 | 7개 | ACE KRX금현물, KODEX 골드선물(H) |
| 해외주식_지수 | 43개 | TIGER 미국S&P500, KODEX 미국나스닥100 |
| 해외주식_섹터 | 31개 | TIGER 미국테크TOP10, TIGER 미국배당다우존스 |
| 국내주식_지수 | 17개 | KODEX 200, TIGER 200 |
| 국내주식_섹터 | 36개 | KODEX 반도체, PLUS K방산 |

### 안전자산 (5개 카테고리, 제한 없음)

| 카테고리 | ETF 수 | 대표 종목 |
|---------|--------|----------|
| 금리연계형/초단기채권 | 11개 | KODEX CD금리액티브, KODEX 머니마켓액티브 |
| 해외채권_회사채 | 7개 | TIGER 미국투자등급회사채액티브(H) |
| 해외채권_종합 | 11개 | ACE 미국30년국채액티브(H) |
| 국내채권_회사채 | 9개 | KODEX 종합채권(AA-이상)액티브 |
| 국내채권_종합 | 12개 | TIGER 단기통안채, KODEX 국고채3년 |

---

## 전략 설계: Human-AI Black-Litterman 파이프라인 (v2)

### 설계 철학

기존 v1에서는 RL이 BL 신뢰도 파라미터(τ, Ω)를 출력했으나, 이는 학습 신호가 약하다는 한계가 있었다.  
**v2**에서는 RL이 직접 **카테고리 배분 비중 `w_RL`**을 출력하고, 이를 역최적화를 통해 BL 뷰로 변환한다.  
인간 운용역의 정성적 배분 `w_Human`도 동일한 방식으로 변환 후, Black-Litterman이 두 독립 뷰를 베이지안으로 융합한다.

### 팀 역할 분담

| 역할 | 담당 | 입력 | 산출물 |
|------|------|------|--------|
| AI 피처 생성 | 권승빈 | 카테고리별 가격 시계열 | 카테고리별 월별 방향성 예측 `ai_pred` (10-dim) |
| RL 에이전트 | RL 팀원 | State (AI 예측 포함, 150-dim) | 카테고리 배분 비중 `w_RL` (10-dim) |
| 정성 분석 | 인간 운용역 | 거시경제 분석 | 카테고리 목표 비중 `w_Human` (10-dim) |
| BL + MVO 통합 | 공동 | `w_RL`, `w_Human`, Σ, Π | 최종 ETF 비중 `w*` |

### 전체 파이프라인

```
[Layer 0] 데이터
  188개 ETF 일별 종가 → 10개 카테고리 월별 수익률, 공분산 행렬 Σ
        ↓
[Layer 1] 시장 균형 Prior 수립  ← 03_black_litterman_prior.ipynb
  AUM 기반 w_mkt → CAPM 역최적화: Π = δ · Σ · w_mkt
        ↓
     ┌──────────────────────────────────┐
     ▼                                  ▼
[Layer 2] AI 피처 생성 (권승빈)    [Layer 3] 인간 운용역 분석
  Chronos + MTGNN 하이브리드          거시경제 분석 → 카테고리 목표 비중
  → ai_pred (10-dim)                  → w_Human (10-dim)
     ↓
[Layer 4] RL 에이전트 (PPO)  ← 04_rl_portfolio_agent.ipynb
  State: (카테고리 수익률 120 + 변동성 10 + ai_pred 10 + 전월비중 10) = 150-dim
  → w_RL (10-dim, 매월)
     ↓                                  ↓
[Layer 5] 역최적화 — BL 뷰 변환
  Q_RL   = δ · Σ_cat · w_RL
  Q_Human = δ · Σ_cat · w_Human
        ↓
[Layer 6] Black-Litterman 베이지안 융합  ← 05_bl_fusion_mvo.ipynb
  P = [I; I], Q = [Q_RL; Q_Human], Ω = diag(Ω_RL·I, Ω_Human·I)
  → 사후 수익률 E[R]_cat, Σ_post_cat
        ↓
[Layer 7] MVO 최적화
  max E[R]ᵀw - (λ/2)·wᵀΣw
  s.t. 위험자산 ≤ 70%, Σw=1, w≥0, 회전율 ≥ 10%
  → 최종 ETF 비중 w*
        ↓
[Layer 8] 월말 리밸런싱 실행
```

---

## 단계별 진행 현황

### ✅ 완료: 01 — ETF 데이터 수집

**노트북**: `notebooks/01_collect_etf_data_colab.ipynb`

- yfinance로 188개 ETF 일별 종가 수집 (2020-01 ~ 2026-05)
- 10개 카테고리 매핑 및 카테고리 월별 수익률 산출
- 기술적 지표 20개 계산 (SMA, EMA, MACD, RSI, 볼린저밴드, ATR, 거래량 등)

**출력 (Google Drive)**
- `etf_close_wide.parquet`: 188개 ETF 일별 종가 (wide format)

---

### ✅ 완료: 02 — 카테고리 모멘텀 백테스트

**노트북**: `notebooks/02_backtest_momentum.ipynb`

**전략 로직**
```
① 카테고리 12개월 모멘텀 계산
   → 위험 상위 3개 카테고리 + 안전 상위 2개 카테고리 선택

② 카테고리 내 ETF 3개월 모멘텀 계산
   → 카테고리 내 상위 33% ETF만 선택 (회전율 ≥ 10% 확보)

③ 비중: 위험 65% / 안전 35% 고정, 카테고리 내 선택 ETF 균등 배분
```

**백테스트 결과 (2021-01 ~ 2026-05)**

| 전략 | 누적수익률 | CAGR | 변동성 | Sharpe | MDD |
|------|-----------|------|--------|--------|-----|
| **카테고리 모멘텀** | 143.6% | 18.2% | 17.0% | 1.07 | -13.0% |
| 균등분산 BM | 81.1% | 11.8% | 9.3% | 1.27 | -9.5% |
| KODEX 200 | 209.6% | 23.6% | 30.5% | 0.77 | -34.2% |
| TIGER 미국S&P500 | 178.3% | 21.2% | 13.6% | 1.55 | -15.1% |

**문제점**: 균등분산 BM 대비 Sharpe 열세 (1.07 < 1.27) → v2 파이프라인으로 개선 목표

**개선 목표**

| 지표 | 현재 | 목표 |
|------|------|------|
| CAGR | 18.2% | > 21% |
| Sharpe | 1.07 | > 1.30 |
| MDD | -13.0% | < -12% |

---

### ✅ 완료: 02b — ETF 하이브리드 모델 (Chronos + MTGNN)

**노트북**: `notebooks/02b_etf_hybrid_model_colab.ipynb`

**목표**: 카테고리별 월별 방향성 예측 `ai_pred_monthly.parquet` 생성

| 모듈 | 역할 |
|------|------|
| **Chronos T5 Encoder** | Close price → 시계열 temporal 임베딩 (512-dim) |
| **MTGNN Adaptive Graph** | 20개 기술지표 × 학습된 인접 행렬 → 피처 간 상관관계 |
| **Fusion Layer** | Chronos 임베딩 + MTGNN 임베딩 → 카테고리별 월별 예측 수익률 |

- 졸업 프로젝트의 Chronos+iTransformer 구조에서 GAPS ETF 특성에 맞게 MTGNN으로 변경
- 출력 `ai_pred (10-dim)`은 BL에 직접 입력되지 않고 **RL 에이전트의 State에 포함**됨

---

### ✅ 완료: 03 — Black-Litterman Prior 수립

**노트북**: `notebooks/03_black_litterman_prior.ipynb`

| 단계 | 내용 |
|------|------|
| 1 | 카테고리 월별 수익률 로드 |
| 2 | 공분산 행렬 Σ 계산 (Ledoit-Wolf 수축 추정) |
| 3 | AUM 기반 시장 가중치 `w_mkt` 계산 |
| 4 | CAPM 역최적화: `Π = δ · Σ · w_mkt` |
| 5 | 위험회피계수 δ 추정 및 저장 |

**핵심 수식**: Π = δ · Σ · w_mkt  
(시장 균형 기대수익률 = 위험회피계수 × 공분산 × 시장 비중)

**출력 (Google Drive)**
- `bl_prior.pkl`: Σ, Π, δ, w_mkt

---

### ✅ 완료: 04 — RL 포트폴리오 에이전트 (PPO)

**노트북**: `notebooks/04_rl_portfolio_agent.ipynb`

**환경 설계 (ETFPortfolioEnv)**

| 항목 | 내용 |
|------|------|
| State | 최근 12개월 카테고리 수익률(120) + 변동성(10) + ai_pred(10) + 전월비중(10) = 150-dim |
| Action | 10-dim 로짓 → 소프트맥스 → 위험자산 ≤ 70% 자동 클리핑 |
| Reward | 월 초과수익률 − 0.1% × 거래회전율 |
| 학습 기간 | 2021-01 ~ 2023-12 |
| 테스트 기간 | 2024-01 ~ 2026-05 |

**알고리즘**: PPO (stable-baselines3)

**출력**
- `w_RL_monthly.parquet`: RL 에이전트의 월별 카테고리 배분 비중 (10-dim)

---

### ✅ 완료: 05 — Black-Litterman 융합 + MVO 최적화

**노트북**: `notebooks/05_bl_fusion_mvo.ipynb`

**핵심 수식**

역최적화 (BL 뷰 변환):
```
Q_RL    = δ · Σ_cat · w_RL
Q_Human = δ · Σ_cat · w_Human
```

BL 사후 수익률:
```
E[R] = [(τΣ)⁻¹ + Ω_RL⁻¹ + Ω_Human⁻¹]⁻¹
       × [(τΣ)⁻¹Π + Ω_RL⁻¹·Q_RL + Ω_Human⁻¹·Q_Human]
```

MVO 최적화:
```
max  E[R]ᵀw - (λ/2)·wᵀΣw
s.t. Σ(위험자산 비중) ≤ 0.70
     모든 w_i ≥ 0
     Σw_i = 1.00
     |w_t - w_{t-1}|₁ ≥ 0.10  (회전율 ≥ 10%)
```

**신뢰도(Ω) 설정 전략**

| 국면 | Ω_RL | Ω_Human | 의미 |
|------|------|---------|------|
| 평온 (저변동성) | 0.01 | 0.05 | RL 배분 강하게 반영 |
| 위기 (고변동성) | 0.10 | 0.01 | 인간 판단 우선 |

---

## 파일 구조

```
GAPS_대회/
├── README.md                              ← 이 파일
├── BL_pipeline_report.md                  ← v2 설계 상세 보고서
├── progress_report.md                     ← 초기 진행 보고서 (v1)
├── notebooks/
│   ├── 01_collect_etf_data_colab.ipynb    ✅ ETF 데이터 수집
│   ├── 02_backtest_momentum.ipynb         ✅ 카테고리 모멘텀 백테스트
│   ├── 02b_etf_hybrid_model_colab.ipynb   ✅ Chronos+MTGNN 하이브리드 모델
│   ├── 03_black_litterman_prior.ipynb     ✅ BL Prior 수립 (Σ, Π, δ)
│   ├── 04_rl_portfolio_agent.ipynb        ✅ PPO RL 에이전트 → w_RL
│   └── 05_bl_fusion_mvo.ipynb             ✅ BL 융합 + MVO → w*
├── src/
│   └── etf_universe.py                    ETF 유니버스 정의 (188개)
└── data/
    ├── backtest_metrics.csv               성과 지표 요약
    └── backtest_returns.csv               월별 수익률 시계열
```

### Google Drive (`GAPS_대회/data/`)

| 파일 | 내용 |
|------|------|
| `etf_close_wide.parquet` | 188개 ETF 일별 종가 |
| `backtest_cumulative.png` | 누적수익률 + 드로우다운 차트 |
| `backtest_heatmap.png` | 월별 수익률 히트맵 |
| `bl_prior.pkl` | Σ, Π, δ, w_mkt |
| `ai_pred_monthly.parquet` | Chronos+MTGNN 카테고리별 월별 예측 수익률 |
| `w_RL_monthly.parquet` | PPO 에이전트 월별 카테고리 배분 비중 |

---

## 다음 단계

1. **통합 백테스트**: v2 파이프라인 전체 롤링 백테스트 (2021-01 ~ 2026-05)
2. **성과 비교**: 카테고리 모멘텀(v1) vs BL+RL 파이프라인(v2) vs BM
3. **Ω 튜닝**: 변동성 국면 감지 기반 자동 신뢰도 조정 실험
4. **최종 보고서**: 대회 제출용 전략 보고서 작성
