"""
실시간 5분봉으로부터 20개 기술지표 피처 윈도우를 만든다.

crypto/preprocess_features.py 의 add_features()를 그대로 재사용한다 — 오프라인
피처 생성(학습에 쓰인 features_5m/*.parquet)과 100% 동일한 로직이어야 학습된
모델의 입력 분포와 어긋나지 않는다. 여기서 재구현하지 않는다.
"""

from __future__ import annotations

import time

import pandas as pd

from crypto.broker.base import BrokerClient
from crypto.preprocess_features import FEATURE_COLS, add_features

SEQ_LEN = 60  # 하이브리드 모델 입력 윈도우 길이 (노트북 SEQ_LEN과 동일)
BAR = "5min"
BAR_MS = 5 * 60 * 1000
STALE_AFTER_MS = 6 * BAR_MS  # 마지막 완성봉이 30분 넘게 묵었으면 거래정지/상장폐지로 본다


def _regularize(bars: list[dict]) -> pd.DataFrame:
    """preprocess_features.load_and_regularize()와 동일한 방식으로 5분 그리드 정합화."""
    df = pd.DataFrame(bars)
    df["datetime"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df = df.drop_duplicates(subset="datetime").set_index("datetime").sort_index()

    full_index = pd.date_range(df.index[0], df.index[-1], freq=BAR, tz="UTC")
    df = df.reindex(full_index)

    df["close"] = df["close"].ffill()
    for col in ("open", "high", "low"):
        df[col] = df[col].fillna(df["close"])
    df["volume"] = df["volume"].fillna(0.0)
    return df


def build_live_window(broker: BrokerClient, symbol: str, n_bars: int = 150) -> pd.DataFrame | None:
    """최근 n_bars개 5분봉으로 피처를 계산해 마지막 SEQ_LEN(60)행을 반환한다.

    데이터가 부족하거나(SMA_60 워밍업 미달) 최근 봉이 없거나(거래정지) 조회 결과가 비정상이면
    None을 반환한다 — 호출부는 이 경우 해당 심볼을 0-vector 임베딩으로 대체해야 한다
    (학습 시 상장 전 자산 처리와 동일).
    """
    now_ms = int(time.time() * 1000)
    bars = broker.get_minute_bars(symbol, n_bars=n_bars + 1)
    # 거래소가 돌려주는 마지막 봉은 아직 진행 중인 봉이다(close·volume이 미완성) — 학습 피처는
    # 완성봉으로만 만들었으므로 닫히지 않은 봉은 버린다.
    bars = [b for b in bars if b["time"] + BAR_MS <= now_ms]
    if len(bars) < SEQ_LEN:
        return None
    if now_ms - (bars[-1]["time"] + BAR_MS) > STALE_AFTER_MS:
        # 거래정지(BREAK) 심볼은 과거 봉만 돌려주므로, 묵은 데이터로 임베딩하지 않고 0-vector 처리
        return None

    df = _regularize(bars)
    df = add_features(df)
    df = df.dropna(subset=["SMA_60"])
    if len(df) < SEQ_LEN:
        return None

    window = df.tail(SEQ_LEN)
    if window[FEATURE_COLS].isna().any().any():
        return None
    return window
