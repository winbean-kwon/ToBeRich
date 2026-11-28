"""Exploratory runner: P24-07 (Markowitz Meets Bellman) public script with the 5-ticker filter removed.

Pre-registered in notes/p2407_30stock_prereg.md (based on notes/funnel_f7x_p2407_prereg.md). Train mode only,
derived from replication/funnel_f4_p2407_run.py. Executes the author's knowledgement_drill_ddpg.py
(BMEgang/BellmanMarkwitzProject @93c273f) with these modifications only:
  1. base_folder -> our output folder; run-folder name fixed to train_seed{SEED};
  2. the raw_data.csv path -> the author's repository-root raw_data.csv (@93c273f, git blob 904e6f40...),
     downloaded to RAW_CSV. The original read -> split -> to_csv -> re-read block is kept as written
     (unlike the 5-stock runner, which had to substitute the author's 5-stock split files);
  3. the two ticker-filter lines (original lines 77 and 80: `tickers_to_keep = [...]` and the `isin` filter)
     are commented out -- this is the experimental change;
  4. get_model("ddpg") -> get_model("ddpg", seed=SEED);
  5. MPLBACKEND=Agg; torch/BLAS threads limited to THREADS (for running two seeds in parallel).
Pre-run gates (abort before training if either fails):
  G1  git blob of RAW_CSV == 904e6f40c2ea20c9ab2ae2099536f8a875775a27;
  G2  RAW_CSV with the original 5-ticker filter and data_split reproduces the author's 5-stock split files
      (final/2023-11-21_19-19-07 train_data.csv / trade_data.csv used by the 5-stock runs): same shape,
      columns, index, date/tic, and numeric max relative difference <= 1e-12.
Never prints or opens metrics: stdout/stderr go to <out>/train_seed{SEED}_stdout.log; only exit status, timings,
file existence and line counts are reported.

Usage: python p2407_30stock_run.py SEED AUTHOR_DIR RAW_CSV OUT_DIR [THREADS]
"""
import difflib
import hashlib
import json
import os
import runpy
import sys
import time
import traceback

SEED, AUTHOR_DIR, RAW_CSV, OUT = int(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]), \
    os.path.abspath(sys.argv[4])
THREADS = int(sys.argv[5]) if len(sys.argv) > 5 else 3
RAW_BLOB = "904e6f40c2ea20c9ab2ae2099536f8a875775a27"
FIVE = ['AAPL', 'CRM', 'V', 'UNH', 'BA']
for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[k] = str(THREADS)
os.environ["MPLBACKEND"] = "Agg"
os.makedirs(OUT, exist_ok=True)


def git_blob(path):
    data = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def gates():
    import numpy as np
    import pandas as pd
    from finrl.meta.preprocessor.preprocessors import data_split
    g = {"G1_raw_blob": git_blob(RAW_CSV)}
    g["G1"] = g["G1_raw_blob"] == RAW_BLOB
    p = pd.read_csv(RAW_CSV, parse_dates=['date'])
    del p['weight']
    five = p[p['tic'].isin(FIVE)]
    ok, worst = True, 0.0
    for start, end, fname in [('2009-01-01', '2015-01-01', 'train_data.csv'), ('2016-01-01', '2018-09-01', 'trade_data.csv')]:
        x = data_split(five, start, end).copy()
        x['date'] = x['date'].astype(str)  # as written by to_csv
        y = pd.read_csv(os.path.join(AUTHOR_DIR, fname), index_col=0)
        if x.shape != y.shape or list(x.columns) != list(y.columns) or not (x.index == y.index).all() \
                or not (x[['date', 'tic']].values == y[['date', 'tic']].values).all():
            ok = False
            continue
        num = [c for c in x.columns if c not in ('date', 'tic')]
        xv, yv = x[num].values.astype(float), y[num].values.astype(float)
        rel = np.abs(xv - yv) / np.maximum(np.abs(yv), 1e-12)
        worst = max(worst, float(np.nanmax(rel)))
        ok = ok and bool(np.array_equal(np.isnan(xv), np.isnan(yv)))
    g["G2_max_rel"] = worst
    g["G2"] = ok and worst <= 1e-12
    g["n_tickers_raw"] = int(p['tic'].nunique())
    return g


src = open(os.path.join(AUTHOR_DIR, "knowledgement_drill_ddpg.py"), encoding="utf-8").read()
new = src


def sub(old, rep, count=1):
    global new
    assert new.count(old) == count, (old, new.count(old))
    new = new.replace(old, rep)


# 1. output folder, fixed run-folder name
sub('base_folder = "/Users/ganghu/Desktop/pythonProject1/final"', f'base_folder = {OUT!r}')
sub('current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")', f'current_time = "train_seed{SEED}"')
# 2. raw data path
sub('pd.read_csv("/Users/ganghu/Desktop/pythonProject1/raw_data.csv"', f'pd.read_csv({RAW_CSV!r}')
# 3. the experimental change: only the two ticker-filter lines are commented out
lines = new.split("\n")
assert lines[76].startswith("tickers_to_keep = ['AAPL', 'CRM', 'V', 'UNH', 'BA']"), lines[76]
assert lines[79] == "processed_full = processed_full[processed_full['tic'].isin(tickers_to_keep)]", lines[79]
lines[76] = "# [P24-07 30-stock runner] " + lines[76]
lines[79] = "# [P24-07 30-stock runner] " + lines[79]
new = "\n".join(lines)
# 4. seed
sub('model_ddpg = agent.get_model("ddpg")', f'model_ddpg = agent.get_model("ddpg", seed={SEED})')
# 5. threads
new = f"import torch as _t\n_t.set_num_threads({THREADS})\n" + new

script = os.path.join(OUT, f"train_seed{SEED}_script.py")
open(script, "w", encoding="utf-8").write(new)
open(os.path.join(OUT, f"train_seed{SEED}_diff.txt"), "w", encoding="utf-8").write(
    "".join(difflib.unified_diff(src.splitlines(True), new.splitlines(True), "author", "runner")))

g = gates()
res = {"mode": "train", "seed": SEED, "threads": THREADS, "gates": g}
if not (g["G1"] and g["G2"]):
    res["exception"] = "pre-run gate failed; not run"
    json.dump(res, open(os.path.join(OUT, f"train_seed{SEED}.json"), "w"), indent=1)
    print(json.dumps(res))
    sys.exit(1)

log = open(os.path.join(OUT, f"train_seed{SEED}_stdout.log"), "w")
so, se = sys.stdout, sys.stderr
sys.stdout = sys.stderr = log
t = time.time()
err = None
try:
    runpy.run_path(script, run_name="__main__")
except BaseException:
    err = traceback.format_exc()[-1500:]
finally:
    sys.stdout, sys.stderr = so, se
    log.close()
secs = time.time() - t

run_dir = os.path.join(OUT, f"train_seed{SEED}")
acct = os.path.join(run_dir, "data", "originate_ddpg.csv")
n_lines = sum(1 for _ in open(acct)) if os.path.exists(acct) else None
res.update({"seconds": secs, "exception": err, "account_csv_exists": os.path.exists(acct),
            "account_csv_lines": n_lines,
            "model_saved": os.path.exists(os.path.join(run_dir, "model", "agent_ddpg.zip"))})
json.dump(res, open(os.path.join(OUT, f"train_seed{SEED}.json"), "w"), indent=1)
print(json.dumps({k: (v if k != "exception" else (v is not None)) for k, v in res.items()}))
