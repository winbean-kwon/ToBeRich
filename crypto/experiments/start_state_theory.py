"""
[시작 상태 효과 · 닫힌 형태 예측 · 2026-10-27] 관성 정책의 시작 상태 효과를 시장 수익만으로 예측한다.

관성 정책 w_t = (1 − α) w_{t−1} + α · 목표_t 를 노출 x_0 에서 시작하면, 정상 상태 노출 x̄ 와의 차이가 (1 − α)^k 로
줄어든다. 그 차이만큼 기준 바스켓을 더(덜) 들고 있으므로
    시작 효과 ≈ (x_0 − x̄) · Σ_k (1 − α)^k · log(1 + b_k)
    표준편차 ≈ |x_0 − x̄| · σ_b / √(1 − (1 − α)²)
정책 모델 없이 시장 수익 b_k 와 α, x̄ 만으로 계산된다.

이 스크립트는 사후 분석이다(공식은 관측을 본 뒤 유도). 새 정책·시장에 대한 예측은 별도로 사전 등록해 검증한다.
실행: python -m crypto.experiments.start_state_theory
"""

import numpy as np
import pandas as pd

from crypto.experiments.attribution_calibration import load_returns

ROLL = "crypto/notebooks/retrain1006/results/drive/rt1006/start_state_rolling.csv"
ALPHA, XBAR, WIN = 0.01, {"valid": 0.194, "test": 0.094}, 28 * 48   # β=30 워밍업 경로 평균 노출


def main():
    R = load_returns()
    T = R.notna()
    b = np.log1p((R.fillna(0.0) * T).sum(1) / T.sum(1).clip(lower=1))
    roll = pd.read_csv(ROLL)
    pred = []
    for _, r in roll.iterrows():
        bb = b.loc[pd.Timestamp(r["창 시작"]):].iloc[:WIN].to_numpy()
        pred.append((1 - XBAR[r["구간"]]) * ((1 - ALPHA) ** np.arange(len(bb)) * bb).sum())
    roll["예측"] = pred
    obs, p = roll["시작 효과"] * 100, roll["예측"] * 100
    print(f"창 {len(roll)}개: 관측 vs 예측 상관 {np.corrcoef(obs, p)[0, 1]:.3f}, 기울기 {np.polyfit(p, obs, 1)[0]:.2f}, "
          f"평균 |효과| 관측 {obs.abs().mean():.2f} / 예측 {p.abs().mean():.2f} 로그%p")
    roll.to_csv("crypto/experiments/results/start_state_theory.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
