"""Exploratory F7 FRONTIER (ruankie/frontier-rl @e019ce4) - one seed, Dow 30, RL_CNN.

Pre-registered in notes/funnel_f7x_frontier_prereg.md (same commit). Same mechanism as
replication/funnel_f4_frontier_wsl.py (papermill-equivalent in-process execution of the author's
notebooks, 'parameters' cell then overrides, '%%time' stripped), with paper settings:
200 episodes, train 2010-01-01..2018-01-01, backtest 2018-01-01..2020-01-01 (paper Table I).

Usage (cwd = <fresh run copy>/code/REINFORCE):
  python funnel_f7x_frontier_run.py train <SEED> <OUT_JSON>
  python funnel_f7x_frontier_run.py backtest <SEED> <OUT_JSON>
  python funnel_f7x_frontier_run.py pilot <SEED> <OUT_JSON>   # 2 episodes x first 30 pairs, training only (throughput/RSS)
TF threads are fixed to 1 (intra/inter) before the notebook runs (prereg 2, allowed modification).
plt.clf is replaced by plt.close('all') (memory shim, prereg 7).
Never prints metrics. stdout of the notebook goes to <OUT>_stdout.log (not opened).
"""
import contextlib
import io
import json
import os
import sys
import time

os.environ.setdefault("MPLBACKEND", "Agg")
MODE, SEED, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]

MARKET, MODEL = "DOW_30", "RL_CNN"
TRAIN_FROM, TRAIN_UNTIL = "2010-01-01", "2018-01-01"
TEST_FROM, TEST_UNTIL = "2018-01-01", "2020-01-01"
NB_EPISODES = 200

sys.path.insert(0, os.getcwd())
import resource  # noqa: E402
import tensorflow as tf  # noqa: E402
tf.config.threading.set_intra_op_parallelism_threads(1)
tf.config.threading.set_inter_op_parallelism_threads(1)
import market_tickers  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

# Memory shim (prereg 7, 2026-11-23): the author's training loop saves each pair's loss figure and then
# calls plt.clf() without closing it, so figures accumulate (~3 MB/pair) and the run hit the WSL OOM killer.
# After savefig, plt.clf() now closes all figures. Saved files and all computations are unchanged.
plt.clf = lambda *a, **k: plt.close("all")

PILOT = MODE == "pilot"
if PILOT:
    NB_EPISODES = 2
nb_name = "backtest_template.ipynb" if MODE == "backtest" else "train_template.ipynb"
cells = [c for c in json.load(open(nb_name))["cells"] if c["cell_type"] == "code"]
overrides = {
    "SEED_LIST": [SEED],
    "TICKERS": list(market_tickers.DOW_30_TICKER),
    "MARKET_NAME": MARKET,
    "MODEL_BASE_NAME": MODEL,
    "NB_EPISODES": NB_EPISODES,
}
if MODE in ("train", "pilot"):
    overrides.update({"FROM": TRAIN_FROM, "UNTIL": TRAIN_UNTIL, "SAVE_EVERY": 200})
else:
    overrides.update({"FROM": TEST_FROM, "UNTIL": TEST_UNTIL})

ns = {"__name__": "__main__"}
buf = io.StringIO()
t0 = time.time()
err = None
with contextlib.redirect_stdout(buf):
    try:
        for c in cells:
            src = "\n".join(ln for ln in "".join(c["source"]).splitlines() if not ln.lstrip().startswith("%%"))
            exec(compile(src, nb_name, "exec"), ns)
            if "parameters" in (c.get("metadata", {}).get("tags") or []):
                ns.update(overrides)
                if PILOT:
                    ns["GAMMA_PAIRS"] = ns["GAMMA_PAIRS"][:30]
    except Exception as e:
        err = f"{type(e).__name__}: {e}"[:500]
text = buf.getvalue()
open(OUT.replace(".json", "_stdout.log"), "w").write(text)

base = f"experiments/{MARKET}/seeded/{MODEL}"
n_models = 0
sd = f"{base}/seed_{SEED}"
if os.path.isdir(sd):
    for d in os.listdir(sd):
        p = f"{sd}/{d}/models"
        if os.path.isdir(p) and any(x.startswith(f"{MODEL}_seed_{SEED}_{NB_EPISODES}") for x in os.listdir(p)):
            n_models += 1
res = {
    "mode": MODE, "seed": SEED, "seconds": time.time() - t0,
    "max_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, "start_unix": t0, "exception": err,
    "n_models_saved_final": n_models,
    "count_train_episode_error_strings": text.count("*** error in episode"),
    "count_backtest_error_strings": text.count("**error for model"),
    "results_csv_exists": os.path.exists(f"{base}/backtests/{MARKET}_{MODEL}_seeds_{SEED}_etc.csv") if MODE == "backtest" else None,
}
json.dump(res, open(OUT, "w"))
print(json.dumps(res))
