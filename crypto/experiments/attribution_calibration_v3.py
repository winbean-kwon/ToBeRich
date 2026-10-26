"""
[방법론 1 보강 · 보정 실험 3차 · 2026-10-26] 2차와 같은 설계에서 합성 정책의 시작 보유만 정상 상태 평균으로 바꾼다.

2차(attribution_calibration_v2) 실패: 귀무 기각률 3개월 0.19/0.13, 6개월 0.14/0.09.
추정 원인: 합성 정책이 첫 스텝 목표 비중에서 출발해 α = 0.01로 수렴한다. 시작 과도 구간의 노출 편차(sd ≈ 0.2)가
정상 상태(sd ≈ 0.014)보다 훨씬 커서 위약(시간 이동)이 이 구간을 다른 시점으로 옮기면 교환 가능성이 깨진다.
즉 평가 시작 상태 편향이 검정에도 들어간다. 실제 정책 적용은 2주 워밍업 경로를 쓰므로, 보정도 그 조건을 맞춘다.

사전 등록(실행 전 커밋): 2차에서 바꾸는 것은 한 가지뿐이다 —
  시작 보유 w_0 = 0.4 × (t=0 거래 가능 종목 등가중)  (합성 목표 비중의 정상 상태 평균, 미래 정보 없음).
  나머지(데이터·구간·합성 규칙·ρ 격자·정책 100개·위약 199개·판정 규칙)는 2차와 동일. 난수 시드만 새로 쓴다(+5000).
  판정도 2차와 동일: 타당성 = 귀무 기각률 ∈ [0.01, 0.10](두 층·두 구간), 분리 = 심지 않은 층 기각률 ≤ 0.10.
  3차도 실패하면 위약 검정은 '실패'로 기록하고 더 고치지 않는다.

실행: python -m crypto.experiments.attribution_calibration_v3 → results/attribution_calibration_v3.csv
"""

from __future__ import annotations

import sys

import numpy as np

from crypto.experiments import attribution_calibration_v2 as V2


def synth(rho_t, rho_s, R, T, F_bask, F_cs, rng):
    S, N = R.shape
    s = rho_t * V2.zscore(F_bask) + np.sqrt(1 - rho_t ** 2) * rng.standard_normal(S)
    x_tgt = np.clip(V2.X_BAR + V2.SCALE * s, 0, 1)
    score = rho_s * F_cs + np.sqrt(1 - rho_s ** 2) * rng.standard_normal((S, N))
    score = np.where(T, score, -np.inf)
    top = np.argsort(-score, axis=1)[:, :V2.TOP]
    tgt = np.zeros((S, N))
    tgt[np.arange(S)[:, None], top] = 1.0
    tgt *= T
    tgt = tgt / np.maximum(tgt.sum(1, keepdims=True), 1) * x_tgt[:, None]
    W = np.empty((S, N))
    t0 = T[0].astype(float)
    w = V2.X_BAR * t0 / max(t0.sum(), 1)          # 유일한 변경: 정상 상태 평균에서 시작
    for t in range(S):
        w = (1 - V2.ALPHA) * w + V2.ALPHA * tgt[t]
        w = w * T[t]
        W[t] = w
    return W


if __name__ == "__main__":
    V2.synth = synth
    V2.OUT = V2.OUT.with_name("attribution_calibration_v3.csv")
    _rng = np.random.default_rng
    V2.np.random.default_rng = lambda seed=None: _rng(None if seed is None else seed + 5000)
    sys.exit(V2.main())
