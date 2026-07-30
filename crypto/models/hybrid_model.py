"""
Chronos T5 인코더(temporal) + MTGNN 피처 그래프(cross-feature) 하이브리드 백본.

crypto/notebooks/crypto_hybrid_model_colab.ipynb 셀 7·10을 그대로 이식한 것 —
학습 로직은 없고(헤드는 정의만 하고 쓰지 않음), 라이브 추론(임베딩 추출)에만 쓴다.
로직을 바꾸면 학습된 crypto_hybrid_best.pt 가중치와 어긋나므로 원본과 동일하게 유지할 것.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from chronos import ChronosPipeline


class AdaptiveGraphLearner(nn.Module):
    """학습 가능한 노드 임베딩 → 피처 그래프 인접 행렬 자동 생성"""

    def __init__(self, n_nodes, emb_dim=10):
        super().__init__()
        self.E1 = nn.Parameter(torch.randn(n_nodes, emb_dim) * 0.1)
        self.E2 = nn.Parameter(torch.randn(n_nodes, emb_dim) * 0.1)

    def forward(self):
        return torch.softmax(torch.relu(self.E1 @ self.E2.T), dim=-1)  # (N, N)


class MTGNNEncoder(nn.Module):
    """MTGNN 피처 그래프 인코더 (헤드 없음) → (B, n_features × d_model)"""

    def __init__(self, seq_len=60, n_features=20, d_model=64, n_layers=3, dropout=0.1):
        super().__init__()
        self.input_proj = nn.Conv2d(1, d_model, kernel_size=(1, 1))

        dilations = [1, 2, 4][:n_layers]
        self.filter_convs = nn.ModuleList(
            [
                nn.Conv2d(d_model, d_model, (1, 3), dilation=(1, d), padding=(0, d))
                for d in dilations
            ]
        )
        self.gate_convs = nn.ModuleList(
            [
                nn.Conv2d(d_model, d_model, (1, 3), dilation=(1, d), padding=(0, d))
                for d in dilations
            ]
        )
        self.res_convs = nn.ModuleList([nn.Conv2d(d_model, d_model, 1) for _ in dilations])
        self.gc_weights = nn.ModuleList([nn.Linear(d_model, d_model, bias=False) for _ in dilations])
        self.norms = nn.ModuleList([nn.LayerNorm(d_model) for _ in dilations])
        self.graph = AdaptiveGraphLearner(n_features)
        self.drop = nn.Dropout(dropout)

    def forward(self, x_flat):
        B, T, N = x_flat.shape
        x = x_flat.permute(0, 2, 1).unsqueeze(1)
        x = self.input_proj(x)  # (B, d, N, T)
        A = self.graph()  # (N, N)

        for fc, gc_c, rc, gc_w, norm in zip(
            self.filter_convs, self.gate_convs, self.res_convs, self.gc_weights, self.norms
        ):
            residual = x
            T_cur = x.size(-1)
            h = torch.tanh(fc(x)[..., :T_cur]) * torch.sigmoid(gc_c(x)[..., :T_cur])  # Gated TCN
            h_p = h.permute(0, 3, 2, 1)  # (B, T, N, d)
            h_gc = torch.einsum("nm,btmc->btnc", A, h_p)
            h_gc = gc_w(h_gc).permute(0, 3, 2, 1)  # (B, d, N, T)
            combined = self.drop(h_gc) + rc(residual)
            x = norm(combined.permute(0, 3, 2, 1)).permute(0, 3, 2, 1)

        x = x.mean(-1)  # (B, d, N)
        return x.permute(0, 2, 1).flatten(1)  # (B, N*d)


class ChronosMTGNN(nn.Module):
    """
    Chronos T5 인코더(temporal) + MTGNN 피처 그래프(cross-feature) 하이브리드
    - Chronos: 가격 시계열 시간축 패턴 → 64-dim
    - MTGNN:   20개 기술지표 그래프 관계 → 1280-dim
    → Fusion → 64-dim RL state embedding
    """

    def __init__(self, seq_len=60, n_features=20, chronos_dim=512, d_model=64, n_layers=3, dropout=0.1):
        super().__init__()
        self.chronos_proj = nn.Linear(chronos_dim, d_model)
        self.chronos_norm = nn.LayerNorm(d_model)

        self.mtgnn = MTGNNEncoder(seq_len, n_features, d_model, n_layers, dropout)

        fusion_in = d_model + n_features * d_model  # 64 + 1280 = 1344
        self.fusion = nn.Sequential(
            nn.Linear(fusion_in, 256), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(256, 64), nn.GELU(),
        )
        self.head = nn.Linear(64, 1)

    def _fuse(self, x_flat, c_emb):
        chron = self.chronos_norm(self.chronos_proj(c_emb))  # (B, 64)
        mtg = self.mtgnn(x_flat)  # (B, 1280)
        return self.fusion(torch.cat([chron, mtg], dim=-1))  # (B, 64)

    def forward(self, x_flat, c_emb):
        return self.head(self._fuse(x_flat, c_emb)).squeeze(-1)

    @torch.no_grad()
    def embed(self, x_flat, c_emb):
        """64-dim RL state representation"""
        self.eval()
        return self._fuse(x_flat, c_emb)

    @torch.no_grad()
    def get_adjacency(self):
        return self.mtgnn.graph().cpu().numpy()


def load_hybrid_model(
    checkpoint_path: str | Path,
    seq_len: int = 60,
    n_features: int = 20,
    chronos_dim: int = 512,
    d_model: int = 64,
    n_layers: int = 3,
    device: str = "cpu",
) -> ChronosMTGNN:
    """crypto_hybrid_best.pt(plain state_dict)를 로드해 eval 모드 모델을 반환한다."""
    model = ChronosMTGNN(seq_len, n_features, chronos_dim, d_model, n_layers)
    state_dict = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model


def load_chronos_pipeline(device: str = "cpu") -> ChronosPipeline:
    return ChronosPipeline.from_pretrained(
        "amazon/chronos-t5-small",
        device_map=device,
        torch_dtype=torch.float32,
    )


@torch.no_grad()
def extract_chronos_embs(pipeline: ChronosPipeline, close_prices_np: np.ndarray, batch_size: int = 256, device: str = "cpu") -> np.ndarray:
    """close_prices_np: (N, seq_len) float32 → (N, chronos_dim) 임베딩 (masked mean pool)"""
    tokenizer = pipeline.tokenizer
    encoder = pipeline.model.model.encoder
    all_embs = []
    for i in range(0, len(close_prices_np), batch_size):
        ctx = torch.tensor(close_prices_np[i : i + batch_size], dtype=torch.float32)
        ids, mask, _ = tokenizer.context_input_transform(ctx)
        out = encoder(input_ids=ids.to(device), attention_mask=mask.to(device))
        h = out.last_hidden_state  # (B, L, D)
        m = mask.to(device).unsqueeze(-1).float()
        emb = (h * m).sum(1) / m.sum(1).clamp(min=1)  # masked mean pool
        all_embs.append(emb.cpu().float().numpy())
    return np.concatenate(all_embs, axis=0)
