"""
[방법론 1 보강 · 2026-10-26] 분해 층의 통계적 추론 — 위약(placebo) 정책 귀무분포, 블록 bootstrap 신뢰구간, 순서 민감도.

attribution.py는 보고 수익을 층으로 '나누기'만 한다. 이 모듈은 각 층이 잡음과 구분되는지를 묻는다.
핵심 아이디어: 정책의 성질(노출 수준·노출 변동·집중도·회전율)은 그대로 두고 '언제 무엇을 들고 있었는지'의
시점 정렬만 깨뜨린 위약 정책을 만들어, 그 위약들이 우연히 얻는 층 값의 분포를 귀무분포로 쓴다.

  노출 타이밍 위약 : 노출 경로 x_t 를 원형으로 시간 이동 (평균·분포·자기상관 유지, 수익과의 정렬만 깨짐)
  종목 선택 위약   : 상대 비중 w_t / x_t 를 원형으로 시간 이동하고 실제 노출 x_t 를 곱함
                     (노출 경로·집중도·종목 교체 속도 유지, 어느 종목을 언제 들었는지만 깨짐)

층 정의는 attribution.py와 같다(비용 전 로그 성장률, 비용 전에는 경로 의존이 없어 스텝별 합으로 계산된다):
  정적 노출   = Σ log(1 + x̄ · b_t)          b_t = 거래 가능 종목 등가중 수익
  노출 타이밍 = Σ log(1 + x_t · b_t) − 정적 노출
  종목 선택   = Σ log(1 + w_t · r_t) − Σ log(1 + x_t · b_t)
순서 민감도: '선택 먼저' 순서 = 상대 비중을 평균 노출 x̄로 고정해 보유한 경로를 중간 단계로 쓴다.
  선택(선택 먼저) = Σ log(1 + x̄ · ρ_t · r_t) − 정적,  타이밍(선택 먼저) = 정책 − Σ log(1 + x̄ · ρ_t · r_t)
  두 순서의 평균이 2자 Shapley 값이다.
"""

from __future__ import annotations

import numpy as np

STEPS_PER_DAY = 48
MIN_SHIFT = 7 * STEPS_PER_DAY   # 위약 이동량 하한(1주) — 이동 0 근처는 원래 정책과 거의 같아 귀무가 아니다
BLOCK = 7 * STEPS_PER_DAY       # bootstrap 블록 길이(1주) — 노출이 느리게 움직여 층 차이 계열의 자기상관이 길다


def basket_return(R: np.ndarray, T: np.ndarray) -> np.ndarray:
    """거래 가능 종목 등가중 수익 b_t (T,)."""
    t = T.astype(np.float64)
    n = t.sum(axis=1)
    return np.where(n > 0, (R * t).sum(axis=1) / np.maximum(n, 1), 0.0)


def relative_weights(W: np.ndarray, T: np.ndarray) -> np.ndarray:
    """ρ_t = w_t / x_t (합 1). 노출이 0인 스텝은 거래 가능 종목 등가중."""
    x = W.sum(axis=1, keepdims=True)
    t = T.astype(np.float64)
    ew = t / np.maximum(t.sum(axis=1, keepdims=True), 1)
    return np.where(x > 1e-12, W / np.maximum(x, 1e-12), ew)


def remask(rel: np.ndarray, T: np.ndarray) -> np.ndarray:
    """이동한 상대 비중에서 지금 거래 불가인 종목을 빼고 합 1로 다시 맞춘다(전부 불가면 등가중)."""
    t = T.astype(np.float64)
    m = rel * t
    s = m.sum(axis=1, keepdims=True)
    ew = t / np.maximum(t.sum(axis=1, keepdims=True), 1)
    return np.where(s > 1e-12, m / np.maximum(s, 1e-12), ew)


def step_series(W: np.ndarray, R: np.ndarray, T: np.ndarray) -> dict[str, np.ndarray]:
    """층 계산에 쓰는 스텝별 비용 전 로그 수익 계열."""
    x = W.sum(axis=1)
    b = basket_return(R, T)
    rho = relative_weights(W, T)
    xb = x.mean()
    return {
        "policy": np.log1p((W * R).sum(axis=1)),
        "path": np.log1p(x * b),
        "static": np.log1p(xb * b),
        "sel_first": np.log1p(xb * (rho * R).sum(axis=1)),
    }


def layers(W: np.ndarray, R: np.ndarray, T: np.ndarray) -> dict[str, float]:
    s = {k: v.sum() for k, v in step_series(W, R, T).items()}
    timing, selection = s["path"] - s["static"], s["policy"] - s["path"]
    sel_f, tim_f = s["sel_first"] - s["static"], s["policy"] - s["sel_first"]
    return {
        "정적 노출": s["static"], "노출 타이밍": timing, "종목 선택": selection,
        "타이밍(선택 먼저)": tim_f, "선택(선택 먼저)": sel_f,
        "타이밍 Shapley": (timing + tim_f) / 2, "선택 Shapley": (selection + sel_f) / 2,
        "상호작용": timing - tim_f,
    }


def placebo_null(W: np.ndarray, R: np.ndarray, T: np.ndarray, n: int = 1000, seed: int = 0) -> dict[str, np.ndarray]:
    """위약 정책 n개의 노출 타이밍·종목 선택 층 값."""
    rng = np.random.default_rng(seed)
    S = len(W)
    if S <= 2 * MIN_SHIFT:
        raise ValueError(f"구간이 너무 짧다: {S} 스텝")
    x = W.sum(axis=1)
    b = basket_return(R, T)
    rho = relative_weights(W, T)
    static = np.log1p(x.mean() * b).sum()
    shifts = rng.integers(MIN_SHIFT, S - MIN_SHIFT, size=n)
    tim, sel = np.empty(n), np.empty(n)
    for i, k in enumerate(shifts):
        xs = np.roll(x, k)
        path_s = np.log1p(xs * b).sum()
        tim[i] = path_s - static
        rs = remask(np.roll(rho, k, axis=0), T)
        path_x = np.log1p(x * b).sum()
        sel[i] = np.log1p(x * (rs * R).sum(axis=1)).sum() - path_x
    return {"노출 타이밍": tim, "종목 선택": sel, "shifts": shifts}


def placebo_p(observed: float, null: np.ndarray) -> float:
    """단측 p = (1 + #{null ≥ observed}) / (1 + n)."""
    return float((1 + np.sum(null >= observed)) / (1 + len(null)))


def block_bootstrap_ci(W: np.ndarray, R: np.ndarray, T: np.ndarray, n: int = 2000, block: int = BLOCK,
                       level: float = 0.95, seed: int = 0) -> dict[str, tuple[float, float]]:
    """원형 블록 bootstrap으로 층 값의 신뢰구간. 스텝별 층 차이 계열을 같은 블록 인덱스로 함께 재표집한다."""
    s = step_series(W, R, T)
    d = {"정적 노출": s["static"], "노출 타이밍": s["path"] - s["static"], "종목 선택": s["policy"] - s["path"]}
    S = len(W)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(S / block))
    out = {k: np.empty(n) for k in d}
    for i in range(n):
        starts = rng.integers(0, S, size=nb)
        idx = ((starts[:, None] + np.arange(block)[None, :]) % S).ravel()[:S]
        for k, v in d.items():
            out[k][i] = v[idx].sum()
    a = (1 - level) / 2
    return {k: (float(np.quantile(v, a)), float(np.quantile(v, 1 - a))) for k, v in out.items()}


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm 보정 p값."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for j, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - j) * p))
        out[k] = run
    return out
