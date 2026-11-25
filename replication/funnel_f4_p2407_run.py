"""Exploratory F4/F7x runner for P24-07 (Markowitz Meets Bellman, KDD), BMEgang/BellmanMarkwitzProject @93c273f.

Pre-registered in notes/funnel_f4_p2407_prereg.md. Executes the author's draw/algo/knowledgement_drill_ddpg.py
text with only the allowed modifications (prereg 3):
  1. the raw_data.csv read/filter/split block is replaced by loading the author's own split files from run folder
     final/2023-11-21_19-19-07 (train_data.csv is re-read by the script itself afterwards, as in the original;
     `trade` is rebuilt exactly as data_split returns it: date-parsed, index = day index);
  2. base_folder -> our output folder;
  3. mode "train": get_model("ddpg") -> get_model("ddpg", seed=SEED);
     mode "author": the training block is removed and DDPG.load points to the author's agent_ddpg.zip;
  4. MPLBACKEND=Agg.
The transformed script and its diff against the author file are saved next to the outputs.
Never prints or opens metrics: stdout/stderr go to <out>/stdout.log; only exit status, timings, file existence
and line counts are reported.

Usage: python funnel_f4_p2407_run.py {author|train} SEED AUTHOR_DIR OUT_DIR
"""
import difflib
import json
import os
import runpy
import sys
import time
import traceback

MODE, SEED, AUTHOR_DIR, OUT = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
assert MODE in ("author", "train")
os.environ["MPLBACKEND"] = "Agg"
os.makedirs(OUT, exist_ok=True)

src = open(os.path.join(AUTHOR_DIR, "knowledgement_drill_ddpg.py"), encoding="utf-8").read()
new = src


def sub(old, rep, count=1):
    global new
    assert new.count(old) == count, (old, new.count(old))
    new = new.replace(old, rep)


# 2. output folder; fixed run-folder name instead of the wall-clock name (one folder per run)
sub('base_folder = "/Users/ganghu/Desktop/pythonProject1/final"', f'base_folder = {OUT!r}')
sub('current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")', f'current_time = "{MODE}_seed{SEED}"')

# 1. input: replace read/filter/split with the author's split files
start = new.index('processed_full = pd.read_csv("/Users/ganghu/Desktop/pythonProject1/raw_data.csv"')
end_marker = "trade.to_csv(f'{data_folder}/trade_data.csv')"
end = new.index(end_marker) + len(end_marker)
replacement = (
    "# [P24-07 runner] raw_data.csv is not in the repository; use the author's split files from\n"
    "# final/2023-11-21_19-19-07/data (written by this same script right after data_split).\n"
    "import shutil as _sh\n"
    f"_sh.copy({os.path.join(AUTHOR_DIR, 'train_data.csv')!r}, f'{{data_folder}}/train_data.csv')\n"
    f"_sh.copy({os.path.join(AUTHOR_DIR, 'trade_data.csv')!r}, f'{{data_folder}}/trade_data.csv')\n"
    "trade = pd.read_csv(f'{data_folder}/trade_data.csv', index_col=0, parse_dates=['date'])\n"
    "trade.index.name = None"
)
new = new[:start] + replacement + new[end:]

if MODE == "train":
    # 3. seed
    sub('model_ddpg = agent.get_model("ddpg")', f'model_ddpg = agent.get_model("ddpg", seed={SEED})')
else:
    # author checkpoint: drop training, load the author's model
    t0 = new.index("agent = DRLAgent(env = env_train)")
    t1_marker = 'trained_ddpg.save(model_folder + "/agent_ddpg")'
    t1 = new.index(t1_marker) + len(t1_marker)
    new = new[:t0] + "# [P24-07 runner] training removed (author checkpoint mode)" + new[t1:]
    sub('trained_ddpg = DDPG.load(model_folder + "/agent_ddpg")',
        f'trained_ddpg = DDPG.load({os.path.join(AUTHOR_DIR, "agent_ddpg.zip")!r})')

script = os.path.join(OUT, f"{MODE}_seed{SEED}_script.py")
open(script, "w", encoding="utf-8").write(new)
open(os.path.join(OUT, f"{MODE}_seed{SEED}_diff.txt"), "w", encoding="utf-8").write(
    "".join(difflib.unified_diff(src.splitlines(True), new.splitlines(True), "author", "runner")))

log = open(os.path.join(OUT, f"{MODE}_seed{SEED}_stdout.log"), "w")
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

run_dir = os.path.join(OUT, f"{MODE}_seed{SEED}")
acct = os.path.join(run_dir, "data", "originate_ddpg.csv")
n_lines = sum(1 for _ in open(acct)) if os.path.exists(acct) else None
res = {"mode": MODE, "seed": SEED, "seconds": secs, "exception": err,
       "account_csv_exists": os.path.exists(acct), "account_csv_lines": n_lines,
       "model_saved": os.path.exists(os.path.join(run_dir, "model", "agent_ddpg.zip")) if MODE == "train" else None}
json.dump(res, open(os.path.join(OUT, f"{MODE}_seed{SEED}.json"), "w"), indent=1)
print(json.dumps({k: (v if k != "exception" else (v is not None)) for k, v in res.items()}))
