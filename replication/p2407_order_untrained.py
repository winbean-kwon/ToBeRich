"""Exploratory P24-07 follow-ups (pre-registered in notes/degenerate_policy_baseline_prereg.md, sections 2-3).

Same environment as the author script draw/algo/knowledgement_drill_ddpg.py @93c273f (FinRL StockTradingEnv,
5 tickers, hmax 100, initial 10,000, cost 0.1%, reward_scaling 1e-4, trade env risk_indicator_col='vix') and the
author's own split files. The prediction loop mirrors finrl DRLAgent.DRL_prediction (deterministic=True), except
that the policy observes the state mapped back to the original ticker order and its action is mapped to the
environment's ticker order (closed loop). With the identity permutation this is exactly DRL_prediction.

  O (order): models = author checkpoint + our trained seeds 0-4; all 120 orderings of the 5 tickers in the env.
  U (untrained): SB3 DDPG built by agent.get_model("ddpg", seed=s) on the training env, s = 0..4, no learning;
                 evaluated with the identity ordering.

Usage: python -I p2407_order_untrained.py AUTHOR_DIR OUT_DIR(our runs) RESULT_JSON
"""
import contextlib
import io
import itertools
import json
import sys

import numpy as np
import pandas as pd

AUTHOR_DIR, RUNS, OUT = sys.argv[1:4]
TICS = ["AAPL", "BA", "CRM", "UNH", "V"]
N = 5
SAT = 0.99


def setup():
    from finrl.config import INDICATORS
    from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
    train = pd.read_csv(f"{AUTHOR_DIR}/train_data.csv")
    train = train.set_index(train.columns[0]); train.index.names = [""]
    trade = pd.read_csv(f"{AUTHOR_DIR}/trade_data.csv", index_col=0, parse_dates=["date"]); trade.index.name = None
    state_space = 1 + 2 * N + len(INDICATORS) * N
    kw = {"hmax": 100, "initial_amount": 10000, "num_stock_shares": [0] * N, "buy_cost_pct": [0.001] * N,
          "sell_cost_pct": [0.001] * N, "state_space": state_space, "stock_dim": N,
          "tech_indicator_list": INDICATORS, "action_space": N, "reward_scaling": 1e-4}
    return StockTradingEnv, train, trade, kw, len(INDICATORS)


def reorder(trade, perm):
    rank = {t: i for i, t in enumerate(perm)}
    d = trade.copy(); d["_day"] = d.index; d["_r"] = d["tic"].map(rank)
    d = d.sort_values(["_day", "_r"], kind="stable")
    d.index = d["_day"].values; d.index.name = None
    return d.drop(columns=["_day", "_r"])


def run(model, Env, trade, kw, n_ind, perm):
    p = [TICS.index(t) for t in perm]          # env column j holds original ticker p[j]
    inv = np.argsort(p)                         # original ticker i sits at env column inv[i]
    nblocks = 2 + n_ind

    def to_orig(obs):
        o = obs.copy()
        for b in range(nblocks):
            s = 1 + b * N
            o[:, s:s + N] = obs[:, s:s + N][:, inv]
        return o

    env = Env(df=reorder(trade, perm), risk_indicator_col="vix", **kw)
    test_env, obs = env.get_sb_env()
    test_env.reset()
    max_steps = len(env.df.index.unique()) - 1
    raw = []
    acc = acts = None
    for i in range(len(env.df.index.unique())):
        a, _ = model.predict(to_orig(obs), deterministic=True)
        raw.append(a[0].copy())
        obs, r, dones, info = test_env.step(a[:, p])
        if i == max_steps - 1:
            acc = test_env.env_method(method_name="save_asset_memory")[0]
            acts = test_env.env_method(method_name="save_action_memory")[0]
        if dones[0]:
            break
    acts = acts[[t for t in TICS]] if set(TICS) <= set(acts.columns) else acts
    return acc, acts, np.array(raw)


def sharpe(v):
    r = pd.Series(v).pct_change()
    return float((r.mean() - 0.02 / 252) / r.std() * np.sqrt(252))


def predict_day1(raw0_orig, perm, close0_orig, cash=10000.0, cost=0.001):
    """Prediction fixed in advance: int(a*100) per asset; buy in descending order of that integer, ties broken by
    higher env column first (np.argsort on small int arrays keeps ascending index; FinRL reverses it)."""
    p = [TICS.index(t) for t in perm]
    a = (raw0_orig[p] * 100).astype(int)       # env order
    order = sorted([j for j in range(N) if a[j] > 0], key=lambda j: (-a[j], -j))
    held = {}
    for j in order:
        px = close0_orig[p[j]]
        n = min(int(cash // (px * (1 + cost))), a[j])
        cash -= n * px * (1 + cost)
        if n:
            held[TICS[p[j]]] = n
    return held


def bh_fit(trade, values, tol=0.01):
    px = trade.pivot(index="date", columns="tic", values="close").sort_index()[TICS].values
    v = np.asarray(values, float)
    for d in range(1, 31):
        P, y = px[d:], v[d:]
        X = np.column_stack([np.ones(len(P)), P])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        n = np.rint(coef[1:]); c = float(np.mean(y - P @ n))
        if (n >= 0).all() and float(np.max(np.abs(y - c - P @ n))) <= tol:
            return d
    return None


def main():
    from finrl.agents.stablebaselines3.models import DRLAgent
    from stable_baselines3 import DDPG
    Env, train, trade, kw, n_ind = setup()
    close0 = trade[trade.index == 0].set_index("tic").loc[TICS, "close"].values
    res = {"O": {}, "U": {}}
    models = {"author": f"{AUTHOR_DIR}/agent_ddpg.zip"}
    models.update({f"seed{s}": f"{RUNS}/train_seed{s}/model/agent_ddpg.zip" for s in range(5)})
    stored = {"author": f"{AUTHOR_DIR}/author_originate_ddpg.csv"}
    stored.update({f"seed{s}": f"{RUNS}/train_seed{s}/data/originate_ddpg.csv" for s in range(5)})
    perms = list(itertools.permutations(TICS))
    for name, path in models.items():
        m = DDPG.load(path)
        rows = []
        for perm in perms:
            with contextlib.redirect_stdout(io.StringIO()):
                acc, acts, raw = run(m, Env, trade, kw, n_ind, perm)
            d1 = acts.iloc[0][TICS]
            held = {t: int(d1[t]) for t in TICS if d1[t] > 0}
            rows.append({"perm": "".join(t[0] if t != "CRM" else "C" for t in perm), "perm_full": list(perm),
                         "day1_buys": held, "pred_day1": predict_day1(raw[0], perm, close0),
                         "sharpe": sharpe(acc["account_value"]), "final": float(acc["account_value"].iloc[-1]),
                         "vals": acc["account_value"].values if tuple(perm) == tuple(TICS) else None,
                         "raw0": raw[0].tolist()})
        ident = [r for r in rows if r["perm_full"] == TICS][0]
        ref = pd.read_csv(stored[name], index_col=0)["account_value"].values
        ctrl = float(np.max(np.abs(ident["vals"] - ref) / np.abs(ref))) if len(ref) == len(ident["vals"]) else None
        for r in rows:
            r.pop("vals")
        hs = sorted({json.dumps(r["day1_buys"], sort_keys=True) for r in rows})
        sh = [r["sharpe"] for r in rows]
        res["O"][name] = {"control_max_rel_diff": ctrl, "control_ok": ctrl is not None and ctrl <= 1e-9,
                          "raw_action_day0": ident["raw0"],
                          "n_distinct_day1_holdings": len(hs), "distinct_day1_holdings": hs,
                          "pred_match": f"{sum(r['day1_buys'] == r['pred_day1'] for r in rows)}/{len(rows)}",
                          "sharpe_min": min(sh), "sharpe_median": float(np.median(sh)), "sharpe_max": max(sh),
                          "rows": rows}
    # U: untrained
    for s in range(5):
        env_train, _ = Env(df=train, **kw).get_sb_env()
        with contextlib.redirect_stdout(io.StringIO()):
            m = DRLAgent(env=env_train).get_model("ddpg", seed=s)
            acc, acts, raw = run(m, Env, trade, kw, n_ind, TICS)
        sat = float((np.abs(raw) >= SAT).mean())
        signs = np.sign(raw)
        const = [bool((signs[:, j] == signs[0, j]).all()) for j in range(N)]
        nz_trade_days = int((acts[TICS].abs().sum(axis=1) > 0).sum())
        res["U"][f"seed{s}"] = {"saturation_share": sat, "sign_constant_per_asset": const,
                                "all_signs_constant": all(const), "trade_days": nz_trade_days,
                                "bh_from_day": bh_fit(trade, acc["account_value"].values),
                                "sharpe": sharpe(acc["account_value"]), "raw_action_day0": raw[0].tolist(),
                                "mean_abs_action": float(np.abs(raw).mean())}
    json.dump(res, open(OUT, "w"), indent=1, default=str)
    print(json.dumps({"O": {k: {kk: v[kk] for kk in ("control_ok", "n_distinct_day1_holdings", "pred_match",
                                                        "sharpe_min", "sharpe_max")} for k, v in res["O"].items()},
                      "U": {k: {kk: v[kk] for kk in ("saturation_share", "all_signs_constant", "trade_days",
                                                        "bh_from_day")} for k, v in res["U"].items()}}, indent=1))


if __name__ == "__main__":
    main()
