"""Judge for the exploratory 30-stock (full raw_data.csv universe) P24-07 run (notes/p2407_30stock_prereg.md).

Same definitions as replication/funnel_f7x_p2407_judge.py (metric functions from the author's draw/draw.py,
rf = 0.02; dji.csv date intersection must be 671 days; aggregation = date-wise mean of seed curves), applied to the
full universe:
  R1'  mean-curve Sharpe in [1.505, 2.555]  (aux: mean-curve AR in [26.90, 50.58]);
  R2'  median per-seed Sharpe > EW_N Sharpe AND >= 4/5 seeds above EW_N, where EW_N = all tickers of the trade
       data, equal weight, daily rebalanced, 0.1% cost (same ew_daily as the base judge's EW5).
No R0 (there is no author checkpoint for this setting).

Usage:
  python p2407_30stock_judge.py OUT_DIR TRADE_CSV DJI_CSV RESULT_JSON
  python p2407_30stock_judge.py --baselines TRADE_CSV        (pre-run disclosure: EW_N / BH_N only)
  python p2407_30stock_judge.py --selftest
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from funnel_f7x_p2407_judge import (REP, HALF_SR, HALF_AR, SEEDS, COST, INIT,  # noqa: E402
                                    metrics, read_acct, ew_daily, bh)


def baselines(trade_csv):
    t = pd.read_csv(trade_csv, index_col=0, parse_dates=["date"])
    px = t.pivot(index="date", columns="tic", values="close").sort_index()
    return {"n_tickers": int(px.shape[1]), "tickers": list(px.columns), "n_days": int(px.shape[0]),
            "price_nan": int(px.isna().sum().sum()),
            "EWN_cost10bp": metrics(*ew_daily(trade_csv)), "EWN_cost0": metrics(*ew_daily(trade_csv, cost=0.0)),
            "BHN_cost10bp": metrics(*bh(trade_csv)), "BHN_cost0": metrics(*bh(trade_csv, cost=0.0))}


def judge(out_dir, trade_csv, dji_csv):
    dji_dates = set(pd.to_datetime(pd.read_csv(dji_csv, usecols=["date"])["date"]))
    res = {"reported": REP, "band_sharpe": [REP["Sharpe"] - HALF_SR, REP["Sharpe"] + HALF_SR],
           "band_ar": [REP["AR"] - HALF_AR, REP["AR"] + HALF_AR]}
    curves, per_seed = {}, {}
    for s in SEEDS:
        p = f"{out_dir}/train_seed{s}/data/originate_ddpg.csv"
        try:
            c = read_acct(p)
        except FileNotFoundError:
            continue
        curves[s] = c
        per_seed[s] = metrics(c["date"], c["account_value"])
    res["seeds_done"] = sorted(curves)
    b = baselines(trade_csv)
    res.update(b)
    if len(curves) < 4:
        res["R1p"] = res["R1p_aux_AR"] = res["R2p"] = "판정 불가(완료 시드 4개 미만)"
        return res
    base = curves[sorted(curves)[0]][["date"]]
    common = [d for d in base["date"] if d in dji_dates]
    res["common_dates_with_dji"] = len(common)
    if len(common) != 671:
        res["R1p"] = res["R1p_aux_AR"] = res["R2p"] = "판정 불가(dji 날짜 교집합이 671일이 아님)"
        return res
    res["per_seed"] = per_seed
    mat = pd.concat([base.merge(c, on="date", how="left")["account_value"].rename(s) for s, c in curves.items()], axis=1)
    if mat.isna().any().any():
        res["R1p"] = res["R1p_aux_AR"] = res["R2p"] = "판정 불가(시드 간 날짜 불일치)"
        return res
    mm = metrics(base["date"], mat.mean(axis=1))
    res["mean_curve_metrics"] = mm
    res["median_seed_metrics"] = {k: float(np.median([v[k] for v in per_seed.values()])) for k in REP}
    lo, hi = res["band_sharpe"]
    res["R1p"] = "통과" if lo <= mm["Sharpe"] <= hi else ("폭 아래" if mm["Sharpe"] < lo else "폭 위")
    lo, hi = res["band_ar"]
    res["R1p_aux_AR"] = "통과" if lo <= mm["AR"] <= hi else "미통과"
    ew = b["EWN_cost10bp"]
    k = sum(v["Sharpe"] > ew["Sharpe"] for v in per_seed.values())
    res["R2p_seeds_above_EW"] = f"{k}/{len(per_seed)}"
    res["R2p"] = "통과" if (res["median_seed_metrics"]["Sharpe"] > ew["Sharpe"] and k >= 4) else "미통과"
    res["R2p_mean_curve_vs_EW_descriptive"] = bool(mm["Sharpe"] > ew["Sharpe"])
    # distinct curves (descriptive; the 5-stock runs collapsed onto a few first-day allocations)
    vals = [tuple(np.round(c["account_value"].values, 6)) for c in curves.values()]
    res["distinct_seed_curves"] = len(set(vals))
    return res


def selftest():
    import tempfile
    d = tempfile.mkdtemp()
    dates = pd.bdate_range("2016-01-04", periods=671)
    tics = [f"T{i:02d}" for i in range(29)]
    rng = np.random.default_rng(0)
    rows = [{"date": dt, "tic": t, "close": 100 * np.exp(0.0008 * i + 0.01 * rng.standard_normal())}
            for i, dt in enumerate(dates) for t in tics]
    trade = pd.DataFrame(rows)
    trade.index = np.repeat(np.arange(len(dates)), len(tics))
    trade.to_csv(f"{d}/trade.csv")
    pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": 1.0}).to_csv(f"{d}/dji.csv", index=False)

    def write(path, vals):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "account_value": vals}).to_csv(path)
    for s in SEEDS:
        write(f"{d}/out/train_seed{s}/data/originate_ddpg.csv",
              10000 * np.exp(np.cumsum(0.0013 + 0.009 * rng.standard_normal(len(dates)))))
    r = judge(f"{d}/out", f"{d}/trade.csv", f"{d}/dji.csv")
    assert r["n_tickers"] == 29 and r["n_days"] == 671
    print("selftest:", r["R1p"], r["R2p"], r["R2p_seeds_above_EW"], round(r["mean_curve_metrics"]["Sharpe"], 3),
          "EW", round(r["EWN_cost10bp"]["Sharpe"], 3))
    flat = trade.copy(); flat["close"] = 50.0; flat.to_csv(f"{d}/flat.csv")
    _, v0 = ew_daily(f"{d}/flat.csv", cost=0.0); assert np.allclose(v0, INIT)
    _, v1 = ew_daily(f"{d}/flat.csv"); assert np.allclose(v1, INIT * (1 - COST))
    os.remove(f"{d}/out/train_seed4/data/originate_ddpg.csv")
    os.remove(f"{d}/out/train_seed3/data/originate_ddpg.csv")
    assert judge(f"{d}/out", f"{d}/trade.csv", f"{d}/dji.csv")["R1p"].startswith("판정 불가")
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1] == "--selftest":
        selftest()
    elif sys.argv[1] == "--baselines":
        print(json.dumps(baselines(sys.argv[2]), ensure_ascii=False, indent=1, default=float))
    else:
        out_dir, trade_csv, dji_csv, out_json = sys.argv[1:5]
        r = judge(out_dir, trade_csv, dji_csv)
        json.dump(r, open(out_json, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps({k: r.get(k) for k in ("n_tickers", "R1p", "R1p_aux_AR", "R2p", "R2p_seeds_above_EW",
                                                "seeds_done")}, ensure_ascii=False))
