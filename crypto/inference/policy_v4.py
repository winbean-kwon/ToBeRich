"""
v4 정책(β=30 PPO 풀 에이전트 단독 + 추론 스무딩)을 실계좌 라이브 루프에 연동하는 어댑터.

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

2026-10-08 (회계 수정 후 재학습, paper/RETRAIN_1006.md): 위 §16 비교는 재조정 비용이 빠진 보상으로
학습한 풀의 결과였다. 수정된 보상으로 풀을 처음부터 다시 학습하자 판정이 뒤집혀 β=30이 valid
Sharpe 0.653·test 2.602로 네 β 중 valid 최고가 됐고, β=-30은 valid에서 손실(−7.39%, Sharpe −1.155)을
냈다. 이에 따라 배포 에이전트를 **β=30(재학습 모델)으로 다시 교체**했다. 모델은 재학습 전 파일과
섞이지 않도록 `models/rt1006/crypto_hrl_pool_v4/`에서 불러온다(Drive `models/rt1006/crypto_hrl_pool_v4/`
에서 받아 둘 것). 이 정책은 평균 위험자산 노출이 10~20%(나머지 현금)인 매우 보수적인 정책이다.
아래 "알려진 한계" 1·3은 재학습 후 β=30 기준으로 해소됐다(저턴오버 진단·1~9월 클린 재학습 수행).

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

import hashlib
import json
import logging
import os
import time
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from crypto.broker.base import BrokerClient, managed_equity
from crypto.inference.embeddings import build_embedding
from crypto.inference.features import build_live_window
from crypto.models.hybrid_model import load_chronos_pipeline, load_hybrid_model
from crypto.policy_base import PolicyAdapter

log = logging.getLogger("policy_v4")

BETA = 30  # 재학습 후 valid Sharpe 최고(0.653, test 2.602) — paper/RETRAIN_1006.md
POOL_SUBDIR = Path("rt1006") / "crypto_hrl_pool_v4"  # 수정된 보상으로 재학습한 풀(재학습 전 파일과 분리)
# Drive의 rt1006 β=30 파일 크기(DEPLOY_WINDOWS.md 2.5절). 같은 이름의 파일이 asset_scaling/topk_sweep
# 폴더와 재학습 전 풀(38,537,656바이트)에도 있어 잘못 받기 쉽다 — 다르면 엉뚱한 정책이 실계좌에서
# 돌게 되므로 시작 단계에서 막는다.
EXPECTED_AGENT_BYTES = 38_538_412
STATE_MAX_AGE_SEC = 24 * 3600  # 저장된 스무딩 상태를 재시작 시 이어 쓰는 최대 경과 시간
TOP_K = 10
ALPHA = 0.01  # §13-F BEST_ALPHA_V4 (비용 후 최고 성과 관측치)
EMB_DIM = 64


def action_to_weights(
    action: np.ndarray, top_k: int, tradable: np.ndarray | None = None
) -> tuple[np.ndarray, float, np.ndarray]:
    """§13-A SparseGatedCryptoPortfolioEnv.action_to_weights 이식.

    action: (n_assets+1,) — 앞 n_assets개는 종목별 confidence logit, 마지막 1개는
    리스크자산 총 노출 게이트 로짓. top-K개만 골라 그 안에서 softmax 후 sigmoid(게이트)를 곱한다.

    tradable: (n_assets,) bool — 학습 이후 거래정지/상장폐지된 종목을 top-K 후보에서 뺀다(라이브 전용,
    학습 때는 전부 True). 빼지 않으면 그 종목 몫의 비중이 주문되지 못하고 현금으로 남아, 게이트 ρ가 정한
    위험자산 노출보다 실제 노출이 체계적으로 낮아진다. 종목 선택만 바뀌고 ρ는 그대로다.
    """
    action = np.asarray(action, dtype=np.float64)
    asset_logits, gate_logit = action[:-1].copy(), action[-1]
    n_assets = len(asset_logits)
    if tradable is not None:
        asset_logits[~tradable] = -np.inf
        n_candidates = int(tradable.sum())
    else:
        n_candidates = n_assets
    k = min(top_k, n_candidates)
    rho = float(1.0 / (1.0 + np.exp(-gate_logit)))
    if k == 0:
        return np.zeros(n_assets, dtype=np.float32), rho, np.array([], dtype=int)
    top_idx = np.argpartition(asset_logits, -k)[-k:]
    sel = asset_logits[top_idx]
    sel = np.exp(sel - sel.max())
    sel = sel / sel.sum()
    risky_w = np.zeros(n_assets, dtype=np.float32)
    risky_w[top_idx] = sel
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
        max_capital: float | None = None,  # 루프의 --max-capital과 같은 값이어야 비중 기준이 일치
        state_path: str | Path | None = None,  # 스무딩 상태(prev_weights) 저장 위치. None이면 저장 안 함(dry-run)
    ):
        model_dir = Path(model_dir)
        self.symbols = list(symbols)
        self.n_assets = len(self.symbols)
        self.device = device
        self.alpha = alpha
        self.top_k = top_k
        self.n_bars = n_bars
        self.max_capital = max_capital
        self.state_path = Path(state_path) if state_path is not None else None

        log.info("[v4] 풀 에이전트(β=%d) 로드 중...", beta)
        agent_path = model_dir / POOL_SUBDIR / f"agent_beta_{beta}.zip"
        if not agent_path.exists():
            raise FileNotFoundError(
                f"재학습 모델 없음: {agent_path} — Drive models/rt1006/crypto_hrl_pool_v4/에서 받아 두세요"
            )
        size = agent_path.stat().st_size
        if beta == BETA and size != EXPECTED_AGENT_BYTES:
            raise ValueError(
                f"{agent_path} 크기 {size:,}바이트 ≠ 기대값 {EXPECTED_AGENT_BYTES:,} — 다른 폴더(asset_scaling/"
                "topk_sweep/재학습 전 풀)의 파일일 가능성. Drive models/rt1006/crypto_hrl_pool_v4/에서 다시 받으세요"
            )
        sha = hashlib.sha256(agent_path.read_bytes()).hexdigest()[:12]
        self.model_info = f"{agent_path.name} (β={beta}) | {size:,}바이트 | sha256 {sha}"  # 대시보드 표시용
        log.info("[v4] 모델 파일 %s | %s바이트 | sha256 %s", agent_path, f"{size:,}", sha)
        self.model = PPO.load(str(agent_path))

        log.info("[v4] 하이브리드 백본(ChronosMTGNN) 로드 중...")
        self.hybrid_model = load_hybrid_model(model_dir / "crypto_hybrid_best.pt", device=device)
        self.pipeline = load_chronos_pipeline(device=device)

        self.prev_weights: np.ndarray | None = None  # 첫 target_weights 호출 시 실계좌 포지션으로 초기화
        self.last_top_symbols: list[str] = []  # 가장 최근 호출의 진짜 top-K 선택(스무딩 이전, 진단용)
        self.last_rho: float | None = None

        log.info("[v4] 초기화 완료 — 심볼 %d개, β=%d, α=%.3f, top_k=%d", self.n_assets, beta, alpha, top_k)

    def _init_prev_weights_from_broker(self, broker: BrokerClient) -> np.ndarray:
        """prev_weights를 실계좌 현재 포지션 비중으로부터 계산한다.

        등가중(1/n_assets)으로 고정 초기화하면 프로세스가 재시작될 때마다 관성 스무딩
        (α=0.01, 사이클당 1%만 반영)의 시작점이 매번 등가중으로 리셋돼, top-K 희소선택이
        의도한 대로 10종목에 집중되지 못하고 나머지 종목에도 등가중 잔여 비중이 매우 느리게만
        빠지는 문제가 있었다 — 실제 보유 포지션에서 역산하면 재시작 여부와 무관하게 항상
        "지금 실제로 들고 있는 상태"에서 스무딩이 이어진다.

        분모는 루프가 주문 수량을 계산할 때 쓰는 것과 같은 managed_equity(유니버스 밖 코인 제외,
        --max-capital 상한)다 — 전체 잔고로 나누면 --max-capital 운용 시 비중이 과소평가돼
        재시작 직후 이미 들고 있는 종목을 또 사게 된다.
        """
        positions = {p.symbol: p for p in broker.get_positions()}
        equity = managed_equity(broker.get_cash_balance(), positions, self.symbols, self.max_capital)
        w = np.zeros(self.n_assets, dtype=np.float32)
        if equity > 0:
            for i, sym in enumerate(self.symbols):
                pos = positions.get(sym)
                if pos is not None:
                    w[i] = (pos.quantity * pos.current_price) / equity
        log.info("[v4] prev_weights를 실계좌 포지션에서 초기화 — 비중 합=%.4f (equity=%.2f USDT)", float(w.sum()), equity)
        return w

    def _load_state(self) -> np.ndarray | None:
        """저장된 스무딩 상태를 불러온다. 없거나 심볼 구성이 다르거나 너무 오래됐으면 None.

        재시작 때마다 실계좌 포지션에서 다시 역산하면, 최소주문금액 때문에 실제 포지션이 거의 안 움직이는
        소액 계좌에서는 스무딩 진행분이 매번 지워진다 — 2026-10-25 서버 실측: 재시작 직전 목표 노출 23.0%가
        재시작 직후 25.5%(=실제 보유 비중)로 되돌아감. 정책의 내부 상태를 이어 써야 백테스트와 같은 궤적이 된다.
        """
        if self.state_path is None or not self.state_path.exists():
            return None
        try:
            state = json.loads(self.state_path.read_text())
        except (OSError, ValueError):
            log.warning("[v4] 스무딩 상태 파일을 읽지 못함 — 실계좌 포지션에서 초기화")
            return None
        age = time.time() - state.get("saved_at", 0)
        if state.get("symbols") != self.symbols or age > STATE_MAX_AGE_SEC:
            log.info("[v4] 저장된 스무딩 상태 무시(심볼 구성 변경 또는 %.1f시간 경과) — 실계좌 포지션에서 초기화", age / 3600)
            return None
        w = np.asarray(state["prev_weights"], dtype=np.float32)
        log.info("[v4] 저장된 스무딩 상태 복원 — 비중 합=%.4f (%.0f분 전 저장)", float(w.sum()), age / 60)
        return w

    def _save_state(self) -> None:
        if self.state_path is None:
            return
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({
            "symbols": self.symbols, "prev_weights": [float(x) for x in self.prev_weights], "saved_at": time.time(),
        }))
        os.replace(tmp, self.state_path)

    def _build_embeddings(self, broker: BrokerClient) -> np.ndarray:
        embeddings = np.zeros((self.n_assets, EMB_DIM), dtype=np.float32)
        for i, sym in enumerate(self.symbols):
            if not broker.is_tradable(sym):
                # 거래정지 종목은 봉 조회 없이 0-vector(학습 시 상장 전 자산과 동일). 경고는 루프가 한 번만 남긴다 —
                # 여기서 매 사이클 경고하면 대시보드가 항상 "주의"가 되고 진짜 경고가 묻힌다.
                continue
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
            self.prev_weights = self._load_state()
        if self.prev_weights is None:
            self.prev_weights = self._init_prev_weights_from_broker(broker)

        embeddings = self._build_embeddings(broker)
        obs = np.concatenate([embeddings.flatten(), self.prev_weights]).astype(np.float32)

        action, _ = self.model.predict(obs, deterministic=True)
        tradable = np.array([broker.is_tradable(s) for s in self.symbols])
        target_w, rho, top_idx = action_to_weights(action, self.top_k, tradable)
        self.last_rho = rho
        self.last_top_symbols = [self.symbols[i] for i in top_idx]  # 더스트 청산 등 진단용

        w = (1 - self.alpha) * self.prev_weights + self.alpha * target_w
        self.prev_weights = w
        self._save_state()

        log.info(
            "[v4] ρ=%.3f | top-%d 종목(%s) | 스무딩 후 비중 합=%.4f",
            rho, len(top_idx), ",".join(self.last_top_symbols), float(w.sum()),
        )
        return {sym: float(w[i]) for i, sym in enumerate(self.symbols)}
