"""
[방법론 1 보강 · 보정 실험 · 2026-10-26] 정답을 아는 합성 정책으로 위약 검정을 검증하고, 검출 가능한 최소 실력을 잰다.

질문 1(타당성): 실력이 없는 정책(IC = 0)에 대해 위약 검정이 '유의'라고 잘못 말하는 비율이 명목 5% 근처인가?
질문 2(검정력): 실제 44종목 30분 수익률에서, 3개월(검증 구간)·6개월(테스트 구간) 평가로 어느 정도 실력부터 잡히는가?
질문 3(분리): 타이밍 실력만 심은 정책의 선택 층, 선택 실력만 심은 정책의 타이밍 층이 잘못 유의해지지 않는가?

사전 등록(실행 전 커밋):
  데이터: crypto/data/features_5m 의 live_universe 44종목 5분봉 종가 → 30분 종가. r_t = 다음 30분 수익률.
          거래 가능 = t와 t+1 종가가 모두 있는 종목.
  구간: 검증 2025-10-01~2025-12-31(3개월), 테스트 2026-01-01~2026-07-12(약 6개월, 로컬 데이터 끝).
  합성 정책(평균 노출 x̄ = 0.4, 실력 ρ = 스텝당 IC):
    타이밍형: x_t = clip(x̄ + 0.2 · s_t, 0, 1), s_t = ρ · b_t/sd(b) + √(1−ρ²) · ε_t, 비중 = x_t × 거래 가능 등가중
    선택형:   x_t = x̄, 점수_i = ρ · z_cs(r_t,i) + √(1−ρ²) · ε_i, 상위 10종목 등가중 × x̄
  ρ 격자: 0, 0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12. 각 (유형, 구간, ρ)마다 정책 100개, 위약 199개.
  검정: attribution_inference.placebo_null / placebo_p, 단측 α = 0.05.
  판정:
    타당성 통과 = ρ = 0에서 두 층·두 구간 모두 기각률 ∈ [0.01, 0.10]
    분리 통과   = 모든 ρ에서 '심지 않은 층'의 기각률 ≤ 0.10
    검출 가능 최소 IC = 기각률 ≥ 0.8인 가장 작은 ρ (구간·층별 보고)

실행: python -m crypto.experiments.attribution_calibration → crypto/experiments/results/attribution_calibration.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from crypto.experiments.attribution_inference import layers, placebo_null, placebo_p

ROOT = Path(__file__).resolve().parents[2]
FEAT = ROOT / "crypto" / "data" / "features_5m"
OUT = ROOT / "crypto" / "experiments" / "results" / "attribution_calibration.csv"
WINDOWS = {"검증 3개월": ("2025-10-01", "2025-12-31 23:59"), "테스트 6개월": ("2026-01-01", "2026-07-12 23:59")}
X_BAR, TIMING_SCALE, TOP = 0.4, 0.2, 10
RHOS = [0.0, 0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12]
N_POLICY, N_PLACEBO = 100, 199


def load_returns():
    syms = [s.split("/")[0] for s in json.loads((ROOT / "crypto" / "data" / "live_universe.json").read_text())]
    cols = {}
    for s in syms:
        d = pd.read_parquet(FEAT / f"{s}USDT.parquet", columns=["datetime", "close"])
        d = d[pd.to_datetime(d["datetime"], utc=True) >= pd.Timestamp("2025-09-25", tz="UTC")]
        cols[s] = d.set_index(pd.to_datetime(d["datetime"], utc=True))["close"].astype(float).resample("30min").last()
    P = pd.DataFrame(cols).sort_index()
    R = P.shift(-1) / P - 1
    return R


def synth(kind: str, rho: float, R: np.ndarray, T: np.ndarray, rng) -> np.ndarray:
    S, N = R.shape
    t = T.astype(np.float64)
    ew = t / np.maximum(t.sum(1, keepdims=True), 1)
    if kind == "타이밍":
        b = (R * ew).sum(1)
        s = rho * b / b.std() + np.sqrt(1 - rho ** 2) * rng.standard_normal(S)
        x = np.clip(X_BAR + TIMING_SCALE * s, 0, 1)
        return ew * x[:, None]
    Rm = np.where(T, R, np.nan)
    z = (Rm - np.nanmean(Rm, 1, keepdims=True)) / (np.nanstd(Rm, 1, keepdims=True) + 1e-12)
    score = rho * np.nan_to_num(z) + np.sqrt(1 - rho ** 2) * rng.standard_normal((S, N))
    score = np.where(T, score, -np.inf)
    W = np.zeros((S, N))
    top = np.argsort(-score, axis=1)[:, :TOP]
    rows = np.arange(S)[:, None]
    W[rows, top] = 1.0
    W *= T
    return W / np.maximum(W.sum(1, keepdims=True), 1) * X_BAR


def main():
    Rdf = load_returns()
    rows = []
    for wname, (a, b) in WINDOWS.items():
        sub = Rdf.loc[a:b]
        T = sub.notna().to_numpy()
        R = sub.fillna(0.0).to_numpy()
        print(f"{wname}: {len(sub)} 스텝, 평균 거래 가능 {T.sum(1).mean():.1f}종목", flush=True)
        for kind in ("타이밍", "선택"):
            for rho in RHOS:
                rng = np.random.default_rng(int(rho * 10000) * 7 + (kind == "선택"))
                for i in range(N_POLICY):
                    W = synth(kind, rho, R, T, rng)
                    L = layers(W, R, T)
                    null = placebo_null(W, R, T, n=N_PLACEBO, seed=i)
                    rows.append({"구간": wname, "유형": kind, "ρ": rho, "정책": i,
                                 "타이밍 층": L["노출 타이밍"], "선택 층": L["종목 선택"],
                                 "타이밍 p": placebo_p(L["노출 타이밍"], null["노출 타이밍"]),
                                 "선택 p": placebo_p(L["종목 선택"], null["종목 선택"])})
                d = pd.DataFrame(rows[-N_POLICY:])
                print(f"  {kind} ρ={rho:.2f}: 기각률 타이밍 {np.mean(d['타이밍 p'] < 0.05):.2f} "
                      f"선택 {np.mean(d['선택 p'] < 0.05):.2f} | 평균 층 타이밍 {d['타이밍 층'].mean()*100:+.2f} "
                      f"선택 {d['선택 층'].mean()*100:+.2f} 로그%p", flush=True)
    res = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT, index=False, encoding="utf-8-sig")

    rej = res.assign(타이밍=res["타이밍 p"] < 0.05, 선택=res["선택 p"] < 0.05).groupby(["구간", "유형", "ρ"])[["타이밍", "선택"]].mean()
    print("\n기각률(α=0.05)\n" + rej.round(2).to_string())
    size = rej.xs(0.0, level="ρ")
    ok_size = bool(((size >= 0.01) & (size <= 0.10)).all().all())
    cross = pd.concat([rej.xs("타이밍", level="유형")["선택"], rej.xs("선택", level="유형")["타이밍"]])
    ok_sep = bool((cross <= 0.10).all())
    print(f"\n[사전 등록 판정] 타당성(ρ=0 기각률 ∈ [0.01, 0.10]): {'통과' if ok_size else '실패'} | "
          f"분리(심지 않은 층 기각률 ≤ 0.10): {'통과' if ok_sep else '실패'}")
    for wname in WINDOWS:
        for kind, col in (("타이밍", "타이밍"), ("선택", "선택")):
            r = rej.loc[(wname, kind)][col]
            hit = r[r >= 0.8]
            print(f"  검출 가능 최소 IC — {wname} {kind}: {hit.index.min() if len(hit) else '격자 안에 없음(>0.12)'}")
    print("저장:", OUT)


if __name__ == "__main__":
    sys.exit(main())
