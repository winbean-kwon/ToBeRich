"""T4 MARS (github.com/jiayiderekchen/MARS) — O1 실행기·판정 계산.

사전 등록: notes/mars_t4_o1_prereg.md(5e3cd6e). 공식 코드 파일은 고치지 않고 이 파일의 런타임 래퍼만 쓴다.

환경 변수: MARS_WORK(코드 체크아웃), MARS_OUT(결과. Colab은 Drive data/mars_t4), MARS_THREADS(선택, torch 스레드 수).

  python mars_t4.py setup                    공식 저장소 체크아웃(L=2561606, N=6ca2051), 커밋·데이터 해시 확인
  python mars_t4.py pilot <L|N> <device>     2 에피소드 시간만 측정(학습 데이터만, 검증·테스트 없음) → pilot_*.json
  python mars_t4.py run <L|N> <seed> <device> 학습 + 테스트 1회. 완료 시드는 다시 돌리지 않는다
  python mars_t4.py ckpt                     번들 체크포인트 C 평가 2회(결정성 점검 포함)
  python mars_t4.py judge                    O1 판정 계산 → judge_o1.json
  python mars_t4.py queue                    대기열: C → L 2개·N 1개 동시. 완료 시드는 건너뛰고 끊긴 시드는 처음부터 다시 돌린다
  python mars_t4.py status                   진행 상황(완료 수·시간만, 성과 없음)
  python mars_t4.py smoke <L|N> <device>     전 경로 시험: 10 에피소드, 검증·테스트 자리에 학습 데이터 조각(날짜만 2024)을 넣는다.
                                             실제 검증·테스트 데이터로 정책을 돌리지 않으며, 결과 파일 존재만 확인하고 지운다

런타임 래퍼(모두 계산 결과를 바꾸지 않음, 사전 등록 2.2):
  - config.SEED, config.RESULT_DIR 지정.
  - 학습 중 log_trade·log_daily_performance 끄기(N의 `not train` 조건과 같음). 호출 앞의 계산은 그대로 실행된다.
  - plot_* 끄기(그림만 그림).
  - 표준 출력은 파일로만 보낸다. 시드가 모두 끝나 judge를 돌리기 전에는 성과를 화면에 내지 않는다.
"""
import contextlib, fcntl, hashlib, json, math, os, pathlib, shutil, socket, subprocess, sys, time

REPO = "https://github.com/jiayiderekchen/MARS.git"
COMMITS = {
    "L": "2561606",  # 2025-07-30, 논문 v1 직전
    "N": "6ca2051",  # 2026-07-10, 저자 수정본
}
BLOBS = {  # git blob 해시 앞 8자리(사전 등록 1장)
    "data/test_data.csv": "eb942233",
    "data/training_data.csv": "2e560545",
    "data/validation_data.csv": "95500c9a",
    "data/DJI.csv": "d7d32540",
}
SEEDS = [42, 123, 0, 1, 2, 3, 4, 5, 6, 7]
PILOT_EPISODES = 2
FULL_EPISODES = {"L": 300, "N": 200}
CKPT = "checkpoints/dji2024_seed123_ep130"

# 논문 Table 2, DJI 2024(AAAI-26 pp. 20096)
PAPER = {"CR": 29.50, "AR": 31.19, "SR": 2.84, "AVol": 10.99, "MDD": -5.39}
PAPER_DJI = {"CR": 15.36, "AR": 16.19, "SR": 1.41, "AVol": 11.51, "MDD": -6.06}
TOL = {"CR": 7.07, "SR": 0.715}
W240 = ("2024-01-17", "2024-12-27")
BUSY = 75  # 같은 시드가 이미 실행 중
SLOTS = {"L": 2, "N": 1}
STOP_DATE = "2026-11-24"  # 사전 등록 3장. 이날이 지나면 새 실행을 멈추고 끝난 시드로 판정한다
MIN_FREE_GB = 1.0
MAX_FAILS = 3


def work():
    return pathlib.Path(os.environ.get("MARS_WORK", "/content/mars_t4_work")).resolve()


def out():
    p = pathlib.Path(os.environ.get("MARS_OUT", "/content/mars_t4_out")).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def sh(*a, cwd=None):
    return subprocess.check_output(a, cwd=cwd, text=True).strip()


# ---------------------------------------------------------------- setup
def setup():
    w = work()
    base = w / "repo"
    if not base.exists():
        w.mkdir(parents=True, exist_ok=True)
        sh("git", "clone", "--quiet", REPO, str(base))
    meta = {}
    for c, h in COMMITS.items():
        t = w / c
        if not t.exists():
            sh("git", "worktree", "add", "--quiet", "--detach", str(t), h, cwd=base)
        full = sh("git", "rev-parse", "HEAD", cwd=t)
        if not full.startswith(h):
            sys.exit(f"{c}: HEAD {full} != {h}")
        for f, b in BLOBS.items():
            got = sh("git", "rev-parse", f"HEAD:{f}", cwd=t)
            if not got.startswith(b):
                sys.exit(f"{c}: {f} blob {got} != {b}")
        if sh("git", "status", "--porcelain", cwd=t):
            sys.exit(f"{c}: 작업 트리가 원본과 다름")
        meta[c] = full
    (out() / "setup.json").write_text(json.dumps(meta, indent=1))
    print("setup ok", meta)


# ---------------------------------------------------------------- 래퍼
class Ctx:
    """체크아웃 c의 공식 main 모듈을 불러와 기록용 래퍼만 씌운다."""

    def __init__(self, cond, seed, result_dir):
        self.cond = cond
        code = work() / cond
        os.chdir(code)
        sys.path.insert(0, str(code))
        os.environ["MPLBACKEND"] = "Agg"
        import torch
        if os.environ.get("MARS_THREADS"):
            torch.set_num_threads(int(os.environ["MARS_THREADS"]))
        import config, utils, main as M
        from multi_agent import MultiAgentSystem as MAS
        self.torch, self.config, self.utils, self.M, self.MAS = torch, config, utils, M, MAS
        config.SEED = seed
        config.RESULT_DIR = str(result_dir) + "/"
        self.training = False
        self.ep_times = []
        self.blend = {"steps": 0, "blended": 0}
        self._risk_calls = 0
        self._count = False
        self._wrap()

    def _wrap(self):
        M, utils, MAS = self.M, self.utils, self.MAS
        M.plot_training_curves = lambda *a, **k: None
        M.plot_test_results = lambda *a, **k: None

        for name in ("log_trade", "log_daily_performance"):
            orig = getattr(utils, name)
            setattr(utils, name, (lambda o: lambda *a, **k: None if self.training else o(*a, **k))(orig))

        orig_ep = M.run_episode

        def run_episode(*a, **k):
            train = k.get("train", a[3] if len(a) > 3 else True)
            self.training = bool(train)
            t0 = time.time()
            try:
                return orig_ep(*a, **k)
            finally:
                if train:
                    self.ep_times.append(time.time() - t0)
                self.training = False
        M.run_episode = run_episode

        # 행동 혼합 발동 횟수: select_action 한 번에 estimate_risk가 2회 이상 불리면 혼합 경로다(사전 등록 2장).
        orig_risk = utils.estimate_risk

        def estimate_risk(*a, **k):
            self._risk_calls += 1
            return orig_risk(*a, **k)
        utils.estimate_risk = estimate_risk
        orig_sel = MAS.select_action

        def select_action(s, *a, **k):
            self._risk_calls = 0
            r = orig_sel(s, *a, **k)
            if self._count:
                self.blend["steps"] += 1
                self.blend["blended"] += int(self._risk_calls > 1)
            return r
        MAS.select_action = select_action

        # 쓰지 않는 중간 체크포인트를 저장하지 않는다(디스크). 저장은 파일만 쓰고 난수·계산에 영향이 없다(사전 등록 2.2의 5번).
        # L은 best_models로 테스트하므로 models_episode_*가 필요 없고, N은 BMID 대역 안의 것만 쓴다.
        orig_save = MAS.save_models
        cond, config = self.cond, self.config

        def save_models(s, path):
            name = os.path.basename(str(path).rstrip("/"))
            if name.startswith("models_episode_"):
                ep = int(name.rsplit("_", 1)[1])
                if cond == "L" or not (config.BMID_EPISODE_MIN <= ep <= config.BMID_EPISODE_MAX):
                    return None
            return orig_save(s, path)
        MAS.save_models = save_models

    def main(self, *argv):
        sys.argv = ["main.py", *argv]
        self.M.main()


def env_meta(device):
    import numpy, pandas, torch
    return {"host": socket.gethostname(), "device": device, "torch": torch.__version__, "numpy": numpy.__version__,
            "pandas": pandas.__version__, "python": sys.version.split()[0], "threads": torch.get_num_threads(),
            "cuda": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "time": time.strftime("%F %T %z")}


# ---------------------------------------------------------------- pilot: 시간만
def pilot(cond, device):
    rd = work() / f"pilot_{cond}_{device}"
    shutil.rmtree(rd, ignore_errors=True)
    rd.mkdir(parents=True)
    with open(rd / "stdout.log", "w") as f, contextlib.redirect_stdout(f):
        c = Ctx(cond, 42, rd)
        c.config.EPISODES = PILOT_EPISODES
        c.config.EVAL_FREQUENCY = 10  # 2 에피소드에서는 검증이 돌지 않는다
        err = None
        try:
            c.main("--mode", "train", "--device", device)
        except Exception as e:  # 2 에피소드용 통계 저장 단계의 길이 불일치 등. 시간은 이미 측정됐다
            err = f"{type(e).__name__}: {e}"
    if len(c.ep_times) < PILOT_EPISODES:
        sys.exit(f"pilot 실패: {err}. {rd}/stdout.log 확인")
    # 첫 에피소드는 초기 64스텝 동안 갱신이 없어 마지막 값으로 환산한다
    sec = c.ep_times[-1]
    r = {"cond": cond, "episodes": PILOT_EPISODES, "episode_sec": c.ep_times, "after_episodes_error": err,
         "projected_hours_per_seed": sec * FULL_EPISODES[cond] / 3600, **env_meta(device)}
    p = out() / f"pilot_{cond}_{device}_{socket.gethostname()}.json"
    p.write_text(json.dumps(r, indent=1))
    shutil.rmtree(rd, ignore_errors=True)
    print(json.dumps({k: r[k] for k in ("cond", "device", "episode_sec", "projected_hours_per_seed", "threads", "after_episodes_error")}))


# ---------------------------------------------------------------- run
def _test_with_extras(c):
    """공식 test_model을 그대로 한 번 부른 뒤, 보조용 W240 현금 시작 평가를 이어서 한다(사전 등록 4.2)."""
    M, config = c.M, c.config
    orig_test = M.test_model

    def test_model(multi_agent, test_data, test_returns_history, baseline_data=None):
        weights0 = multi_agent.agent_weights.copy()
        c._count = True
        r = orig_test(multi_agent, test_data, test_returns_history, baseline_data)
        c._count = False
        (pathlib.Path(config.RESULT_DIR) / "blend.json").write_text(json.dumps(c.blend))
        # 보조: 입력을 W240으로 잘라 현금에서 시작
        import pandas as pd
        idx = pd.Series(test_data.index).astype(str).str[:10].values  # 서머타임으로 UTC 오프셋이 섞여 있어 문자열로 자른다
        cut = test_data[(idx >= W240[0]) & (idx <= W240[1])]
        prev, config.RESULT_DIR = config.RESULT_DIR, config.RESULT_DIR + "w240_cash/"
        os.makedirs(config.RESULT_DIR + "log", exist_ok=True)
        multi_agent.agent_weights = weights0
        orig_test(multi_agent, cut, c.utils.calculate_returns(cut[[k for k in cut.columns if "_Adj Close" in k]]), baseline_data)
        config.RESULT_DIR = prev
        return r
    M.test_model = test_model


KEEP = ["test_results_detailed.csv", "test_results_metrics.csv", "blend.json", "bmid_selected_checkpoint.json",
        "training_validation_stats.csv", "training_stats.csv", "stdout.log"]


def run(cond, seed, device):
    dst = out() / cond / f"seed_{seed}"
    dst.mkdir(parents=True, exist_ok=True)
    if (dst / "done.json").exists():
        print(f"{cond} seed {seed}: 이미 완료. 재실행하지 않음(사전 등록 2.1)")
        return
    lock = open(dst / "run.lock", "w")  # 프로세스가 죽으면 자동 해제. 같은 시드가 겹쳐 돌지 않게 한다
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(BUSY)
    with open(dst / "attempts.jsonl", "a") as f:
        f.write(json.dumps({"start": time.strftime("%F %T %z"), **env_meta(device)}) + "\n")
    rd = work() / "runs" / cond / f"seed_{seed}"
    shutil.rmtree(rd, ignore_errors=True)
    rd.mkdir(parents=True)
    t0 = time.time()
    with open(rd / "stdout.log", "w") as f, contextlib.redirect_stdout(f):
        c = Ctx(cond, seed, rd)
        _test_with_extras(c)
        c.main("--mode", "both", "--device", device)
    if not (rd / "test_results_detailed.csv").exists():
        sys.exit(f"{cond} seed {seed}: 테스트 결과 없음. {rd}/stdout.log 확인")
    for k in KEEP:
        if (rd / k).exists():
            shutil.copy2(rd / k, dst / k)
    for p in rd.glob("*.csv"):  # 통계 파일 이름은 커밋마다 다를 수 있다
        shutil.copy2(p, dst / p.name)
    if (rd / "w240_cash" / "test_results_detailed.csv").exists():
        shutil.copy2(rd / "w240_cash" / "test_results_detailed.csv", dst / "w240_cash_detailed.csv")
    (dst / "done.json").write_text(json.dumps({"seconds": time.time() - t0, "cpu_seconds": time.process_time(), "episode_sec_mean": sum(c.ep_times) / max(len(c.ep_times), 1),
                                               "episodes_run": len(c.ep_times), **env_meta(device)}, indent=1))
    shutil.rmtree(rd, ignore_errors=True)  # 체크포인트 삭제(사전 등록 2.2의 5번)
    print(f"{cond} seed {seed} 완료, {time.time() - t0:.0f}초")


def smoke(cond, device):
    """실제 검증·테스트 성과를 보지 않고 run의 전 경로(검증, 체크포인트 선택, 테스트, W240 현금 시작, 판정 계산)를 시험한다."""
    import pandas as pd
    root = work() / f"smoke_{cond}"
    shutil.rmtree(root, ignore_errors=True)
    (root / "data").mkdir(parents=True)
    code = work() / cond / "data"
    tr = pd.read_csv(code / "training_data.csv")
    dates = pd.read_csv(code / "test_data.csv", usecols=["Date"]).Date.values  # 날짜 열만 읽는다
    fake = tr.iloc[-len(dates):].copy()
    fake["Date"] = dates
    fake.to_csv(root / "data" / "fake_test.csv", index=False)
    val = tr.iloc[-(len(dates) + 250):-len(dates)]
    val.to_csv(root / "data" / "fake_val.csv", index=False)
    rd = root / "run"
    rd.mkdir()
    with open(rd / "stdout.log", "w") as f, contextlib.redirect_stdout(f):
        c = Ctx(cond, 42, rd)
        c.config.EPISODES = 10
        if cond == "N":  # 10 에피소드 시험에서도 실제와 같은 BMID 대역 경로를 지나게 한다
            c.config.BMID_EPISODE_MIN = c.config.BMID_EPISODE_MAX = 10
        c.config.VALIDATION_DATA_PATH = str(root / "data" / "fake_val.csv")
        c.config.TEST_DATA_PATH = str(root / "data" / "fake_test.csv")
        _test_with_extras(c)
        c.main("--mode", "both", "--device", device)
    need = ["test_results_detailed.csv", "test_results_metrics.csv", "blend.json", "w240_cash/test_results_detailed.csv"]
    missing = [k for k in need if not (rd / k).exists()]
    if missing:
        sys.exit(f"smoke 실패 {cond}: 없음 {missing}. {rd}/stdout.log 확인")
    df = pd.read_csv(rd / "test_results_detailed.csv")
    cash = pd.read_csv(rd / "w240_cash" / "test_results_detailed.csv")
    n240 = len(slice_w240(df))
    blend = json.loads((rd / "blend.json").read_text())
    ok = len(df) == 251 and n240 == 240 and len(cash) == 240 and blend["steps"] == 250
    print(json.dumps({"cond": cond, "rows": len(df), "w240_rows": n240, "cash_rows": len(cash), "blend_steps": blend["steps"], "episodes": len(c.ep_times), "files": sorted(p.name for p in rd.iterdir())[:30], "ok": ok}, ensure_ascii=False))
    if not ok:
        sys.exit("smoke 형태 점검 실패")
    shutil.rmtree(root, ignore_errors=True)


def ckpt():
    dst = out() / "C"
    dst.mkdir(parents=True, exist_ok=True)
    rd = work() / "runs" / "C"
    shutil.rmtree(rd, ignore_errors=True)
    rd.mkdir(parents=True)
    with open(rd / "stdout.log", "w") as f, contextlib.redirect_stdout(f):
        c = Ctx("N", 123, rd)
        orig_test, c._count = c.M.test_model, True
        for i in (1, 2):
            c.main("--mode", "test", "--model_path", CKPT, "--device", "cpu")
            shutil.copy2(rd / "test_results_detailed.csv", dst / f"run{i}_detailed.csv")
            shutil.copy2(rd / "test_results_metrics.csv", dst / f"run{i}_metrics.csv")
    (dst / "done.json").write_text(json.dumps(env_meta("cpu"), indent=1))
    print("C 완료")


# ---------------------------------------------------------------- 대기열
def _progress():
    r = {}
    for c in SLOTS:
        d = [s for s in SEEDS if (out() / c / f"seed_{s}" / "done.json").exists()]
        att = 0
        for s in SEEDS:
            f = out() / c / f"seed_{s}" / "attempts.jsonl"
            if f.exists():
                att += sum(1 for _ in open(f))
        r[c] = {"done": d, "attempts": att}
    r["C"] = {"done": (out() / "C" / "done.json").exists()}
    return r


def _fails():
    f = out() / "failures.jsonl"
    return [json.loads(x) for x in open(f)] if f.exists() else []


def queue():
    """launchd가 로그인할 때마다 띄운다. 끊기면 다시 실행해도 안전하다(완료 건너뜀, 미완료 시드는 처음부터, 시도 전부 기록)."""
    qlock = open(out() / "queue.lock", "w")
    try:
        fcntl.flock(qlock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("대기열이 이미 실행 중")
        return
    me = str(pathlib.Path(__file__).resolve())
    running = {}

    def start(key, args):
        logf = open(out() / "queue_children.log", "a")
        env = dict(os.environ, MARS_THREADS=os.environ.get("MARS_THREADS", "1"))
        running[key] = subprocess.Popen([sys.executable, me, *args], stdout=logf, stderr=logf, env=env)

    while True:
        for k, p in list(running.items()):
            rc = p.poll()
            if rc is None:
                continue
            del running[k]
            if rc not in (0, BUSY) and rc > 0:  # 파이썬 오류만 실패로 센다. 전원 차단·kill(음수)은 세지 않는다
                with open(out() / "failures.jsonl", "a") as f:
                    f.write(json.dumps({"key": k, "rc": rc, "time": time.strftime("%F %T %z")}) + "\n")
        today = time.strftime("%F")
        fails = _fails()
        nfail = lambda k: sum(1 for x in fails if x["key"] == k)
        free_gb = shutil.disk_usage(str(out())).free / 2 ** 30
        stopped = today > STOP_DATE
        pending = 0
        if stopped:
            for p in running.values():
                p.terminate()
        else:
            if not (out() / "C" / "done.json").exists() and nfail("C") < MAX_FAILS:
                pending += 1
                if "C" not in running and free_gb >= MIN_FREE_GB:
                    start("C", ["ckpt"])
            for c, slots in SLOTS.items():
                for s in SEEDS:
                    k = f"{c}_{s}"
                    if (out() / c / f"seed_{s}" / "done.json").exists() or nfail(k) >= MAX_FAILS:
                        continue
                    pending += 1
                    n = sum(1 for x in running if x.startswith(c + "_"))
                    if k not in running and n < slots and free_gb >= MIN_FREE_GB:
                        start(k, ["run", c, str(s), "cpu"])
        (out() / "queue_status.json").write_text(json.dumps({
            "updated": time.strftime("%F %T %z"), "running": sorted(running), "pending": pending, "free_gb": round(free_gb, 2),
            "stopped_by_date": stopped, "failures": fails, "waiting_for_disk": free_gb < MIN_FREE_GB, **_progress()}, indent=1))
        if stopped or (pending == 0 and not running):
            return
        time.sleep(60)


def status():
    f = out() / "queue_status.json"
    print(f.read_text() if f.exists() else "대기열 기록 없음")


# ---------------------------------------------------------------- 판정
def metrics(p):
    """p: 가치 경로(numpy). 사전 등록 4장 정의."""
    import numpy as np
    p = np.asarray(p, float)
    r = p[1:] / p[:-1] - 1
    cr = p[-1] / p[0] - 1
    ar = (1 + cr) ** (252 / len(p)) - 1
    vol = r.std(ddof=0) * math.sqrt(252)
    return {"CR": 100 * cr, "AR": 100 * ar, "AVol": 100 * vol, "SR": ar / vol,
            "MDD": 100 * (p / np.maximum.accumulate(p) - 1).min(), "SR_code": r.mean() / r.std(ddof=0) * math.sqrt(252), "n": len(p)}


def slice_w240(df, col="portfolio_value", date="date"):
    import pandas as pd
    d = pd.to_datetime(df[date].astype(str).str[:10])
    return df.loc[(d >= W240[0]) & (d <= W240[1]), col].values


def reference():
    """DJI·1/N(비용 0, 0.1%). 번들 데이터로 계산."""
    import numpy as np, pandas as pd
    base = work() / "L" / "data"
    d = pd.read_csv(base / "DJI.csv")
    d["date"] = d["Date"].astype(str).str[:10]
    d = d[(d.date >= "2024-01-01") & (d.date <= "2024-12-31")]
    t = pd.read_csv(base / "test_data.csv")
    t["date"] = t["Date"].astype(str).str[:10]
    P = t[[k for k in t.columns if k.endswith("_Adj Close")]].values
    R = P[1:] / P[:-1] - 1
    ew0 = np.r_[1, np.cumprod(1 + R.mean(1))]
    # 비용 0.1%: 매일 드리프트 가중치에서 등가중으로 되돌리는 회전율에 부과
    n = P.shape[1]
    w = np.ones(n) / n
    v = [1.0]
    for i in range(len(R)):
        g = 1 + (w * R[i]).sum()
        drift = w * (1 + R[i]) / g
        v.append(v[-1] * g * (1 - 0.001 * np.abs(np.ones(n) / n - drift).sum()))
    ew1 = np.array(v)
    frame = pd.DataFrame({"date": t.date, "ew0": ew0, "ew1": ew1})
    return {"DJI": {"W240": metrics(slice_w240(d, "Close")), "W251": metrics(d.Close.values)},
            "EW_cost0": {"W240": metrics(slice_w240(frame, "ew0")), "W251": metrics(ew0)},
            "EW_cost10bp": {"W240": metrics(slice_w240(frame, "ew1")), "W251": metrics(ew1)}}


def judge_cond(cond, ref):
    import numpy as np, pandas as pd
    rows = {}
    for s in SEEDS:
        d = out() / cond / f"seed_{s}"
        if not (d / "done.json").exists():
            continue
        df = pd.read_csv(d / "test_results_detailed.csv")
        rows[s] = {"W240": metrics(slice_w240(df)), "W251": metrics(df.portfolio_value.values)}
        if (d / "w240_cash_detailed.csv").exists():
            rows[s]["W240_cash"] = metrics(pd.read_csv(d / "w240_cash_detailed.csv").portfolio_value.values)
        if (d / "blend.json").exists():
            rows[s]["blend"] = json.loads((d / "blend.json").read_text())
    n = len(rows)
    res = {"n_seeds": n, "seeds": rows}
    if n == 0:
        return res
    cr = np.array([rows[s]["W240"]["CR"] for s in rows])
    sr = np.array([rows[s]["W240"]["SR"] for s in rows])
    med = {"CR": float(np.median(cr)), "SR": float(np.median(sr))}
    res["median"] = med
    res["within_tol"] = int(((abs(cr - PAPER["CR"]) <= TOL["CR"]) & (abs(sr - PAPER["SR"]) <= TOL["SR"])).sum())
    res["R1"] = None if n < 3 else bool(abs(med["CR"] - PAPER["CR"]) <= TOL["CR"] and abs(med["SR"] - PAPER["SR"]) <= TOL["SR"])
    dji = ref["DJI"]["W240"]
    ew = ref["EW_cost0"]["W240"]
    beat = int(((cr > dji["CR"]) & (sr > dji["SR"])).sum())
    need = math.ceil(0.7 * n - 1e-9)
    res.update(beat_dji=beat, need=need, R2=None if n < 5 else beat >= need,
               beat_ew_cost0=int(((cr > ew["CR"]) & (sr > ew["SR"])).sum()))
    if res["R1"] is None or res["R2"] is None:
        res["grade"] = "판정 불가"
    else:
        res["grade"] = {2: "재현", 1: "부분 재현", 0: "미재현"}[int(res["R1"]) + int(res["R2"])]
    if 42 in rows:
        res["seed42_W240"] = rows[42]["W240"]
    return res


def judge():
    import pandas as pd
    ref = reference()
    r = {"reference": ref, "L": judge_cond("L", ref), "N": judge_cond("N", ref), "paper": PAPER, "paper_dji": PAPER_DJI}
    c = out() / "C"
    if (c / "done.json").exists():
        a, b = [pd.read_csv(c / f"run{i}_detailed.csv") for i in (1, 2)]
        m = metrics(slice_w240(a))
        r["C"] = {"W240": m, "W251": metrics(a.portfolio_value.values), "deterministic": bool((a.portfolio_value == b.portfolio_value).all()),
                  "R1": bool(abs(m["CR"] - PAPER["CR"]) <= TOL["CR"] and abs(m["SR"] - PAPER["SR"]) <= TOL["SR"])}
    (out() / "judge_o1.json").write_text(json.dumps(r, indent=1, default=float))
    print(json.dumps({k: {x: r[k].get(x) for x in ("n_seeds", "median", "R1", "R2", "beat_dji", "need", "beat_ew_cost0", "within_tol", "grade")} for k in ("L", "N")}, indent=1, ensure_ascii=False))
    if "C" in r:
        print("C", {k: r["C"][k] for k in ("R1", "deterministic")}, {k: round(r["C"]["W240"][k], 3) for k in ("CR", "SR", "MDD")})


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "setup":
        setup()
    elif a[0] == "pilot":
        pilot(a[1], a[2])
    elif a[0] == "run":
        run(a[1], int(a[2]), a[3])
    elif a[0] == "ckpt":
        ckpt()
    elif a[0] == "judge":
        judge()
    elif a[0] == "smoke":
        smoke(a[1], a[2])
    elif a[0] == "queue":
        queue()
    elif a[0] == "status":
        status()
    else:
        sys.exit(__doc__)
