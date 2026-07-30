"""
심볼별 (60,20) 피처 윈도우 + (60,) raw close 윈도우로부터 64-dim RL 임베딩을 만든다.

crypto_hybrid_model_colab.ipynb 셀 20(배치 임베딩 추출 루프)의 라이브 버전 —
한 번에 윈도우 하나(N=1)씩 처리한다는 점만 다르고 정규화/모델 호출 로직은 동일하다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from crypto.models.hybrid_model import ChronosMTGNN, extract_chronos_embs
from crypto.preprocess_features import FEATURE_COLS


def build_embedding(
    window_df: pd.DataFrame,
    hybrid_model: ChronosMTGNN,
    pipeline,
    device: str = "cpu",
) -> np.ndarray:
    """window_df: build_live_window()가 반환한 SEQ_LEN(60)행 DataFrame."""
    w = window_df[FEATURE_COLS].to_numpy(dtype=np.float32)  # (60, 20)
    mu, sd = w.mean(0), w.std(0) + 1e-8
    x_flat = ((w - mu) / sd)[None, ...]  # (1, 60, 20) — 노트북과 동일한 윈도우별 z-score

    close = window_df["close"].to_numpy(dtype=np.float32)[None, ...]  # (1, 60)
    c_emb_np = extract_chronos_embs(pipeline, close, batch_size=1, device=device)
    c_emb = torch.tensor(c_emb_np, dtype=torch.float32, device=device)

    emb = hybrid_model.embed(torch.tensor(x_flat, device=device), c_emb)
    return emb.cpu().numpy()[0]  # (64,)
