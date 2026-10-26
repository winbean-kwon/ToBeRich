"""
[방법론 1 · 2026-10-26] 반사실 성과 분해 — 포트폴리오 정책의 보고 수익을 어디서 왔는지 층별로 나눈다.

입력은 정책의 '스텝별 보유 목표 비중 경로'와 자산 수익률뿐이라 어떤 포트폴리오 정책(RL이든 규칙이든)에도 쓸 수 있다.
각 층은 반사실 시나리오 하나만 바꾼 차이이고, 로그 성장률(Σ log(1+r))로 계산해 합이 정확히 보고 수익과 일치한다.

  보고(원본 평가)   = 시작 상태 효과 + 워밍업 평가(순)
  워밍업 평가(순)   = 정적 노출 + 노출 타이밍 + 종목 선택 − 거래 비용
    정적 노출    : 기준 바스켓을 정책의 평균 노출로 고정 보유(비용 전)
    노출 타이밍  : 같은 바스켓을 정책의 노출 경로대로 보유 − 정적 노출 (비용 전)
    종목 선택    : 정책(비용 전) − 노출 경로대로 보유한 바스켓 (비용 전)
    거래 비용    : 정책 비용 전 − 비용 후
  선택 층(있을 때만): 실행 제약 = 실행 시뮬레이션 결과 − 워밍업 평가(순), 유니버스 편향 = 보고 − 시점 고정 유니버스 결과

포트폴리오 계산은 이 저장소 백테스트 환경(SparseGatedCryptoPortfolioEnv.step_with_weights)과 같다:
  회전율 = |w_t − 가격 변동 후 w_{t−1}|, 비용 = tc × 회전율, 수익 = w_t·r_t − 비용, 비중 합 < 1이면 나머지는 현금(수익 0).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def portfolio_log_growth(W: np.ndarray, R: np.ndarray, tc: float, init: np.ndarray | None = None) -> tuple[float, float]:
    """(비용 후, 비용 전) 로그 성장률. W·R: (T, N). init: 시작 보유 비중(기본: 전액 현금)."""
    w_prev = np.zeros(W.shape[1]) if init is None else np.asarray(init, dtype=np.float64)
    net = gross = 0.0
    for w, r in zip(W, R):
        pr = float(w @ r)
        cost = tc * float(np.abs(w - w_prev).sum())
        net += np.log1p(pr - cost)
        gross += np.log1p(pr)
        g = 1.0 + pr
        w_prev = w * (1.0 + r) / g if g > 1e-12 else w
    return net, gross


def basket_weights(R: np.ndarray, tradable: np.ndarray, exposure: np.ndarray) -> np.ndarray:
    """거래 가능 종목 등가중 바스켓에 스텝별 노출을 곱한 비중 (T, N)."""
    t = tradable.astype(np.float64)
    n = t.sum(axis=1, keepdims=True)
    return np.where(n > 0, t / np.maximum(n, 1), 0.0) * np.asarray(exposure, dtype=np.float64)[:, None]


def attribute(W_reported: np.ndarray, W_warm: np.ndarray, R: np.ndarray, tradable: np.ndarray, tc: float,
              init_reported: np.ndarray | None = None, executed_log_growth: float | None = None,
              pit_log_growth: float | None = None) -> pd.DataFrame:
    """보고 수익을 층별로 분해한 표(로그 성장률과 근사 % 기여)."""
    rep_net, _ = portfolio_log_growth(W_reported, R, tc, init_reported)
    warm_net, warm_gross = portfolio_log_growth(W_warm, R, tc)
    x = W_warm.sum(axis=1)
    _, static = portfolio_log_growth(basket_weights(R, tradable, np.full(len(x), x.mean())), R, 0.0)
    _, path = portfolio_log_growth(basket_weights(R, tradable, x), R, 0.0)
    rows = [
        ("보고 수익(원본 평가)", rep_net),
        ("  시작 상태 효과", rep_net - warm_net),
        ("  워밍업 평가(순)", warm_net),
        ("    정적 노출", static),
        ("    노출 타이밍", path - static),
        ("    종목 선택", warm_gross - path),
        ("    거래 비용", warm_net - warm_gross),
    ]
    if executed_log_growth is not None:
        rows.append(("  (선택) 실행 제약", executed_log_growth - warm_net))
    if pit_log_growth is not None:
        rows.append(("  (선택) 유니버스 편향", rep_net - pit_log_growth))
    df = pd.DataFrame(rows, columns=["층", "로그 성장률"])
    df["근사 %p"] = np.expm1(df["로그 성장률"]) * 100
    df.attrs["평균 노출"] = float(x.mean())
    # 항등식 확인: 하위 층의 합이 상위 값과 정확히 같아야 한다
    assert abs((static + (path - static) + (warm_gross - path) + (warm_net - warm_gross)) - warm_net) < 1e-9
    return df
