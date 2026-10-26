"""
[방법론 2 · 절제 실험 · 2026-10-26] v4 라우터 환경의 어느 요소가 붕괴를 만드는가.

배경: 통제 실험(router_collapse_study, 72da820)은 전문가 구성을 16가지로 바꿨지만 붕괴가 0/32건이라 판정 불가였다.
그 환경은 v4 라우터와 달리 입력을 로그수익×100으로 정규화하고, 보유 전문가 원-핫을 주고, 무작위 시점에서 180일
에피소드를 시작하고, 6만 스텝을 학습한다. v4 매칭 라우터 Q값 탐침에서는 선택이 거의 NAV 수준값으로만 정해졌다.
그래서 전문가 구성은 고정하고 라우터 쪽 요소를 하나씩 v4 값으로 바꿔 붕괴가 생기는지 본다.

사전 등록(실행 전 커밋, 결과를 본 뒤 바꾸지 않는다):
  환경: factor_router_pit의 일간 PIT 13종목, 분할 2021–23 학습 / 2024 검증 / 2025– 테스트, 수수료 0.1%.
  전문가 구성(고정): S04 저노출 혼합 [EW10, LV30, BTC30, EW20], S07 팩터+현금 [MOM100, LV100, EW100, CASH].
  요소(v4 값, crypto_hrl_earnhft_colab 셀 50·63):
    A 관측 = NAV 수준값 창 14개(앞은 1.0으로 채움, 정규화 없음) + [창 끝−처음, 창 수익 std, 창 수익 mean, 0.5]
    B 보유 전문가 원-핫 제거
    C 에피소드 = 학습 구간 처음부터 끝까지 1개(항상 t=0 시작)
    D DQN = v4 설정(2만 스텝, gamma 0.95, 버퍼 2만, 시작 500, 타깃 200, 망 [128, 64]) — 나머지는 동일
  기준 = 통제 실험의 nav 모드(로그수익×100 창 30 + 원-핫, 무작위 180일 에피소드, 6만 스텝, gamma 0.9, [64, 64]).
  조건 10개: 기준, +A, +B, +C, +D, ALL, ALL−A, ALL−B, ALL−C, ALL−D. 시드 0·1·2 → 10 × 2 × 3 = 60회.
  붕괴(시드 단위): 검증과 테스트 '둘 다'에서 한 전문가 선택 비율 ≥ 0.9. 조건별 붕괴 수 = 6개 중 몇 개.
  판정:
    1. ALL이 4/6 미만이면 "v4 붕괴는 이 라우터 요소들만으로 재현되지 않음"으로 보고하고 요소별 해석은 하지 않는다.
    2. ALL이 4/6 이상이면 요소 X를 분류한다: 필요 = ALL−X ≤ 1/6, 충분 = +X ≥ 4/6, 그 외 = 기여 불명확.
  기록만(판정에 안 씀): 선택 전환 횟수, 검증·테스트 각각의 최빈 비율.

실행: python -m crypto.experiments.router_ablation  (저장소 루트) → crypto/experiments/results/router_ablation.csv
"""

from __future__ import annotations

import sys

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces
from stable_baselines3 import DQN

from crypto.experiments import factor_router_pit as F
from crypto.experiments.router_collapse_study import library

SEEDS = [0, 1, 2]
CONFIGS = {"S04": ["EW10", "LV30", "BTC30", "EW20"], "S07": ["MOM100", "LV100", "EW100", "CASH"]}
FACTORS = "ABCD"
CONDITIONS = {"기준": "", "+A": "A", "+B": "B", "+C": "C", "+D": "D", "ALL": "ABCD",
              "ALL−A": "BCD", "ALL−B": "ACD", "ALL−C": "ABD", "ALL−D": "ABC"}
LEVEL_WINDOW = 14
BASE_DQN = dict(learning_rate=1e-3, buffer_size=50_000, learning_starts=1_000, batch_size=64, gamma=0.9, train_freq=1,
                target_update_interval=500, exploration_fraction=0.3, exploration_final_eps=0.05)
V4_DQN = dict(learning_rate=1e-3, buffer_size=20_000, learning_starts=500, batch_size=64, gamma=0.95, train_freq=1,
              target_update_interval=200, exploration_fraction=0.3, exploration_final_eps=0.05)


class AblationEnv(gym.Env):
    """factor_router_pit.RouterEnv(nav 모드)에 요소 A·B·C를 켜고 끌 수 있게 한 것. 보상·비용 계산은 같다."""

    def __init__(self, W, Rn, idx, flags: str, rng, evaluate=False):
        super().__init__()
        self.W, self.Rn, self.idx, self.rng, self.evaluate = W, Rn, idx, rng, evaluate
        self.level, self.no_hold, self.full_ep = "A" in flags, "B" in flags, "C" in flags
        self.nE = W.shape[0]
        dim = (LEVEL_WINDOW + 4 if self.level else 30) + (0 if self.no_hold else self.nE)
        self.action_space = spaces.Discrete(self.nE)
        self.observation_space = spaces.Box(-np.inf, np.inf, (dim,), np.float32)

    def _obs(self):
        if self.level:   # v4 MacroRouterEnvV4._macro_obs (매칭: 진행률 0.5)
            h = self.nav_hist[-LEVEL_WINDOW:]
            h = [1.0] * (LEVEL_WINDOW - len(h)) + h
            recent = np.asarray(h, np.float64)
            ret = np.diff(recent)
            x = np.concatenate([recent, [recent[-1] - recent[0], ret.std(), ret.mean(), 0.5]])
        else:
            h = (self.nav_hist[-30:] if len(self.nav_hist) >= 30 else [1.0] * (30 - len(self.nav_hist)) + self.nav_hist)
            x = np.diff(np.log(np.asarray([h[0]] + h))) * 100
        if not self.no_hold:
            x = np.concatenate([x, np.eye(self.nE)[self.cur]])
        return x.astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        start = 0 if (self.evaluate or self.full_ep) else self.rng.integers(0, max(1, len(self.idx) - F.EP_LEN))
        self.k0 = self.k = int(start)
        self.cur, self.w_prev, self.nav_hist, self.nav = 3 % self.nE, np.zeros(self.W.shape[2]), [], 1.0
        return self._obs(), {}

    def step(self, a):
        i = self.idx[self.k]
        w = self.W[int(a), i]
        cost = F.TC * np.abs(w - self.w_prev).sum()
        pr = float(w @ self.Rn[i])
        self.w_prev = w * (1 + self.Rn[i]) / (1 + pr) if pr > -1 else w
        r = pr - cost
        self.nav *= 1 + r
        self.nav_hist.append(self.nav)
        self.cur, self.k = int(a), self.k + 1
        ep_end = (not self.evaluate) and (not self.full_ep) and self.k - self.k0 >= F.EP_LEN
        done = self.k >= len(self.idx) or ep_end
        obs = self._obs() if not done else np.zeros(self.observation_space.shape, np.float32)
        return obs, float(np.log1p(r)), done, False, {}


def run(model, W, Rn, idx, flags):
    env = AblationEnv(W, Rn, idx, flags, np.random.default_rng(0), evaluate=True)
    obs, _ = env.reset()
    ch, done = [], False
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        ch.append(int(a))
        obs, _, done, _, _ = env.step(a)
    return np.asarray(ch)


def main():
    C, V = F.load_daily()
    lib, Rn = library(C, V)
    days = np.arange(len(C) - 1)
    idx = {k: np.array([i for i in days if a <= str(C.index[i].date()) <= b]) for k, (a, b) in F.SPLITS.items()}
    rows = []
    for cname, members in CONFIGS.items():
        W = np.stack([lib[m] for m in members])
        for cond, flags in CONDITIONS.items():
            for seed in SEEDS:
                env = AblationEnv(W, Rn, idx["train"], flags, np.random.default_rng(seed))
                d = "D" in flags
                model = DQN("MlpPolicy", env, **(V4_DQN if d else BASE_DQN),
                            policy_kwargs=dict(net_arch=[128, 64] if d else [64, 64]), seed=seed, verbose=0, device="cpu")
                model.learn(20_000 if d else F.TOTAL_STEPS)
                rec = {"구성": cname, "조건": cond, "요소": flags, "시드": seed}
                for split in ("valid", "test"):
                    ch = run(model, W, Rn, idx[split], flags)
                    rec[f"{split} 최빈 비율"] = np.bincount(ch, minlength=len(members)).max() / len(ch)
                    rec[f"{split} 최빈 전문가"] = members[int(np.bincount(ch, minlength=len(members)).argmax())]
                    rec[f"{split} 전환 횟수"] = int((np.diff(ch) != 0).sum())
                rec["붕괴"] = int(rec["valid 최빈 비율"] >= 0.9 and rec["test 최빈 비율"] >= 0.9)
                rows.append(rec)
                print(f"{cname} {cond:6s} seed {seed}: 검증 {rec['valid 최빈 비율']:.2f} 테스트 {rec['test 최빈 비율']:.2f} "
                      f"→ 붕괴 {rec['붕괴']}", flush=True)
    res = pd.DataFrame(rows)
    out = F.OUT / "router_ablation.csv"
    res.to_csv(out, index=False, encoding="utf-8-sig")

    n = res.groupby("조건", sort=False)["붕괴"].sum()
    print("\n조건별 붕괴 수(/6):", n.to_dict())
    if n["ALL"] < 4:
        print(f"[사전 등록 판정] ALL 붕괴 {n['ALL']}/6 < 4 → v4 붕괴는 이 라우터 요소들만으로 재현되지 않음(요소별 해석 안 함)")
    else:
        print(f"[사전 등록 판정] ALL 붕괴 {n['ALL']}/6 ≥ 4 → 요소별 분류")
        for x in FACTORS:
            need, suff = n[f"ALL−{x}"] <= 1, n[f"+{x}"] >= 4
            label = "필요·충분" if need and suff else "필요" if need else "충분" if suff else "기여 불명확"
            print(f"  {x}: ALL−{x} {n[f'ALL−{x}']}/6, +{x} {n[f'+{x}']}/6 → {label}")
    print("저장:", out)


if __name__ == "__main__":
    sys.exit(main())
