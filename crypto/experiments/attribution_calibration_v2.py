"""
[방법론 1 보강 · 보정 실험 2차 · 2026-10-26] 실제 정책처럼 느리게 움직이는 합성 정책으로 위약 검정을 다시 검증한다.

1차(attribution_calibration)의 결함: 합성 정책이 한 층만 가져 다른 층이 정확히 0이었고(판정이 퇴화), 매 스텝 독립으로
움직여 실제 정책(α = 0.01 스무딩, 노출이 며칠에 걸쳐 변함)과 달랐다. 위약 검정이 자기상관이 긴 경로에서도
명목 수준을 지키는지가 핵심 질문이므로 이를 고친다.

사전 등록(실행 전 커밋):
  데이터·구간: 1차와 동일(44종목 30분 수익률, 검증 3개월 2025-10~12, 테스트 2026-01-01~07-12).
  실력 기준: 다음 1일(48스텝) 누적 로그 수익. ρ = 그 수익과 신호의 상관(IC).
  합성 정책(매 스텝 목표를 만들고 실제 보유는 w_t = (1 − α) w_{t−1} + α · 목표_t, α = 0.01, 거래 불가 종목은 0):
    목표 노출 = clip(0.4 + 0.2 · s_t, 0, 1),  s_t = ρ_T · z(바스켓 1일 선행 수익) + √(1−ρ_T²) · ε_t
    목표 구성 = 점수 상위 10종목 등가중, 점수_i = ρ_S · z_cs(종목 1일 선행 수익) + √(1−ρ_S²) · ε_i
    두 층 모두 늘 움직이므로 어느 층도 퇴화하지 않는다.
  설계: 귀무(ρ_T = ρ_S = 0) / 타이밍만(ρ_T = ρ, ρ_S = 0) / 선택만(ρ_T = 0, ρ_S = ρ), ρ ∈ {0.02, 0.05, 0.1, 0.2, 0.3}.
        각 칸 정책 100개, 위약 199개, 단측 α = 0.05.
  판정:
    타당성 통과 = 귀무 설계에서 두 층·두 구간 기각률 모두 ∈ [0.01, 0.10]
    분리 통과   = 단일 실력 설계에서 심지 않은 층의 기각률이 모든 ρ에서 ≤ 0.10
    검출 가능 최소 IC = 심은 층의 기각률 ≥ 0.8인 가장 작은 ρ (구간·층별)

실행: python -m crypto.experiments.attribution_calibration_v2 → results/attribution_calibration_v2.csv
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from crypto.experiments.attribution_calibration import WINDOWS, load_returns
from crypto.experiments.attribution_inference import layers, placebo_null, placebo_p

OUT = __import__("pathlib").Path(__file__).resolve().parent / "results" / "attribution_calibration_v2.csv"
ALPHA, X_BAR, SCALE, TOP, H = 0.01, 0.4, 0.2, 10, 48
RHOS = [0.02, 0.05, 0.1, 0.2, 0.3]
N_POLICY, N_PLACEBO = 100, 199


def forward(R: np.ndarray, h: int = H) -> np.ndarray:
    """스텝 t부터 h스텝 누적 로그 수익 (끝부분은 남은 스텝까지)."""
    lr = np.log1p(R)
    c = np.concatenate([np.zeros((1,) + lr.shape[1:]), np.cumsum(lr, axis=0)], axis=0)
    S = len(R)
    end = np.minimum(np.arange(S) + h, S)
    return c[end] - c[np.arange(S)]


def zscore(v: np.ndarray) -> np.ndarray:
    return (v - v.mean()) / (v.std() + 1e-12)


def synth(rho_t: float, rho_s: float, R, T, F_bask, F_cs, rng) -> np.ndarray:
    S, N = R.shape
    s = rho_t * zscore(F_bask) + np.sqrt(1 - rho_t ** 2) * rng.standard_normal(S)
    x_tgt = np.clip(X_BAR + SCALE * s, 0, 1)
    score = rho_s * F_cs + np.sqrt(1 - rho_s ** 2) * rng.standard_normal((S, N))
    score = np.where(T, score, -np.inf)
    top = np.argsort(-score, axis=1)[:, :TOP]
    tgt = np.zeros((S, N))
    tgt[np.arange(S)[:, None], top] = 1.0
    tgt *= T
    tgt = tgt / np.maximum(tgt.sum(1, keepdims=True), 1) * x_tgt[:, None]
    W = np.empty((S, N))
    w = tgt[0].copy()
    for t in range(S):
        w = (1 - ALPHA) * w + ALPHA * tgt[t]
        w = w * T[t]
        W[t] = w
    return W


def main():
    Rdf = load_returns()
    rows = []
    designs = [("귀무", 0.0, 0.0)] + [("타이밍만", r, 0.0) for r in RHOS] + [("선택만", 0.0, r) for r in RHOS]
    for wname, (a, b) in WINDOWS.items():
        sub = Rdf.loc[a:b]
        T = sub.notna().to_numpy()
        R = sub.fillna(0.0).to_numpy()
        t = T.astype(float)
        ew = t / np.maximum(t.sum(1, keepdims=True), 1)
        F_bask = forward((R * ew).sum(1))
        Fa = np.where(T, forward(R), np.nan)
        F_cs = np.nan_to_num((Fa - np.nanmean(Fa, 1, keepdims=True)) / (np.nanstd(Fa, 1, keepdims=True) + 1e-12))
        for j, (dname, rt, rs) in enumerate(designs):
            rng = np.random.default_rng(1000 * j + (wname == "테스트 6개월"))
            for i in range(N_POLICY):
                W = synth(rt, rs, R, T, F_bask, F_cs, rng)
                L = layers(W, R, T)
                null = placebo_null(W, R, T, n=N_PLACEBO, seed=i)
                rows.append({"구간": wname, "설계": dname, "ρ_T": rt, "ρ_S": rs, "정책": i,
                             "타이밍 층": L["노출 타이밍"], "선택 층": L["종목 선택"],
                             "타이밍 p": placebo_p(L["노출 타이밍"], null["노출 타이밍"]),
                             "선택 p": placebo_p(L["종목 선택"], null["종목 선택"])})
            d = pd.DataFrame(rows[-N_POLICY:])
            print(f"{wname} {dname} ρ_T={rt} ρ_S={rs}: 기각률 타이밍 {np.mean(d['타이밍 p'] < 0.05):.2f} "
                  f"선택 {np.mean(d['선택 p'] < 0.05):.2f} | 평균 층 타이밍 {d['타이밍 층'].mean()*100:+.2f} "
                  f"선택 {d['선택 층'].mean()*100:+.2f} 로그%p", flush=True)
    res = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT, index=False, encoding="utf-8-sig")

    rej = res.assign(타이밍=res["타이밍 p"] < 0.05, 선택=res["선택 p"] < 0.05) \
             .groupby(["구간", "설계", "ρ_T", "ρ_S"])[["타이밍", "선택"]].mean()
    print("\n기각률(α=0.05)\n" + rej.round(2).to_string())
    null = rej.xs("귀무", level="설계")
    ok_size = bool(((null >= 0.01) & (null <= 0.10)).all().all())
    cross = pd.concat([rej.xs("타이밍만", level="설계")["선택"], rej.xs("선택만", level="설계")["타이밍"]])
    ok_sep = bool((cross <= 0.10).all())
    print(f"\n[사전 등록 판정] 타당성: {'통과' if ok_size else '실패'} | 분리: {'통과' if ok_sep else '실패'}")
    for wname in WINDOWS:
        for dname, col, lvl in (("타이밍만", "타이밍", "ρ_T"), ("선택만", "선택", "ρ_S")):
            r = rej.xs((wname, dname), level=["구간", "설계"])[col]
            r.index = r.index.get_level_values(lvl)
            hit = r[r >= 0.8]
            print(f"  검출 가능 최소 IC(1일) — {wname} {col}: {hit.index.min() if len(hit) else '격자 안에 없음(>0.3)'}")
    print("저장:", OUT)


if __name__ == "__main__":
    sys.exit(main())
