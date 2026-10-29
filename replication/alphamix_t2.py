"""T2 AlphaMix+ (PRUDEX-Compass @2b62831 `AlphaMix+/PM`) — O1 실행기·O5 동적 점검·O1 판정 계산.

사전 등록: notes/prereg_reeval_v3.md 2·3장(T2), notes/alphamix_t2_o1_prereg.md(이 파일의 구현 고정). 결과를 보기 전에 커밋한다.

Colab(노트북 replication/alphamix_t2_o1.ipynb가 호출, cwd = PRUDEX/AlphaMix+/PM, PYTHONPATH에 shim):
  python alphamix_t2.py snap              데이터 1회 다운로드 → 스냅샷 저장(sha256), 3단계 분할 기록
  python alphamix_t2.py train <단계> <시드> 원 코드 experiment() 1회, 결과 파일 복사
  python alphamix_t2.py o5                O5 동적 점검(C1·C2·S1, CPU)
맥:
  python3 alphamix_t2.py judge1 <결과 폴더>   O1 판정 계산(R1·R2·등급) → judge_o1.json

데이터 고정: `YahooFinanceProcessor.download_data`를 감싸, 스냅샷이 있으면 그 파일만 읽고(해시 확인), 없으면 원 함수로
한 번 받아 저장한 뒤 다시 읽어 원본과 정확히 같은지 확인한다. 세 단계(dj30, dj30_rolling1, dj30_rolling2)는 같은 인자로
받으므로(2012-01-01~2022-01-01, 같은 30종목) 스냅샷 하나를 같이 쓴다. 인자가 다르면 멈춘다.
"""
import hashlib, json, os, pathlib, sys, time

STAGES = {"S2021": "dj30", "S2020": "dj30_rolling1", "S2019": "dj30_rolling2"}
SEEDS = [12345, 23451, 34512, 45123, 51234]
# 논문 Table 5–7 US AlphaMix+ TR(%) 시드 5개 평균 ± 표준편차, v3 3장 R1 허용 폭(±2σ/√5)
PAPER_TR = {"S2021": 20.7, "S2020": 12.7, "S2019": 25.1}
TOL_TR = {"S2021": 1.61, "S2020": 1.52, "S2019": 1.27}
PAPER_SR_2021 = 1.64


def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def out_root():
    return pathlib.Path(os.environ["T2_OUT"])


# ---------------------------------------------------------------- 데이터 고정
def patch_download():
    import pandas as pd
    from finrl.finrl_meta.data_processors.processor_yahoofinance import YahooFinanceProcessor as YFP
    orig = YFP.download_data
    snap = out_root() / "snapshot"
    f, m = snap / "dj30_raw.csv.gz", snap / "meta.json"

    def load(meta):
        df = pd.read_csv(f, dtype={"date": str, "tic": str}, float_precision="round_trip")
        return df.astype(meta["dtypes"])[meta["columns"]]

    def download_data(self, start_date, end_date, ticker_list, time_interval):
        key = dict(start=start_date, end=end_date, tickers=list(ticker_list), interval=time_interval)
        if m.exists():
            meta = json.loads(m.read_text())
            assert meta["key"] == key, ("다운로드 인자가 스냅샷과 다름", key)
            assert sha256(f) == meta["sha256"], "스냅샷 해시 불일치"
            print("[snapshot] 고정 데이터 사용", meta["sha256"][:12], meta["shape"])
            return load(meta)
        snap.mkdir(parents=True, exist_ok=True)
        df = orig(self, start_date, end_date, ticker_list, time_interval)
        df.to_csv(f, index=False)
        import yfinance
        meta = dict(key=key, sha256=sha256(f), shape=list(df.shape), columns=list(df.columns),
                    dtypes={c: str(t) for c, t in df.dtypes.items()}, tickers_got=sorted(df.tic.unique()),
                    created=time.strftime("%Y-%m-%d %H:%M:%S %Z"), yfinance=yfinance.__version__, pandas=pd.__version__)
        back = load(meta)
        pd.testing.assert_frame_equal(back, df, check_exact=True)
        m.write_text(json.dumps(meta, indent=1))
        print("[snapshot] 새로 저장", meta["sha256"][:12], meta["shape"])
        return df

    YFP.download_data = download_data


def cmd_snap():
    patch_download()
    from rl_env.portfolio_management import get_dataset_config
    info = {}
    for st, ds in STAGES.items():
        tr, va, te = get_dataset_config(ds)
        info[st] = {k: [str(c["df"].date.min()), str(c["df"].date.max()), int(c["df"].date.nunique()),
                        int(c["stock_dim"]), float(c["transaction_cost_pct"])]
                    for k, c in zip(["train", "valid", "test"], [tr, va, te])}
        info[st]["tics"] = list(te["df"].tic.unique())
        # R2 등가중 계산용: 원 env가 수익에 쓰는 close(테스트 구간, 날짜 × 종목)
        te["df"].pivot(index="date", columns="tic", values="close").to_csv(out_root() / "snapshot" / f"test_close_{st}.csv")
    (out_root() / "snapshot" / "splits.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))


# ---------------------------------------------------------------- 학습(원 코드 그대로)
def cmd_train(stage, seed):
    import importlib.util, shutil, torch
    assert stage in STAGES and seed in SEEDS
    out = out_root() / "o1" / f"{stage}_s{seed}"
    if (out / "meta.json").exists():
        print("이미 완료", out); return
    patch_download()
    spec = importlib.util.spec_from_file_location("am", "AlphaMix+_sz50.py")
    am = importlib.util.module_from_spec(spec); spec.loader.exec_module(am)   # __main__ 블록은 실행되지 않음
    import rlkit.torch.pytorch_util as ptu
    from rlkit.launchers.launcher_util import setup_logger_custom
    # 파일럿과 같은 variant: 스크립트 __main__ 값 + 주석으로 남은 dj_30 루프 값 3개
    variant = dict(algorithm="SAC", version="normal", layer_size=128, buffer_size=int(1E4),
        algorithm_kwargs=dict(num_epochs=10, num_eval_steps_per_epoch=1500,
            num_trains_per_train_loop=2000, num_expl_steps_per_train_loop=2000, min_num_steps_before_training=70000,
            max_path_length=5000, batch_size=256, save_frequency=0),
        trainer_kwargs=dict(discount=0.99, soft_target_tau=5e-3, target_update_period=1, policy_lr=7E-4, qf_lr=7E-4,
            reward_scale=1, use_automatic_entropy_tuning=True),
        num_ensemble=3, num_layer=2, dataset=STAGES[stage], seed=seed, ber_mean=0.5, env="portfolio_management",
        inference_type=0.0, temperature=20.0, log_dir="", uncertainty=0.5)
    gpu = torch.cuda.is_available(); ptu.set_gpu_mode(gpu)
    log_dir = setup_logger_custom("AlphaMix+", variant=variant); variant["log_dir"] = log_dir
    ptu.set_gpu_mode(gpu)
    t0 = time.time(); am.experiment(variant); el = time.time() - t0
    tmp = out.with_name(out.name + ".tmp"); shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
    ld = pathlib.Path(log_dir)
    for p in [ld / "result.csv", *ld.glob("test_daily_return_*.csv"), *ld.glob("test_daily_action_*.npy")]:
        shutil.copy(p, tmp / p.name)
    snapmeta = json.loads((out_root() / "snapshot" / "meta.json").read_text())
    (tmp / "meta.json").write_text(json.dumps(dict(stage=stage, dataset=STAGES[stage], seed=seed, seconds=round(el, 1),
        gpu=gpu, device=torch.cuda.get_device_name(0) if gpu else "cpu", torch=torch.__version__,
        snapshot_sha256=snapmeta["sha256"], finished=time.strftime("%Y-%m-%d %H:%M:%S %Z")), indent=1))
    shutil.rmtree(out, ignore_errors=True); tmp.rename(out)
    print("__DONE__", stage, seed, round(el / 60, 1), "분")


# ---------------------------------------------------------------- O5 동적 점검(v2 3장 C1·C2·C3·S1)
def u1_ref(W, R, c):
    """참조 비용(v2 2장): 직전 배분이 드리프트한 가중치 w'와 새 목표 w의 종목 성분 L1 차이 × c(현금은 잔여분이라 세지 않음,
    T3 u1_returns와 같은 정의). W[t]가 R[t]를 받는다. W 행은 [현금, 종목...] 합 1, R 행은 종목 단순수익. 반환: 스텝별 비용률."""
    import numpy as np
    prev = np.r_[1.0, np.zeros(W.shape[1] - 1)]   # 참조 명세의 현금 시작
    cost = []
    for w, r in zip(W, R):
        cost.append(c * np.abs(w[1:] - prev[1:]).sum())
        g = w * np.r_[1.0, 1 + r]
        prev = g / g.sum()
    return np.array(cost)


def cmd_o5():
    import numpy as np
    patch_download()
    from rl_env.portfolio_management import TrainEnv, get_dataset_config
    _, _, te = get_dataset_config("dj30")
    n = te["stock_dim"]; T = 40                          # 테스트 창 앞 40스텝
    close = te["df"].pivot(index="date", columns="tic", values="close").values
    R = close[1:T + 1] / close[:T] - 1
    eq = np.r_[0.0, np.full(n, 1 / n)]
    A = np.r_[0.0, np.where(np.arange(n) < n // 2, 2 / n, 0.0)]; B = np.r_[0.0, np.where(np.arange(n) >= n // 2, 2 / n, 0.0)]
    seqs = {"1_eq_hold": [eq] * T, "2_AB_alt": [A if t % 2 == 0 else B for t in range(T)],
            "3_cash_first3": [eq] * 3}
    res = {}
    for name, W in seqs.items():
        W = np.array(W); runs = {}
        for c in (0.0, 0.001):
            cfg = dict(te, transaction_cost_pct=c); env = TrainEnv(config=cfg); env._seed(0); env.reset()
            rew, w_env = [], []
            with np.errstate(divide="ignore"):
                for w in W:
                    _, r, d, _ = env.step(np.log(w)[None])   # softmax(log w) = w, 현금 0 → exp(-inf) = 0
                    rew.append(r); w_env.append(env.actions_memory[-1][0])
            ret = np.array(env.portfolio_return_memory[1:]); val = np.array(env.asset_memory)
            runs[c] = dict(rew=np.array(rew), ret=ret, val=val, w=np.array(w_env))
        a, b = runs[0.0], runs[0.001]
        k = len(W); ref = u1_ref(W, R[:k], 0.001)
        gross = (W[:, 1:] * R[:k]).sum(1)
        meas = gross - b["ret"]                              # 원 env가 실제로 뺀 비용(수익률 단위)
        res[name] = dict(
            steps=k, inject_err=float(np.abs(b["w"] - W).max()),
            C1_reward_differs=bool(np.abs(a["rew"] - b["rew"]).max() > 0), C1_return_differs=bool(np.abs(a["ret"] - b["ret"]).max() > 0),
            C2_rel_err=float(abs(b["rew"].sum() / cfg["reward_scaling"] - (b["val"][-1] - b["val"][0])) / b["val"][0]),
            S1_measured_over_ref=float(meas.sum() / ref.sum()), S1_ref_bp_first3=[round(x * 1e4, 4) for x in ref[:3]],
            S1_measured_bp_first3=[round(x * 1e4, 4) for x in meas[:3]],
            return_matches_w_dot_r=float(np.abs(b["ret"] - gross).max()))
    res["C3"] = dict(reset_asset=float(env.asset_memory[0]), actions_memory0="1/stock_dim 목록(계산에 안 쓰임)",
                     obs_shape=list(np.array(env.reset()).shape), obs_has_holdings=False,
                     note="관측은 11개 지표 × 종목(직전 보유 없음), 학습·검증·테스트 env 모두 같은 TrainEnv.reset")
    (out_root() / "o5").mkdir(parents=True, exist_ok=True)
    (out_root() / "o5" / "o5_result.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps(res, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- O1 판정(맥)
def cmd_judge1(root):
    import numpy as np, pandas as pd
    root = pathlib.Path(root); snapmeta = json.loads((root / "snapshot" / "meta.json").read_text())
    out = dict(snapshot_sha256=snapmeta["sha256"], stages={})
    n_r1 = n_r2 = 0
    for st in STAGES:
        close = pd.read_csv(root / "snapshot" / f"test_close_{st}.csv", index_col=0).values
        ew = np.r_[0.0, (close[1:] / close[:-1] - 1).mean(1)]           # market average: 매일 등가중, 무비용
        ew_tr = 100 * (np.prod(1 + ew) - 1)
        seeds = {}
        for s in SEEDS:
            d = root / "o1" / f"{st}_s{s}"
            meta = json.loads((d / "meta.json").read_text()); assert meta["snapshot_sha256"] == snapmeta["sha256"]
            r = pd.read_csv(d / "result.csv", index_col=0); assert len(r) == 10
            last = len(r) - 1
            dr = pd.read_csv(d / f"test_daily_return_{last}.csv", index_col=0)["daily_return"].values
            assert len(dr) == len(close), (st, s, len(dr), len(close))
            assert abs((np.prod(1 + dr) - 1) - r.test_tr.iloc[last]) < 1e-9
            vb = int(r.eval_tr.values.argmax())
            seeds[s] = dict(tr=float(100 * r.test_tr.iloc[last]), sr=float(r.test_sr.iloc[last]),
                            vbest_epoch=vb, vbest_tr=float(100 * r.test_tr.iloc[vb]), minutes=round(meta["seconds"] / 60, 1))
        tr_mean = float(np.mean([v["tr"] for v in seeds.values()]))
        r1 = abs(tr_mean - PAPER_TR[st]) <= TOL_TR[st]; r2 = tr_mean > ew_tr
        n_r1 += r1; n_r2 += r2
        out["stages"][st] = dict(paper_tr=PAPER_TR[st], tol=TOL_TR[st], tr_mean=tr_mean,
                                 tr_sd=float(np.std([v["tr"] for v in seeds.values()], ddof=1)), R1=bool(r1),
                                 ew_tr=float(ew_tr), R2=bool(r2), n_beat_ew=int(sum(v["tr"] > ew_tr for v in seeds.values())),
                                 sr_mean=float(np.mean([v["sr"] for v in seeds.values()])),
                                 vbest_tr_mean=float(np.mean([v["vbest_tr"] for v in seeds.values()])), seeds=seeds)
    R1, R2 = n_r1 >= 2, n_r2 >= 2
    out.update(R1_stages=int(n_r1), R2_stages=int(n_r2), R1=bool(R1), R2=bool(R2),
               grade="재현" if R1 and R2 else "부분 재현" if R1 or R2 else "미재현", paper_sr_2021=PAPER_SR_2021)
    (root / "judge_o1.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k != "stages"}, ensure_ascii=False))
    for st, v in out["stages"].items():
        print(st, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in v.items() if k != "seeds"})


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "snap": cmd_snap()
    elif c == "train": cmd_train(sys.argv[2], int(sys.argv[3]))
    elif c == "o5": cmd_o5()
    elif c == "judge1": cmd_judge1(sys.argv[2])
    else: raise SystemExit(__doc__)
