"""Exploratory: untrained (randomly initialised) policies in the FinRL portfolio environment (T3), as a baseline for
the trained-policy diagnostics. Pre-registered in notes/degenerate_policy_baseline_prereg.md section 1.

Same data, window (W0), environment, hyperparameters and seeds as finrl_t3_run.py; the model is built with
agent.get_model(algo, model_kwargs, seed) and NOT trained. Predictions: official (deterministic=False) and
deterministic, through the same _predict as O1/O6. The same descriptive metrics are computed from the stored
trained-policy files (o1/: official W0 a; o6/: W0 a sto/det) for comparison.

Usage: PYTHONPATH=.t3env/pylib python3 replication/finrl_untrained_baseline.py --fm .t3env/fm RESULT_JSON
"""
import contextlib
import io
import json
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import finrl_t3_run as T  # noqa: E402

ALGOS = ["a2c", "ppo", "ddpg", "td3"]
EPS = 1e-6


def describe(W, raw=None):
    import numpy as np
    n = W.shape[1]
    act_share = float((0.5 * np.abs(W - 1.0 / n).sum(axis=1)).mean())
    x = np.log(W) - np.log(W).min(axis=1, keepdims=True)          # action up to a row constant (softmax inverse)
    bound_inv = float(((x <= EPS) | (np.abs(x - 1) <= EPS)).mean())
    rows = np.round(W[1:], 9)
    distinct = int(len({tuple(r) for r in rows}))
    out = {"active_share": act_share, "bound_share_inverted": bound_inv, "distinct_weight_rows_after_day1": distinct,
           "max_weight": float(W.max())}
    if raw is not None:
        out["bound_share_raw"] = float(((raw <= EPS) | (raw >= 1 - EPS)).mean())
        out["mean_raw_action"] = float(raw.mean())
    return out


def main(out_json):
    import numpy as np
    import pandas as pd
    from agents.stablebaselines3_models import DRLAgent
    df = T.load_data(); SPE = T.make_spe()
    train, trade = T.split(df, T.TRAIN[0], T.W0[0]), T.split(df, *T.W0)
    n = len(train.tic.unique()); kw = T.env_kwargs(n)
    assert n == 28
    res = {"untrained": {}, "trained": {}}
    for algo in ALGOS:
        p, _ = T.PARAMS[algo]
        for s in T.SEEDS:
            env_train, _ = SPE(df=train.copy(), **kw).get_sb_env()
            with contextlib.redirect_stdout(io.StringIO()):
                model = DRLAgent(env=env_train).get_model(algo, model_kwargs=dict(p), seed=s, verbose=0)
            for mode, det in (("sto", False), ("det", True)):
                rec = []
                orig = model.predict

                def pred(obs, deterministic=det, **k):
                    a, st = orig(obs, deterministic=deterministic)
                    rec.append(np.array(a).reshape(-1, n)[0].copy())
                    return a, st
                m = types.SimpleNamespace(predict=pred)
                r = T._predict(m, trade, kw, SPE, s, deterministic=False)   # det handled inside pred
                W = r[[c for c in r.columns if c.startswith("w_")]].values
                res["untrained"][f"{algo}_s{s}_{mode}"] = describe(W, np.array(rec))
    for algo in ALGOS:
        for s in T.SEEDS:
            for mode, f in (("official", T.D / "o1" / f"{algo}_W0_a_s{s}.csv"),
                            ("sto", T.o6_path(algo, s, "W0", "a", "sto")),
                            ("det", T.o6_path(algo, s, "W0", "a", "det"))):
                if pathlib.Path(f).exists():
                    r = pd.read_csv(f, index_col=0)
                    W = r[[c for c in r.columns if c.startswith("w_")]].values
                    res["trained"][f"{algo}_s{s}_{mode}"] = describe(W)
    json.dump(res, open(out_json, "w"), indent=1)

    def summ(d, key):
        v = [x[key] for x in d]
        return [round(float(np.median(v)), 4), round(float(min(v)), 4), round(float(max(v)), 4)]
    table = {}
    for group in ("untrained", "trained"):
        for algo in ALGOS:
            for mode in ("sto", "det", "official"):
                d = [v for k, v in res[group].items() if k.startswith(algo + "_") and k.endswith("_" + mode)]
                if d:
                    table[f"{group}:{algo}:{mode}"] = {k: summ(d, k) for k in
                                                       ("active_share", "bound_share_inverted",
                                                        "distinct_weight_rows_after_day1", "max_weight")}
    print(json.dumps(table, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    assert a[0] == "--fm"
    T.setup_fm(a[1])
    main(a[2])
