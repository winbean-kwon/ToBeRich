"""
[방법론 2 · 2026-10-26] 라우터 붕괴 사전 진단 — 학습 없이 데이터만으로 계층 RL 라우터의 결과를 예측한다.

입력: 전문가별 블록 수익 R (T, E), 라우터가 블록 시작 시점에 보는 입력 X (T, d), 학습/검증 블록 인덱스.
  D1 분리도   = 평균_t std_e R[t, e] / std_t mean_e R[t, ·]   — 전문가끼리의 차이 / 공통 움직임
  D2 예측가치 = 검증 구간에서 '학습 구간에 맞춘 분류기(X → 다음 블록 최고 전문가)'를 따른 수익
               − '학습 구간 최고 전문가 고정' 수익 (블록당 평균, 비용 제외). 정확도와 최빈 클래스 기준선도 함께 보고.
가설(2×2): D1 낮음 → 붕괴 / D1 높음·D2≤0 → 붕괴 안 하지만 노이즈 전환으로 손해 / D1 높음·D2>0 → 쓸모 있는 라우팅.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def separation(R: np.ndarray) -> float:
    common = R.mean(axis=1)
    return float(R.std(axis=1).mean() / (common.std() + 1e-12))


def predictive_value(R: np.ndarray, X: np.ndarray, tr: np.ndarray, va: np.ndarray, seed: int = 0) -> dict:
    y = R.argmax(axis=1)
    best_fixed = int(R[tr].mean(axis=0).argmax())
    out = {"최고 고정 전문가": best_fixed, "검증 최고 고정 수익/블록": float(R[va, best_fixed].mean())}
    classes = np.unique(y[tr])
    if len(classes) < 2:
        pred = np.full(len(va), classes[0])
    else:
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=2000, C=1.0, random_state=seed).fit(sc.transform(X[tr]), y[tr])
        pred = clf.predict(sc.transform(X[va]))
    majority = np.bincount(y[tr], minlength=R.shape[1]).argmax()
    out.update({
        "분류 정확도": float((pred == y[va]).mean()),
        "최빈 기준 정확도": float((y[va] == majority).mean()),
        "분류기 수익/블록": float(R[va, pred].mean()) if len(va) else np.nan,
        "D2 예측가치": float(R[va, pred].mean() - R[va, best_fixed].mean()),
        "분류기 최빈 선택 비율": float(np.bincount(pred, minlength=R.shape[1]).max() / len(pred)),
    })
    return out


def diagnose(R, X, tr, va) -> dict:
    return {"D1 분리도": separation(R[tr]), **predictive_value(R, X, tr, va)}
