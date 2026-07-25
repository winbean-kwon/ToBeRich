"""
EarnHFT(Qin et al. 2024) Algorithm 3(Market Segmentation & Labelling) 이식.

가격/지수 곡선을 저역통과 필터링 → 극값 기준 초기 분할 → 인접 구간을
기울기 유사도 + DTW 형태 유사도로 반복 병합 → 기울기 분위수 기준
레짐 라벨(기본 5단계: bear/pullback/sideways/rally/bull) 부여.

원 논문은 초단위 LOB 데이터를 다루지만 여기서는 30분 버킷 단위 크립토
포트폴리오 지수(등가중 또는 단일 자산)에 적용한다. DTW는 외부 패키지
의존 없이 표준 O(n*m) 동적계획법으로 직접 구현했다 — 병합 대상 구간이
짧아(수십~수백 버킷) 성능 문제가 없고 Colab/로컬 모두 설치 없이 동작한다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

REGIME_NAMES = {1: "bear", 2: "pullback", 3: "sideways", 4: "rally", 5: "bull"}
_DTW_MAX_LEN = 200  # 병합이 진행되며 구간이 길어져도 DTW 비용을 상한 이하로 유지


@dataclass
class MarketSegments:
    labels: pd.Series    # 원본 인덱스 그대로, 값은 1..n_labels (레짐 라벨)
    chunks: pd.DataFrame  # columns: start_idx, end_idx, length, slope, label, regime, start, end


def _zscore(x: np.ndarray) -> np.ndarray:
    std = x.std()
    return (x - x.mean()) / std if std > 1e-12 else np.zeros_like(x)


def _downsample(x: np.ndarray, max_len: int = _DTW_MAX_LEN) -> np.ndarray:
    if len(x) <= max_len:
        return x
    idx = np.linspace(0, len(x) - 1, max_len).round().astype(int)
    return x[idx]


def _dtw_distance(a: np.ndarray, b: np.ndarray) -> float:
    """표준 DTW 거리(유클리드 로컬 비용, 대각/수평/수직 이동만 허용)."""
    a, b = _downsample(a), _downsample(b)
    n, m = len(a), len(b)
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0.0
    for i in range(1, n + 1):
        ai = a[i - 1]
        row, prev = cost[i], cost[i - 1]
        for j in range(1, m + 1):
            row[j] = abs(ai - b[j - 1]) + min(prev[j], row[j - 1], prev[j - 1])
    return float(cost[n, m])


def _slope(x: np.ndarray) -> float:
    """구간 buy&hold 순자산 곡선의 선형회귀 기울기(구간 길이로 정규화)."""
    if len(x) < 2:
        return 0.0
    t = np.arange(len(x), dtype=np.float64)
    a, _ = np.polyfit(t, x, 1)
    return float(a)


def _find_extrema_indices(x: np.ndarray) -> np.ndarray:
    """1차 차분 부호가 바뀌는 지점(국소 극값) + 시작/끝 인덱스."""
    d = np.diff(x)
    sign = np.sign(d)
    sign[sign == 0] = 1  # 평탄 구간은 이전 부호를 유지하는 것으로 취급
    change = np.where(np.diff(sign) != 0)[0] + 1  # diff 인덱스를 x 인덱스로 보정
    idx = np.concatenate(([0], change, [len(x) - 1]))
    return np.unique(idx)


def _merge_pass(x: np.ndarray, bounds: list[int], merge_quantile: float) -> tuple[list[int], bool]:
    """인접 구간 쌍을 기울기차/DTW거리 분위수 기준으로 한 패스만큼 병합."""
    if len(bounds) <= 2:
        return bounds, False

    seg_ranges = list(zip(bounds[:-1], bounds[1:]))
    slopes = [_slope(x[a:b + 1]) for a, b in seg_ranges]
    if len(seg_ranges) < 2:
        return bounds, False

    slope_diffs = [abs(slopes[i + 1] - slopes[i]) for i in range(len(slopes) - 1)]
    dtw_dists = [
        _dtw_distance(
            _zscore(x[seg_ranges[i][0]:seg_ranges[i][1] + 1]),
            _zscore(x[seg_ranges[i + 1][0]:seg_ranges[i + 1][1] + 1]),
        )
        for i in range(len(seg_ranges) - 1)
    ]
    slope_thresh = np.quantile(slope_diffs, merge_quantile)
    dtw_thresh = np.quantile(dtw_dists, merge_quantile)

    new_bounds = [bounds[0]]
    merged_any = False
    i = 0
    while i < len(seg_ranges):
        can_merge = (
            i < len(seg_ranges) - 1
            and slope_diffs[i] <= slope_thresh
            and dtw_dists[i] <= dtw_thresh
        )
        if can_merge:
            new_bounds.append(seg_ranges[i + 1][1])
            merged_any = True
            i += 2
        else:
            new_bounds.append(seg_ranges[i][1])
            i += 1
    return new_bounds, merged_any


def _absorb_short_segments(x: np.ndarray, bounds: list[int], min_length: int) -> list[int]:
    """min_length보다 짧은 잔여 구간을 기울기가 더 가까운 이웃 쪽으로 흡수한다."""
    while len(bounds) > 2:
        seg_ranges = list(zip(bounds[:-1], bounds[1:]))
        lengths = [b - a + 1 for a, b in seg_ranges]
        shortest = int(np.argmin(lengths))
        if lengths[shortest] >= min_length:
            break

        slopes = [_slope(x[a:b + 1]) for a, b in seg_ranges]
        left_diff = abs(slopes[shortest] - slopes[shortest - 1]) if shortest > 0 else np.inf
        right_diff = (
            abs(slopes[shortest] - slopes[shortest + 1]) if shortest < len(seg_ranges) - 1 else np.inf
        )
        drop_idx = shortest if left_diff <= right_diff else shortest + 1
        bounds = bounds[:drop_idx] + bounds[drop_idx + 1:]
    return bounds


def segment_and_label(
    series: pd.Series,
    n_labels: int = 5,
    risk_threshold: float = 0.2,
    lowpass_window: int = 48,
    merge_quantile: float = 0.35,
    max_merge_iters: int = 50,
    min_segment_length: int | None = None,
) -> MarketSegments:
    """
    가격/지수 시계열을 레짐 구간으로 분할하고 라벨을 부여한다 (EarnHFT Algorithm 3 이식).

    가격 대신 **로그가격**(buy&hold 순자산 곡선의 로그, EarnHFT의 "B&H net curve"에
    대응)을 기준으로 극값 탐색·기울기·DTW를 계산한다 — 원시 가격 기준으로 하면
    같은 %등락이라도 가격 레벨이 높은 구간(예: 강세장 후반)의 기울기가 기계적으로
    커져 레짐 분류가 가격 스케일에 왜곡되기 때문이다.

    Parameters
    ----------
    series : 시간순 정렬된 가격(양수) 곡선 (인덱스는 버킷 정수 또는 datetime)
    n_labels : 레짐 라벨 개수 (기본 5: bear~bull)
    risk_threshold : 상/하위 라벨 경계를 나누는 분위수 폭 θ (EarnHFT 표기와 동일)
    lowpass_window : 노이즈 제거용 중심 이동평균 윈도우(버킷 수). 기본 48버킷(=1일,
        30분 버킷 기준)로 시간 단위 미시 변동이 아닌 일 단위 이상의 레짐을 잡는다
    merge_quantile : 매 병합 패스에서 병합할 인접쌍의 분위수 비율
    max_merge_iters : 병합 패스 최대 반복 횟수(안전장치)
    min_segment_length : 병합 후에도 남은 min_segment_length 미만의 잔여 구간을
        이웃으로 흡수. 기본값은 lowpass_window와 동일
    """
    x_raw = series.to_numpy(dtype=np.float64)
    if len(x_raw) < 3:
        raise ValueError("series가 너무 짧습니다 (최소 3개 포인트 필요)")
    if np.any(x_raw <= 0):
        raise ValueError("series는 로그 변환을 위해 모두 양수여야 합니다")

    x_log = np.log(x_raw)
    x_smooth = (
        pd.Series(x_log).rolling(lowpass_window, min_periods=1, center=True).mean().to_numpy()
    )

    bounds = _find_extrema_indices(x_smooth).tolist()
    for _ in range(max_merge_iters):
        bounds, merged = _merge_pass(x_smooth, bounds, merge_quantile)
        if not merged or len(bounds) <= 2:
            break

    bounds = _absorb_short_segments(x_log, bounds, min_segment_length or lowpass_window)

    seg_ranges = list(zip(bounds[:-1], bounds[1:]))
    slopes = np.array([_slope(x_log[a:b + 1]) for a, b in seg_ranges])

    theta = risk_threshold
    H = np.quantile(slopes, 1 - theta / 2)
    L = np.quantile(slopes, theta / 2)

    labels = np.empty(len(slopes), dtype=np.int64)
    for i, s in enumerate(slopes):
        if s > H:
            labels[i] = n_labels
        elif s < L:
            labels[i] = 1
        elif H > L:
            frac = (s - L) / (H - L)
            labels[i] = int(np.clip(2 + frac * (n_labels - 2), 2, n_labels - 1))
        else:
            labels[i] = (n_labels + 1) // 2  # H==L (거의 무변동 시계열) → 중립 라벨

    per_point_labels = np.empty(len(x_raw), dtype=np.int64)
    for (a, b), lbl in zip(seg_ranges, labels):
        per_point_labels[a:b + 1] = lbl

    labels_series = pd.Series(per_point_labels, index=series.index, name="regime_label")

    chunks = pd.DataFrame({
        "start_idx": [a for a, _ in seg_ranges],
        "end_idx": [b for _, b in seg_ranges],
        "length": [b - a + 1 for a, b in seg_ranges],
        "slope": slopes,
        "label": labels,
    })
    chunks["start"] = chunks["start_idx"].map(lambda i: series.index[i])
    chunks["end"] = chunks["end_idx"].map(lambda i: series.index[i])
    chunks["regime"] = (
        chunks["label"].map(REGIME_NAMES) if n_labels == 5 else chunks["label"].astype(str)
    )

    return MarketSegments(labels=labels_series, chunks=chunks)


def chunk_sampling_priority(
    chunks: pd.DataFrame, beta: float, risk_threshold: float = 0.2
) -> np.ndarray:
    """
    EarnHFT Eq.4 이식 — chunk의 buy&hold 수익률(slope, r)에 대한 β-지수가중
    샘플링 우선순위. 분포 꼬리(상/하위 θ/2 분위수 밖)는 e^(βr), 중앙부는
    e^(βr)/pdf(r)로 커널밀도 보정(중앙부 밀집으로 인한 샘플링 쏠림 완화).
    반환값은 정규화된 확률 벡터(합 1, chunks와 같은 순서).
    """
    r = chunks["slope"].to_numpy(dtype=np.float64)
    theta = risk_threshold
    Ht = np.quantile(r, 1 - theta / 2)
    Lt = np.quantile(r, theta / 2)

    std = r.std() if r.std() > 1e-12 else 1.0
    h = max(0.9 * std * len(r) ** (-1 / 5), 1e-8)  # Silverman 대역폭 근사
    diffs = (r[:, None] - r[None, :]) / h
    pdf = np.exp(-0.5 * diffs ** 2).sum(axis=1) / (len(r) * h * np.sqrt(2 * np.pi))
    pdf = np.maximum(pdf, 1e-12)

    tail_mask = (r >= Ht) | (r <= Lt)
    log_w = beta * r - np.where(tail_mask, 0.0, np.log(pdf))
    log_w -= log_w.max()  # overflow 방지
    weights = np.exp(log_w)
    return weights / weights.sum()


if __name__ == "__main__":
    import os

    path = os.path.join(os.path.dirname(__file__), "data", "features_5m", "BTCUSDT.parquet")
    df = pd.read_parquet(path, columns=["datetime", "close"])
    df = df[df["datetime"] >= "2025-01-01"].reset_index(drop=True)

    # 5분봉 → 30분 버킷(6봉)으로 다운샘플링해 RL 환경과 동일한 시간 단위로 맞춤
    df["bucket"] = df["datetime"].astype("int64") // 10**9 // 1800
    bucketed = df.groupby("bucket")["close"].last()

    seg = segment_and_label(bucketed)
    print(f"버킷 수: {len(bucketed)}, 구간 수: {len(seg.chunks)}")
    print(seg.chunks["regime"].value_counts())
    print()
    print(seg.chunks[["start", "end", "length", "slope", "regime"]].to_string(index=False))

    weights = chunk_sampling_priority(seg.chunks, beta=60.0)
    print("\nβ=60(강세 선호) 상위 5개 chunk:")
    top5 = np.argsort(weights)[::-1][:5]
    print(seg.chunks.iloc[top5][["start", "end", "regime", "slope"]].assign(weight=weights[top5]))
