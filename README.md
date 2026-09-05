# 졸업 프로젝트 — 시계열 백본 + 강화학습 기반 포트폴리오 운용

> **논문 제목(확정)**: *포트폴리오 배분을 위한 계층적 강화학습에서의 과적합 진단: 세 시장에 걸친 실패 모드 캐스케이드와 일관성 우선 강건성 방법론*
> (*Diagnosing Overfitting in Hierarchical Reinforcement Learning for Portfolio Allocation: A Failure-Mode Cascade and Consistency-First Robustness Methodology Across Three Markets*)
>
> 한양대학교 데이터사이언스학과 졸업 프로젝트 (2026. 4 ~ 11), 시계열/RL 파트 담당: 권승빈
> 투고 목표: KDD Applied Data Science 트랙 / ACM ICAIF (2027 사이클)

---

## 1. 한 줄 요약

EarnHFT(Qin et al., AAAI'24)류 **계층적 강화학습(HRL)을 단일자산·이산 포지션 세팅에서 연속·다자산 포트폴리오 배분으로 이식**하면서 순차적으로 마주친 실패 모드(거래비용 드래그 → 학습 내장 관성의 알파 파괴 → 전문가 풀 다양성 붕괴 → 라우터의 상수함수 붕괴)를 카탈로그화하고, 헤드라인 테스트 성적만으로는 보이지 않는 과적합을 잡아내는 **검증/테스트 일관성 진단**을 정식화한 실증 연구. 새로운 알고리즘이 아니라 **실패 모드 사례 연구 + 진단 방법론**이 기여의 핵심이다.

최종 배포 정책은 라우터 없이 **β=-30 전문가 하나 + 추론 시점 관성 스무딩(α=0.01)** — 시험한 10개 구성 중 검증(2025 Q4)·테스트(2026 H1) **양쪽에서 모두 양(+)의 성과를 내면서 격차가 가장 작은 유일한 구성**이며, 바이낸스 실계좌에 실제로 연동돼 있다.

---

## 2. 프로젝트 구조 (트랙 2개 + 논문)

| 트랙 | 위치 | 상태 | 요약 |
|---|---|---|---|
| **① KOSPI 시계열 백본 트랙** | 저장소 루트 (`*.ipynb`, `*.py`, `data/`) | 완료 (2026-04 ~ 06) | 781종목 일봉 수집 → RevIN 패치 시퀀스 → FFT/DWT 주파수 피처 → DTW 클러스터링(K=5) → 백본 7종 비교 → **Chronos + MTGNN 하이브리드** 확정 → 일봉 PPO(실패, 등가중 대비 +0.28% vs +34.33%) |
| **② 크립토 HRL 트랙 (메인)** | `crypto/` | 완료·실계좌 배포 (2026-07 ~ 08) | Binance 44종목 5분봉 백필 → 하이브리드 백본 이식 → 단일 PPO 실패(−75.68%) → **EarnHFT 계층 구조 v1~v4 캐스케이드** → 라우터 붕괴 진단 → β=-30 단독 배포 + 강건성 검증 총망라 |
| **③ 논문화** | `paper/` | 초고 완성·10라운드 외부 비평 반영 (2026-07-29 ~ 08-19) | `DRAFT.md`(영문) / `DRAFT_KR.md`(국문) 초록~결론 1차 완성, 그림 2개, ablation 표, 관련연구 서지 확정 |

---

## 3. 타임라인

```
2026-04  KOSPI 837종목 OHLCV + 기술지표 20개 수집 (781종목 유효)
2026-05  RevIN + 패치 시퀀스 생성 (sequences.h5), 방향 전환: 멀티모달(뉴스) → 강화학습
2026-06  FFT(13) + DWT(16) 주파수 피처 → LightGBM 검증 (AUC 0.5121 → 0.5250)
2026-07  DTW K-Means 클러스터링 (K=5, 757종목)
2026-08  백본 비교 1차(StockMixer/PatchTST/iTransformer/Chronos) + 2차(MTGNN/Mamba/Chronos-LoRA)
         → Chronos(방향성 1위) + MTGNN(2차 1위) 하이브리드 확정, rl_embeddings.h5 추출
         KOSPI 일봉 PPO: 등가중 대비 실패 (+0.28% vs +34.33%)
2026-07-10  분봉 실거래 시도 → KIS/크레온 제약(Windows COM)으로 KOSPI 분봉 트랙 중단
2026-07-13  자산군을 Binance 크립토로 전환 (히스토리 분봉 + REST 실거래 모두 Mac에서 가능)
2026-07-14  50심볼 5분봉 백필(2021~) → 44종목 피처 → 하이브리드 백본 이식 → 임베딩 생성
2026-07-17  단일 PPO −75.68% 실패 → EarnHFT HRL 이식 v1 (비용 드래그 진단, 추론 스무딩 +11.05%)
2026-07-17  v2: 학습에 관성 내장 → 알파 소멸 (부정적 결과)
2026-07-18  v3: EarnHFT 원문 충실 재구현 → 전문가 풀이 균등가중으로 붕괴 (다양성 엔진 부재)
2026-07-21  v4: top-K 희소선택(FreQuant) + 리스크게이트(DeepClair) → 다양성 복원
2026-07-28  "매칭" 라우터 채택 (Sharpe 3.046) → 실계좌 라이브 연동 (policy_v4.py)
2026-07-29  §14~16: 매칭 라우터 = 상수함수(β=30만 100% 선택) 확정 → 4β 단독 비교 →
            β=30은 valid→test 낙차 극단(과적합), β=-30이 양 구간 일관 → 배포 β=-30으로 교체
2026-07-29  논문 보강 배치: 다중시드(6→16), DSR, 클린 valid, 앙상블(실패), 베이스라인 6종, EIIE
2026-07-30  DRAFT.md / DRAFT_KR.md 초고 완성. 실계좌 자본금 문제·prev_weights 리셋 버그 해결
2026-08-05  top-K 스윕, TC 스윕, 블록 순열검정, LSRE-CAAN, KOSPI HRL 일반화 노트북 4건
2026-08-06  미국 S&P500 제3의 시장 + architecture confound 통제 실험 (임베딩 vs 원시 가격윈도우)
2026-08-12  제목 확정, 최종 통독 교정 (실제 버그 4건 수정)
2026-08-13  외부 비평 10라운드 검토·반영 (수치 오류가 있는 비평은 원문 대조로 걸러냄)
2026-08-14  λ-스윕(목적함수 β 주입) dose-response 확인, DQN/DDQN 불일치 발견·정정
2026-08-15  DDQN 라우터 재검증 → 동일 붕괴 재현 (알고리즘 탓 아님 확정)
2026-08-18  KOSPI 시간축 불일치 지적 → 프레이밍 재정립, 기여#1을 confound 격리 실험으로 교체
2026-08-19  Point-in-time 13종목 다년 walk-forward 실행 → 5개 관측치 전부 실패 (정직한 부정적 결과)
```

---

## 4. 핵심 결과

### 4.1 아키텍처 캐스케이드 (크립토 44종목, 테스트 2026 H1, TC 0.1%)

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

### 4.2 일관성 우선 기준: 검증(2025 Q4) vs 테스트(2026 H1)

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

### 4.3 강건성 검증 목록 (전부 실행·논문 반영 완료)

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

### 4.4 다중 마켓 분석 (7장)

| 시장 | 설계 | 결과 |
|---|---|---|
| KOSPI 5클러스터 (일봉) | 최종 레시피 축소 이식 (β풀 + 스무딩, top-K 제외) | valid 최선 후보(β=90, α=0.3, Sharpe 1.477)가 test에서 0.137로 참패 → **진단 기준이 배포 후보를 사전에 걸러냄** |
| 미국 S&P500 44종목 | 원시 가격윈도우 | 단일 PPO가 등가중과 동률 — 극적 실패 미재현 |
| 미국 S&P500 (confound 통제) | 같은 시장, Chronos 임베딩으로만 교체 | 턴오버 24배 급증·Sharpe 하락 → **architecture가 실패의 방향, market/레짐이 정도를 설명** |
| 크립토 point-in-time 13종목 (2021~) | 다년 walk-forward | 5개 관측치 전부 격차 >1.6 실패 — 다양성 정상이었는데도 실패 (한계로 정직하게 보고) |

---

## 5. 핵심 교훈 (반복 확인된 것)

1. **거래비용이 1차 용의자** — 비용 전/후를 항상 분리. 대부분의 "실패"는 알파 부재가 아니라 회전 억제 실패였다 (44종목 v1, BTC v1 동일 패턴).
2. **학습은 전권(α=1), 실행에서만 관성** — 추론 시점 스무딩/κ 히스테리시스는 성공, 학습 환경에 관성을 넣으면(v2) credit assignment 붕괴. CAPS(ICRA'21)와 같은 발상이 로봇 제어에선 성공하고 여기선 실패하는 대조 사례.
3. **EarnHFT의 다양성은 Stage I(DP Q-teacher)에서 나온다** — 포트폴리오에선 DP가 조합 폭발로 불가능. β를 샘플링 우선순위로만 쓰면 균등가중으로 수렴(v3, EIIE, LSRE-CAAN 3회 재현). 행동공간 자체를 구조적으로 제약(top-K + 게이트)해야 복원된다.
4. **라우터는 붕괴할 수 있고, 붕괴해도 헤드라인 성적은 좋아 보일 수 있다** — 반드시 "라우터 제거 후 단독 실행"과 소수점 비교로 확인해야 한다. 붕괴 전에 전문가 궤적 다양성을 먼저 검증해 두어야 원인(다양성 부재 vs 라우터 실패)을 구분할 수 있다.
5. **"얼마 벌었나"가 아니라 "일관되게 버는가"** — valid/test 격차 + 양 구간 양의 성과를 이중 기준으로. DSR(다중 시도 보정)과 격차 진단(기간 편향)은 서로 다른 것을 잡는 상호보완 도구.

---

## 6. 디렉토리 구조

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

## 7. 실행 방법

### 7.1 실험 재현 (Colab)

이 프로젝트의 관례: **Colab이 저장소를 마운트하지 않으므로 노트북마다 필요한 코드를 자기완결적으로 포함**한다. 데이터는 Google Drive `졸업프로젝트/data/`에 둔다.

크립토 트랙 순서:
1. `crypto/collect_minute_data_binance.py` → `preprocess_features.py` (로컬, `features_5m/`를 Drive에 업로드)
2. `crypto_hybrid_model_colab.ipynb` → `crypto_hybrid_best.pt`, `crypto_rl_embeddings.h5`
3. `crypto_hrl_earnhft_colab.ipynb` §1~13 (v1~v4) → §14~16 (라우터 붕괴 진단) → §17~22 (스윕·검정·DDQN)
4. 강건성 노트북들 (`crypto_beta_robustness`, `crypto_clean_valid`, `crypto_baselines`, `crypto_eiie_baseline`, `crypto_lsre_caan_baseline`)
5. 다중 마켓: `kospi_hrl_generalization`, `us_equity_hrl_generalization`, `us_equity_embedding_confound`, `crypto_pit_walkforward`

협업 패턴: Colab에서 실행 → 실행된 ipynb를 로컬에 교체 → 출력 파싱해 `paper/` 문서 갱신.

### 7.2 실거래 루프

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

### 7.3 데이터 위치

| 파일 | 위치 | 비고 |
|---|---|---|
| `data/kospi_valid.parquet`, `sequences.h5`, `freq_features.h5`, `rl_embeddings.h5` | Drive `grad_project/data/` | gitignore |
| `crypto/data/minute_ohlcv_raw/`, `features_5m/` (2.5GB) | 로컬 + Drive `졸업프로젝트/data/crypto/` | gitignore |
| `crypto_rl_embeddings.h5`, `crypto_pit_rl_embeddings.h5` | Drive | 노트북이 생성 |
| 모델 가중치 (`agent_beta_*.zip`, 라우터, v1~v3) | Drive; 배포용만 git 화이트리스트 | `.gitignore` 참고 |

---

## 8. 문서 안내 — 어디를 읽어야 하나

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

## 9. 현재 상태와 남은 일 (2026-09 기준)

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
