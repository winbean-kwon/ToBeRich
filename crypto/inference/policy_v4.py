"""
v4 정책(β=-30 PPO 풀 에이전트 단독 + 추론 스무딩)을 실계좌 라이브 루프에 연동하는 어댑터.

crypto_hrl_earnhft_colab.ipynb §13 로직을 이식했다:
  - SparseGatedCryptoPortfolioEnv.action_to_weights (셀 44): top-K 희소선택 + 리스크게이트
  - run_v4_solo_smoothed_on (§15, 2026-07-29): w = (1-α)*prev_w + α*target_w 관성 스무딩, α=0.01

§13-I(2026-07-28)에서 "매칭" DQN 라우터(episode_progress 학습·서빙 일치)를 도입했으나, §15(2026-07-29)
재검증에서 이 라우터가 valid·test 전 구간에서 β=30 하나만 100% 선택한다는 게 확인됨 — β=30 단독
실행과 총수익률이 소수점까지 정확히 일치(라우터가 아무 정보도 쓰지 않는 상수함수로 붕괴한 상태였음).
4β 풀·DQN 라우터·macro 관측값을 전부 걷어내고 풀 에이전트 하나만 직접 배포하는 구조로 단순화했다.

§16(2026-07-29)에서 4개 β를 전부 valid(2025 Q4)/test(2026 H1)에서 단독 비교한 결과, 애초에 배포
후보였던 β=30은 valid Sharpe 0.025 → test Sharpe 3.046으로 낙차가 극단적(과적합/우연 성적에 가까운
패턴)이었던 반면 **β=-30은 valid Sharpe 1.314·test Sharpe 1.156으로 두 구간 모두 견조하고 일관됨**
(valid +4.54%/test +5.66%, β=30 대비 test 총수익은 낮지만 훨씬 강건). 이에 따라 배포 에이전트를
β=30 → **β=-30으로 교체**했다.

⚠️ 알려진 한계 (실계좌 투입 전 반드시 인지할 것, 2026-07-29 §16 갱신):
  1. §13-F 보조진단은 β=30 기준으로 수행됐던 것 — β=-30에 대한 정적 포지션 아티팩트 재진단은
     아직 안 함(우선순위 낮음: β=-30은 valid/test 성적 갭이 작아 애초에 아티팩트 의심이 옅음).
  2. §16의 α=0.01은 β=30(매칭 라우터)에 맞춰 고른 값을 그대로 4개 β 비교에 재사용한 것 —
     β=-30 전용으로 α를 다시 스윕하면 더 나아질 여지가 있으나 아직 안 함.
  3. valid(2025 Q4)도 여전히 pool 학습 때 노출된 데이터라 완전한 홀드아웃은 아님 — 더 확실히
     하려면 1~9월만 학습해 진짜 미노출 valid를 만드는 재학습(고비용, 미착수)이 다음 후보.

2026-07-29 (라이브 재시작 후 발견/수정): prev_weights를 등가중(1/n_assets)으로 고정 초기화했더니
프로세스가 재시작될 때마다 α=0.01 스무딩의 시작점이 매번 44종목 등가중으로 리셋돼, top-10에만
집중돼야 할 비중이 나머지 34종목에도 잔여로 남아 사이클당 1%씩만 빠지는 문제가 있었음(재시작 직후
44종목 중 42종목을 소액씩 매수하는 형태로 관측됨) — `_init_prev_weights_from_broker()`로 실계좌
현재 포지션에서 역산한 비중을 시작점으로 쓰도록 수정.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from crypto.broker.base import BrokerClient
from crypto.inference.embeddings import build_embedding
from crypto.inference.features import build_live_window
from crypto.models.hybrid_model import load_chronos_pipeline, load_hybrid_model
from crypto.policy_base import PolicyAdapter

log = logging.getLogger("policy_v4")

BETA = -30  # §16: valid·test 둘 다 견조(Sharpe 1.314/1.156)한 가장 강건한 풀 에이전트
TOP_K = 10
ALPHA = 0.01  # §13-F BEST_ALPHA_V4 (비용 후 최고 성과 관측치)
EMB_DIM = 64


def action_to_weights(action: np.ndarray, top_k: int) -> tuple[np.ndarray, float, np.ndarray]:
    """§13-A SparseGatedCryptoPortfolioEnv.action_to_weights 이식.

    action: (n_assets+1,) — 앞 n_assets개는 종목별 confidence logit, 마지막 1개는
    리스크자산 총 노출 게이트 로짓. top-K개만 골라 그 안에서 softmax 후 sigmoid(게이트)를 곱한다.
    """
    action = np.asarray(action, dtype=np.float64)
    asset_logits, gate_logit = action[:-1], action[-1]
    n_assets = len(asset_logits)
    k = min(top_k, n_assets)
    top_idx = np.argpartition(asset_logits, -k)[-k:]
    sel = asset_logits[top_idx]
    sel = np.exp(sel - sel.max())
    sel = sel / sel.sum()
    risky_w = np.zeros(n_assets, dtype=np.float32)
    risky_w[top_idx] = sel
    rho = float(1.0 / (1.0 + np.exp(-gate_logit)))
    return (rho * risky_w).astype(np.float32), rho, top_idx


class V4PolicyAdapter(PolicyAdapter):
    def __init__(
        self,
        model_dir: str | Path,
        symbols: list[str],
        device: str = "cpu",
        alpha: float = ALPHA,
        top_k: int = TOP_K,
        beta: int = BETA,
        n_bars: int = 150,  # SMA_60 워밍업(59봉 소모) 후에도 SEQ_LEN(60)행이 남도록 여유있게 요청
    ):
        model_dir = Path(model_dir)
        self.symbols = list(symbols)
        self.n_assets = len(self.symbols)
        self.device = device
        self.alpha = alpha
        self.top_k = top_k
        self.n_bars = n_bars

        log.info("[v4] 풀 에이전트(β=%d) 로드 중...", beta)
        self.model = PPO.load(str(model_dir / "crypto_hrl_pool_v4" / f"agent_beta_{beta}.zip"))

        log.info("[v4] 하이브리드 백본(ChronosMTGNN) 로드 중...")
        self.hybrid_model = load_hybrid_model(model_dir / "crypto_hybrid_best.pt", device=device)
        self.pipeline = load_chronos_pipeline(device=device)

        self.prev_weights: np.ndarray | None = None  # 첫 target_weights 호출 시 실계좌 포지션으로 초기화
        self.last_top_symbols: list[str] = []  # 가장 최근 호출의 진짜 top-K 선택(스무딩 이전, 진단용)

        log.info("[v4] 초기화 완료 — 심볼 %d개, β=%d, α=%.3f, top_k=%d", self.n_assets, beta, alpha, top_k)

    def _init_prev_weights_from_broker(self, broker: BrokerClient) -> np.ndarray:
        """prev_weights를 실계좌 현재 포지션 비중으로부터 계산한다.

        등가중(1/n_assets)으로 고정 초기화하면 프로세스가 재시작될 때마다 관성 스무딩
        (α=0.01, 사이클당 1%만 반영)의 시작점이 매번 등가중으로 리셋돼, top-K 희소선택이
        의도한 대로 10종목에 집중되지 못하고 나머지 종목에도 등가중 잔여 비중이 매우 느리게만
        빠지는 문제가 있었다 — 실제 보유 포지션에서 역산하면 재시작 여부와 무관하게 항상
        "지금 실제로 들고 있는 상태"에서 스무딩이 이어진다.
        """
        positions = {p.symbol: p for p in broker.get_positions()}
        equity = broker.get_cash_balance() + sum(p.quantity * p.current_price for p in positions.values())
        w = np.zeros(self.n_assets, dtype=np.float32)
        if equity > 0:
            for i, sym in enumerate(self.symbols):
                pos = positions.get(sym)
                if pos is not None:
                    w[i] = (pos.quantity * pos.current_price) / equity
        log.info("[v4] prev_weights를 실계좌 포지션에서 초기화 — 비중 합=%.4f (equity=%.2f USDT)", float(w.sum()), equity)
        return w

    def _build_embeddings(self, broker: BrokerClient) -> np.ndarray:
        embeddings = np.zeros((self.n_assets, EMB_DIM), dtype=np.float32)
        for i, sym in enumerate(self.symbols):
            try:
                window = build_live_window(broker, sym, n_bars=self.n_bars)
                if window is None:
                    log.warning("심볼 %s 워밍업 데이터 부족 — 0-vector로 대체", sym)
                    continue
                embeddings[i] = build_embedding(window, self.hybrid_model, self.pipeline, device=self.device)
            except Exception:
                log.exception("심볼 %s 임베딩 계산 실패 — 0-vector로 대체", sym)
        return embeddings

    def target_weights(self, symbols: list[str], broker: BrokerClient) -> dict[str, float]:
        if list(symbols) != self.symbols:
            raise ValueError(
                "V4PolicyAdapter는 초기화 시 고정한 심볼 순서와 정확히 같은 리스트를 요구합니다 "
                "(모델 obs/action의 각 차원이 특정 심볼 위치에 대응하므로 순서가 바뀌면 안 됩니다)."
            )

        if self.prev_weights is None:
            self.prev_weights = self._init_prev_weights_from_broker(broker)

        embeddings = self._build_embeddings(broker)
        obs = np.concatenate([embeddings.flatten(), self.prev_weights]).astype(np.float32)

        action, _ = self.model.predict(obs, deterministic=True)
        target_w, rho, top_idx = action_to_weights(action, self.top_k)
        self.last_top_symbols = [self.symbols[i] for i in top_idx]  # 더스트 청산 등 진단용

        w = (1 - self.alpha) * self.prev_weights + self.alpha * target_w
        self.prev_weights = w

        log.info(
            "[v4] ρ=%.3f | top-%d 종목(%s) | 스무딩 후 비중 합=%.4f",
            rho, len(top_idx), ",".join(self.last_top_symbols), float(w.sum()),
        )
        return {sym: float(w[i]) for i, sym in enumerate(self.symbols)}
