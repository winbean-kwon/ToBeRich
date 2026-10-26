"""
[확장 2 · 2026-10-26] 정보를 주는 라우터 — point-in-time 13종목, 일간, 팩터 전문가 사이 배분.

배경: 기존 계층 RL(β만 다른 PPO 전문가 + 포트폴리오 가치 이력만 보는 DQN 라우터)은 알고리즘·자산 수·시드·
주기와 무관하게 라우터가 한 전문가로 붕괴했다. 진단: 라우터 입력에 "다음에 어느 전문가가 나을지"에 대한
정보가 없다. 이 실험은 (1) 전문가를 서로 다른 투명한 전략으로, (2) 라우터 입력을 전문가 성과·시장 상태로
바꿔 붕괴가 풀리는지, 단순 규칙보다 나은지를 사전 등록 기준으로 확인한다.

사전 등록(실행 전 고정):
  전문가: 7일 모멘텀 상위4 / 저변동성(전일 5분봉 실현변동성) 상위4 / 13종목 등가중 / 현금 — 매일 UTC 0시, 수수료 0.1%
  라우터: DQN(MLP 64-64), 입력 = 전문가별 7·30일 성과와 30일 변동성, BTC 30일 추세·변동성, 종목 간 7일 수익률 분산, 현재 보유 전문가
  대조: B1 검증(2024) 최고 단일 전문가 / B2 최근 30일 최고 전문가로 전환 / BTC / 등가중 / B4 가치 이력만 보는 라우터(기존 방식)
  분할: 학습 2021–2023 / 검증 2024 / 테스트 2025-01–데이터 끝(팩터 선택 때 일부 본 구간이라 참고용, 최종 판정은 미지 구간)
  시드 5개 평균. 성공: 정보 라우터 평균 샤프 > B1·B2 (검증·테스트 모두) 그리고 한 전문가 선택 비율 < 90%

실행: python -m crypto.experiments.factor_router_pit  (저장소 루트에서, features_5m 13종목 필요)
"""

from __future__ import annotations

import sys
from pathlib import Path

import gymnasium as gym
import numpy as np
import pandas as pd
from gymnasium import spaces
from stable_baselines3 import DQN

ROOT = Path(__file__).resolve().parents[1]
FEAT_DIR = ROOT / "data" / "features_5m"
OUT = ROOT / "experiments" / "results"
SYMS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "LTCUSDT", "BCHUSDT", "ADAUSDT", "BNBUSDT",
        "LINKUSDT", "XLMUSDT", "TRXUSDT", "DOTUSDT", "THETAUSDT", "XTZUSDT"]
TC, K = 0.001, 4
EXPERTS = ["모멘텀7d", "저변동성", "등가중", "현금"]
SPLITS = {"train": ("2021-01-01", "2023-12-31"), "valid": ("2024-01-01", "2024-12-31"), "test": ("2025-01-01", "2099-12-31")}
SEEDS = [0, 1, 2, 3, 4]
TOTAL_STEPS = 60_000
EP_LEN = 180


def load_daily():
    close, vol = {}, {}
    for s in SYMS:
        d = pd.read_parquet(FEAT_DIR / f"{s}.parquet", columns=["datetime", "close"]).set_index("datetime")["close"]
        rv = d.pct_change().rolling(288).std()
        mid = d.index[(d.index.hour == 0) & (d.index.minute == 0)]
        close[s], vol[s] = d.loc[mid], rv.loc[mid]
    C = pd.DataFrame(close).sort_index()
    end = C["BTCUSDT"].dropna().index[-1]  # BTC 데이터 끝에 맞춤
    C = C[(C.index >= "2020-12-01") & (C.index <= end)]
    V = pd.DataFrame(vol).reindex(C.index)
    return C, V


def expert_weights(C, V):
    """날짜 t에 t까지의 정보로 정한 전문가별 목표 비중 (E, T, N)."""
    R = C.shift(-1) / C - 1
    M7 = C / C.shift(7) - 1
    T, N = len(C), len(SYMS)
    W = np.zeros((len(EXPERTS), T, N))
    for i, t in enumerate(C.index):
        ok = (R.loc[t].notna() & C.loc[t].notna()).to_numpy()
        if ok.sum() == 0:
            continue
        for e, score in [(0, M7.loc[t]), (1, -V.loc[t])]:
            sc = score.where(ok).dropna()
            if len(sc) >= K:
                W[e, i, [SYMS.index(s) for s in sc.sort_values().index[-K:]]] = 1 / K
        W[2, i, ok] = 1 / ok.sum()
    return W, R.fillna(0.0).to_numpy()


def simulate(W, Rn, choice, idx):
    """선택 순서대로 전문가 비중을 보유. 비용은 가격 변동 후 비중 대비 회전율 × TC."""
    w_prev, out = np.zeros(W.shape[2]), []
    for k, i in enumerate(idx):
        w = W[choice[k], i]
        cost = TC * np.abs(w - w_prev).sum()
        pr = float(w @ Rn[i])
        w_prev = w * (1 + Rn[i]) / (1 + pr) if pr > -1 else w
        out.append(pr - cost)
    return np.asarray(out)


def features(C, expert_ret):
    """날짜 t의 라우터 입력 — t 이전에 실현된 정보만 (expert_ret[t]는 t→t+1 수익이므로 shift(1))."""
    er = pd.DataFrame(expert_ret, index=C.index).shift(1)
    f = {}
    for j, name in enumerate(EXPERTS):
        f[f"{name}_7d"] = er[j].rolling(7).sum()
        f[f"{name}_30d"] = er[j].rolling(30).sum()
        f[f"{name}_vol30"] = er[j].rolling(30).std()
    btc = C["BTCUSDT"]
    f["btc_30d"] = btc / btc.shift(30) - 1
    f["btc_vol30"] = btc.pct_change().rolling(30).std()
    f["dispersion_7d"] = (C / C.shift(7) - 1).std(axis=1)
    return pd.DataFrame(f, index=C.index)


class RouterEnv(gym.Env):
    def __init__(self, W, Rn, X, idx, mode, rng, evaluate=False):
        super().__init__()
        self.W, self.Rn, self.X, self.idx, self.mode, self.rng = W, Rn, X, idx, mode, rng
        self.evaluate = evaluate  # 평가 때는 구간 처음부터 끝까지 한 번에
        self.nE = W.shape[0]
        dim = X.shape[1] + self.nE if mode == "info" else 30 + self.nE
        self.action_space = spaces.Discrete(self.nE)
        self.observation_space = spaces.Box(-np.inf, np.inf, (dim,), np.float32)

    def _obs(self):
        hold = np.eye(self.nE)[self.cur]
        if self.mode == "info":
            x = self.X[self.idx[self.k]]
        else:  # 기존 방식: 자기 포트폴리오 가치 이력만
            h = (self.nav_hist[-30:] if len(self.nav_hist) >= 30 else [1.0] * (30 - len(self.nav_hist)) + self.nav_hist)
            x = np.diff(np.log(np.asarray([h[0]] + h))) * 100
        return np.concatenate([x, hold]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        start = 0 if self.evaluate else self.rng.integers(0, max(1, len(self.idx) - EP_LEN))
        self.k0 = self.k = int(start)
        self.cur, self.w_prev, self.nav_hist, self.nav = 3, np.zeros(self.W.shape[2]), [], 1.0
        return self._obs(), {}

    def step(self, a):
        i = self.idx[self.k]
        w = self.W[int(a), i]
        cost = TC * np.abs(w - self.w_prev).sum()
        pr = float(w @ self.Rn[i])
        self.w_prev = w * (1 + self.Rn[i]) / (1 + pr) if pr > -1 else w
        r = pr - cost
        self.nav *= 1 + r
        self.nav_hist.append(self.nav)
        self.cur, self.k = int(a), self.k + 1
        done = self.k >= len(self.idx) or (not self.evaluate and self.k - self.k0 >= EP_LEN)
        obs = self._obs() if not done else np.zeros(self.observation_space.shape, np.float32)
        return obs, float(np.log1p(r)), done, False, {}


def run_router(model, W, Rn, X, idx, mode):
    env = RouterEnv(W, Rn, X, idx, mode, np.random.default_rng(0), evaluate=True)
    obs, _ = env.reset()
    choices, done = [], False
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        choices.append(int(a))
        obs, _, done, _, _ = env.step(a)
    return np.asarray(choices)


def stats(r):
    v = np.cumprod(1 + r)
    return {"수익률": v[-1] - 1, "샤프": r.mean() / (r.std() + 1e-12) * np.sqrt(365), "MDD": (v / np.maximum.accumulate(v) - 1).min()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    C, V = load_daily()
    W, Rn = expert_weights(C, V)
    days = np.arange(len(C) - 1)  # 마지막 날은 다음 날 수익 없음
    alone = {e: simulate(W, Rn, np.full(len(days), j), days) for j, e in enumerate(EXPERTS)}
    Xdf = features(C, np.stack([np.append(alone[e], 0.0) for e in EXPERTS], axis=1))
    idx_of = {k: np.array([i for i in days if a <= str(C.index[i].date()) <= b and Xdf.iloc[i].notna().all()])
              for k, (a, b) in SPLITS.items()}
    mu, sd = Xdf.iloc[idx_of["train"]].mean(), Xdf.iloc[idx_of["train"]].std() + 1e-9
    X = ((Xdf - mu) / sd).fillna(0.0).to_numpy(np.float32)
    print({k: (str(C.index[v[0]].date()), str(C.index[v[-1]].date()), len(v)) for k, v in idx_of.items()})

    rows, dist_rows = [], []

    def add(name, split, r, choice=None, seed=None):
        rows.append({"전략": name, "구간": split, "시드": seed, **stats(r)})
        if choice is not None:
            share = np.bincount(choice, minlength=len(EXPERTS)) / len(choice)
            dist_rows.append({"전략": name, "구간": split, "시드": seed, "최빈 비율": share.max(),
                              **{e: share[j] for j, e in enumerate(EXPERTS)}})

    for split in ["valid", "test"]:
        idx = idx_of[split]
        for j, e in enumerate(EXPERTS):
            add(f"전문가: {e}", split, alone[e][idx])
        add("BTC 보유", split, Rn[idx, SYMS.index("BTCUSDT")])
    # B1: 검증(2024) 샤프 최고 단일 전문가
    b1 = max(range(len(EXPERTS)), key=lambda j: stats(alone[EXPERTS[j]][idx_of["valid"]])["샤프"])
    # B2: 최근 30일 성과 최고 전문가로 전환 (t 이전 정보만)
    tr30 = np.stack([pd.Series(alone[e]).shift(1).rolling(30).sum().to_numpy() for e in EXPERTS], axis=1)
    for split in ["valid", "test"]:
        idx = idx_of[split]
        add(f"B1 검증 최고 고정({EXPERTS[b1]})", split, simulate(W, Rn, np.full(len(idx), b1), idx), np.full(len(idx), b1))
        ch = np.nan_to_num(tr30[idx], nan=-1e9).argmax(1)
        add("B2 최근30일 최고 전환", split, simulate(W, Rn, ch, idx), ch)

    for mode, label in [("info", "정보 라우터(DQN)"), ("nav", "B4 가치이력 라우터(DQN, 기존 방식)")]:
        for seed in SEEDS:
            env = RouterEnv(W, Rn, X, idx_of["train"], mode, np.random.default_rng(seed))
            model = DQN("MlpPolicy", env, learning_rate=1e-3, buffer_size=50_000, learning_starts=1_000, batch_size=64,
                        gamma=0.9, train_freq=1, target_update_interval=500, exploration_fraction=0.3,
                        exploration_final_eps=0.05, policy_kwargs=dict(net_arch=[64, 64]), seed=seed, verbose=0, device="cpu")
            model.learn(TOTAL_STEPS)
            for split in ["valid", "test"]:
                idx = idx_of[split]
                ch = run_router(model, W, Rn, X, idx, mode)
                add(label, split, simulate(W, Rn, ch, idx), ch, seed)
            print(f"{label} seed {seed} 완료", flush=True)

    res, dist = pd.DataFrame(rows), pd.DataFrame(dist_rows)
    res.to_csv(OUT / "factor_router_pit_results.csv", index=False, encoding="utf-8-sig")
    dist.to_csv(OUT / "factor_router_pit_choices.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 220)
    summ = res.groupby(["전략", "구간"])[["수익률", "샤프", "MDD"]].agg(["mean", "std"]).round(3)
    print(summ.to_string())
    print(dist.groupby(["전략", "구간"])[["최빈 비율"] + EXPERTS].mean().round(2).to_string())

    m = res.groupby(["전략", "구간"])["샤프"].mean()
    dmax = dist.groupby(["전략", "구간"])["최빈 비율"].mean()
    b1n = f"B1 검증 최고 고정({EXPERTS[b1]})"
    ok = all(m[("정보 라우터(DQN)", s)] > max(m[(b1n, s)], m[("B2 최근30일 최고 전환", s)]) for s in ["valid", "test"])
    nc = all(dmax[("정보 라우터(DQN)", s)] < 0.9 for s in ["valid", "test"])
    print(f"\n[사전 등록 판정] 샤프 우위(검증·테스트 모두): {ok} | 붕괴 없음(<90%): {nc} → {'성공' if ok and nc else '실패'}")


if __name__ == "__main__":
    sys.exit(main())
