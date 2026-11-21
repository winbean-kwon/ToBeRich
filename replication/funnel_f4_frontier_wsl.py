"""F4/F5 FRONTIER (ruankie/frontier-rl @e019ce4) driver - server WSL, CPU.

Pre-registered in notes/funnel_f4_frontier.md section 2 (same commit). Do not change after running.

What it does (papermill-equivalent, in-process so episodes can be timed):
  - reads the author's notebook code cells in order,
  - runs the cell tagged 'parameters', then our overrides (exactly what papermill injects),
  - strips IPython cell magics ('%%time') only,
  - wraps REINFORCE_soft.play_one_episode with a wall-clock timer (return value untouched),
  - writes timings / file counts / error-string counts to OUT. Never prints or stores losses or metrics.

Usage (cwd = <run copy>/code/REINFORCE):
  python funnel_f4_frontier_wsl.py train <MODEL> <OUT_JSON>
  python funnel_f4_frontier_wsl.py backtest RL_CNN <OUT_JSON>
"""
import contextlib
import io
import json
import os
import sys
import time

os.environ.setdefault("MPLBACKEND", "Agg")

MODE, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

# --- fixed parameters (section 2.3) ---
MARKET = "DOW_30"
TRAIN_FROM, TRAIN_UNTIL = "2010-01-01", "2018-01-01"   # paper Table I, Dow 30 training period
BT_FROM, BT_UNTIL = "2016-01-01", "2018-01-01"         # slice of TRAINING data (performance non-exposure)
NB_EPISODES = 2
SEED = 0

sys.path.insert(0, os.getcwd())
import REINFORCE_soft  # noqa: E402

episode_times = []   # (pair_counter_at_call, seconds)
pair_marks = []      # wall clock at each env construction (= start of a pair)
_orig_play = REINFORCE_soft.play_one_episode
_orig_env_init = REINFORCE_soft.MultiStockEnv.__init__


def timed_play(agent, env, mode="train"):
    t0 = time.perf_counter()
    r = _orig_play(agent, env, mode)
    episode_times.append(time.perf_counter() - t0)
    return r


def marked_env_init(self, *a, **k):
    pair_marks.append(time.perf_counter())
    return _orig_env_init(self, *a, **k)


REINFORCE_soft.play_one_episode = timed_play
REINFORCE_soft.MultiStockEnv.__init__ = marked_env_init

nb_name = "train_template.ipynb" if MODE == "train" else "backtest_template.ipynb"
nb = json.load(open(nb_name))
cells = [c for c in nb["cells"] if c["cell_type"] == "code"]

import market_tickers  # noqa: E402

overrides = {
    "SEED_LIST": [SEED],
    "TICKERS": list(market_tickers.DOW_30_TICKER),
    "MARKET_NAME": MARKET,
    "MODEL_BASE_NAME": MODEL,
    "NB_EPISODES": NB_EPISODES,
}
if MODE == "train":
    overrides.update({"FROM": TRAIN_FROM, "UNTIL": TRAIN_UNTIL, "SAVE_EVERY": 200})
else:
    overrides.update({"FROM": BT_FROM, "UNTIL": BT_UNTIL})

ns = {"__name__": "__main__"}
stdout_buf = io.StringIO()
t_start = time.perf_counter()
err = None
with contextlib.redirect_stdout(stdout_buf):
    try:
        for c in cells:
            src = "".join(c["source"])
            lines = [ln for ln in src.splitlines() if not ln.lstrip().startswith("%%")]
            src = "\n".join(lines)
            # a trailing bare expression (e.g. 'results_df') is a no-op under exec
            exec(compile(src, nb_name, "exec"), ns)
            if "parameters" in (c.get("metadata", {}).get("tags") or []):
                ns.update(overrides)
    except Exception as e:  # recorded, not shown with metrics
        err = f"{type(e).__name__}: {e}"[:500]
t_total = time.perf_counter() - t_start

out_text = stdout_buf.getvalue()
# store raw stdout to a file we do not open (may contain training losses)
with open(OUT.replace(".json", "_stdout.log"), "w") as f:
    f.write(out_text)

base = f"experiments/{MARKET}/seeded/{MODEL}/seed_{SEED}"
n_models = 0
if os.path.isdir(base):
    for d in os.listdir(base):
        p = f"{base}/{d}/models"
        if os.path.isdir(p) and any(x.startswith(f"{MODEL}_seed_{SEED}_{NB_EPISODES}") for x in os.listdir(p)):
            n_models += 1

res = {
    "mode": MODE, "model": MODEL, "market": MARKET, "nb_episodes": NB_EPISODES, "seed": SEED,
    "train_period": [TRAIN_FROM, TRAIN_UNTIL] if MODE == "train" else None,
    "backtest_period": [BT_FROM, BT_UNTIL] if MODE == "backtest" else None,
    "total_seconds": t_total,
    "n_pairs_started": len(pair_marks),
    "n_episodes_timed": len(episode_times),
    "episode_seconds": episode_times,
    "pair_start_offsets": [m - t_start for m in pair_marks],
    "n_models_saved_with_final_episode": n_models,
    "count_train_episode_error_strings": out_text.count("*** error in episode"),
    "count_backtest_error_strings": out_text.count("**error for model"),
    "exception": err,
    "results_csv_exists": os.path.exists(f"{base[:base.rfind('/seed_')]}/backtests/{MARKET}_{MODEL}_seeds_{SEED}_etc.csv")
    if MODE == "backtest" else None,
}
json.dump(res, open(OUT, "w"))
print(json.dumps({k: v for k, v in res.items() if k not in ("episode_seconds", "pair_start_offsets")}))
