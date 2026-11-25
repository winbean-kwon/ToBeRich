"""Pre-registered judge for exploratory F7x P24-07 (notes/funnel_f7x_p2407_prereg.md).

Metric functions follow the author's draw/draw.py (total_return, annualized_return, sharpe_ratio with
rf=0.02, max_drawdown; same logic). draw.py also restricts every strategy to the dates it shares with
draw/dji.csv (common_dates); the judge applies the same intersection (date column of dji.csv only) and
returns '판정 불가' if it is not the full 671 trading days. KDD aggregation = date-wise mean of run curves.

Usage:
  python funnel_f7x_p2407_judge.py OUT_DIR AUTHOR_ACCOUNT_CSV TRADE_CSV DJI_CSV RESULT_JSON
  python funnel_f7x_p2407_judge.py --selftest
"""
import json
import sys

import numpy as np
import pandas as pd

REP = {"TR": 138.38, "AR": 38.74, "Sharpe": 2.03, "MD": -11.46}
DDPG = {"AR": 15.06, "Sharpe": 0.98}
HALF_SR = 0.5 * (REP["Sharpe"] - DDPG["Sharpe"])   # 0.525
HALF_AR = 0.5 * (REP["AR"] - DDPG["AR"])           # 11.84
SEEDS = [0, 1, 2, 3, 4]
R0_TOL = 1e-4
R0_BIT = 1e-9
COST = 0.001
INIT = 10000.0


# ---- author's draw.py metric functions (verbatim logic) ----
def total_return(df):
    return (df['Portfolio_Value'].iloc[-1] / df['Portfolio_Value'].iloc[0] - 1) * 100


def annualized_return(df):
    total_years = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days / 365.25
    return ((df['Portfolio_Value'].iloc[-1] / df['Portfolio_Value'].iloc[0]) ** (1 / total_years) - 1) * 100


def sharpe_ratio(df, risk_free_rate=0.02):
    daily_return = df['Portfolio_Value'].pct_change()
    return (daily_return.mean() - risk_free_rate / 252) / daily_return.std() * np.sqrt(252)


def max_drawdown(df):
    roll_max = df['Portfolio_Value'].cummax()
    drawdown = df['Portfolio_Value'] / roll_max - 1.0
    return drawdown.min() * 100


def metrics(dates, values):
    df = pd.DataFrame({"Date": pd.to_datetime(pd.Series(dates)).values, "Portfolio_Value": np.asarray(values, float)})
    return {"TR": total_return(df), "AR": annualized_return(df), "Sharpe": sharpe_ratio(df), "MD": max_drawdown(df)}


def read_acct(path):
    d = pd.read_csv(path, index_col=0)
    d["date"] = pd.to_datetime(d["date"])
    return d[["date", "account_value"]].reset_index(drop=True)


def ew_daily(trade_csv, cost=COST):
    """5-stock equal weight, daily rebalanced to 1/N at close, proportional cost on traded value."""
    t = pd.read_csv(trade_csv, index_col=0, parse_dates=["date"])
    px = t.pivot(index="date", columns="tic", values="close").sort_index()
    r = px.pct_change().fillna(0.0).values
    n = px.shape[1]
    v = [INIT * (1 - cost)]   # FinRL env starts in cash and pays cost when buying on day 1
    w = np.full(n, 1.0 / n)
    for i in range(1, len(px)):
        grown = w * (1 + r[i])
        val = v[-1] * grown.sum()
        drift = grown / grown.sum()
        turnover = np.abs(drift - 1.0 / n).sum()
        val -= val * turnover * cost
        v.append(val)
        w = np.full(n, 1.0 / n)
    return px.index, np.array(v)


def bh(trade_csv, cost=COST):
    """5-stock buy-and-hold, equal initial weights, cost paid once on day 1."""
    t = pd.read_csv(trade_csv, index_col=0, parse_dates=["date"])
    px = t.pivot(index="date", columns="tic", values="close").sort_index()
    v = (INIT * (1 - cost) / px.shape[1] * (px / px.iloc[0])).sum(axis=1)
    return px.index, v.values


def judge(out_dir, author_csv, trade_csv, dji_csv):
    dji_dates = set(pd.to_datetime(pd.read_csv(dji_csv, usecols=["date"])["date"]))
    res = {"reported": REP, "band_sharpe": [REP["Sharpe"] - HALF_SR, REP["Sharpe"] + HALF_SR],
           "band_ar": [REP["AR"] - HALF_AR, REP["AR"] + HALF_AR]}
    # R0
    ours = read_acct(f"{out_dir}/author_seed0/data/originate_ddpg.csv")
    auth = read_acct(author_csv)
    m = ours.merge(auth, on="date", how="outer", suffixes=("_ours", "_auth"), indicator=True)
    same_dates = bool((m["_merge"] == "both").all()) and len(ours) == len(auth)
    rel = (m["account_value_ours"] - m["account_value_auth"]).abs() / m["account_value_auth"].abs()
    maxrel = float(rel.max()) if same_dates else None
    first_bad, frac_bad = None, None
    if same_dates:
        frac_bad = float((rel > R0_TOL).mean())
        if maxrel > R0_TOL:
            first_bad = str(m.loc[rel > R0_TOL, "date"].iloc[0].date())
    if same_dates and maxrel <= R0_BIT:
        res["R0"] = "비트 일치"
    elif same_dates and maxrel <= R0_TOL:
        res["R0"] = "일치"
    else:
        res["R0"] = "불일치"
    res["R0_detail"] = {"n_ours": len(ours), "n_author": len(auth), "same_dates": same_dates,
                        "max_rel_diff": maxrel, "frac_days_over_1e-4": frac_bad, "first_date_over_tol": first_bad}
    res["Q1_checkpoint_metrics"] = metrics(ours["date"], ours["account_value"])

    # Q2
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
    common = [d for d in ours["date"] if d in dji_dates]
    res["common_dates_with_dji"] = len(common)
    if len(common) != 671:
        res["R1"] = res["R1_aux_AR"] = res["R2"] = "판정 불가(dji 날짜 교집합이 671일이 아님)"
        return res
    res["per_seed"] = per_seed
    dates_ew, v_ew = ew_daily(trade_csv)
    ew = metrics(dates_ew, v_ew)
    ew0 = metrics(*ew_daily(trade_csv, cost=0.0))
    res["EW5_cost10bp"], res["EW5_cost0"] = ew, ew0
    res["BH5_cost10bp"] = metrics(*bh(trade_csv))
    if len(curves) < 4:
        res["R1"] = res["R1_aux_AR"] = res["R2"] = "판정 불가(완료 시드 4개 미만)"
        return res
    base = curves[sorted(curves)[0]][["date"]]
    mat = pd.concat([base.merge(c, on="date", how="left")["account_value"].rename(s) for s, c in curves.items()], axis=1)
    if mat.isna().any().any():
        res["R1"] = res["R1_aux_AR"] = res["R2"] = "판정 불가(시드 간 날짜 불일치)"
        return res
    mean_curve = mat.mean(axis=1)
    mm = metrics(base["date"], mean_curve)
    res["mean_curve_metrics"] = mm
    res["median_seed_metrics"] = {k: float(np.median([v[k] for v in per_seed.values()])) for k in REP}
    lo, hi = res["band_sharpe"]
    res["R1"] = "통과" if lo <= mm["Sharpe"] <= hi else "미통과"
    lo, hi = res["band_ar"]
    res["R1_aux_AR"] = "통과" if lo <= mm["AR"] <= hi else "미통과"
    # R2 per seed (mean-of-curves Sharpe is inflated by averaging across runs; descriptive only)
    k = sum(v['Sharpe'] > ew['Sharpe'] for v in per_seed.values())
    res["R2_seeds_above_EW"] = f"{k}/{len(per_seed)}"
    res["R2"] = "통과" if (res["median_seed_metrics"]["Sharpe"] > ew["Sharpe"] and k >= 4) else "미통과"
    res["R2_mean_curve_vs_EW_descriptive"] = mm["Sharpe"] > ew["Sharpe"]
    return res


def selftest():
    import os
    import tempfile
    d = tempfile.mkdtemp()
    dates = pd.bdate_range("2016-01-04", periods=671)
    tics = ["AAPL", "BA", "CRM", "UNH", "V"]
    rng = np.random.default_rng(0)
    rows = []
    for i, dt in enumerate(dates):
        for j, t in enumerate(tics):
            rows.append({"date": dt, "tic": t, "close": 100 * np.exp(0.0012 * i + 0.01 * rng.standard_normal())})
    trade = pd.DataFrame(rows)
    trade.index = np.repeat(np.arange(len(dates)), len(tics))
    trade.to_csv(f"{d}/trade.csv")

    def write(path, vals):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "account_value": vals}).to_csv(path)
    base = 10000 * np.exp(np.cumsum(0.0013 + 0.009 * rng.standard_normal(len(dates))))
    write(f"{d}/author.csv", base)
    pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "close": 1.0}).to_csv(f"{d}/dji.csv", index=False)
    write(f"{d}/out/author_seed0/data/originate_ddpg.csv", base * (1 + 1e-7))
    for s in SEEDS:
        write(f"{d}/out/train_seed{s}/data/originate_ddpg.csv",
              10000 * np.exp(np.cumsum(0.0013 + 0.009 * rng.standard_normal(len(dates)))))
    r = judge(f"{d}/out", f"{d}/author.csv", f"{d}/trade.csv", f"{d}/dji.csv")
    print("selftest:", r["R0"], r["R1"], r["R1_aux_AR"], r["R2"], r["R2_seeds_above_EW"],
          {k: round(v, 3) for k, v in r["mean_curve_metrics"].items()}, "EW", round(r["EW5_cost10bp"]["Sharpe"], 3))
    assert r["R0"] == "일치"
    # EW numeric checks: constant prices, cost 0 -> constant value; cost 0.1% -> only day-1 cost
    flat = trade.copy(); flat["close"] = 50.0; flat.to_csv(f"{d}/flat.csv")
    _, v0 = ew_daily(f"{d}/flat.csv", cost=0.0); assert np.allclose(v0, INIT)
    _, v1 = ew_daily(f"{d}/flat.csv"); assert np.allclose(v1, INIT * (1 - COST))
    write(f"{d}/out/author_seed0/data/originate_ddpg.csv", base)
    assert judge(f"{d}/out", f"{d}/author.csv", f"{d}/trade.csv", f"{d}/dji.csv")["R0"] == "비트 일치"
    write(f"{d}/out/author_seed0/data/originate_ddpg.csv", base * 1.01)
    assert judge(f"{d}/out", f"{d}/author.csv", f"{d}/trade.csv", f"{d}/dji.csv")["R0"] == "불일치"
    os.remove(f"{d}/out/train_seed4/data/originate_ddpg.csv")
    os.remove(f"{d}/out/train_seed3/data/originate_ddpg.csv")
    assert judge(f"{d}/out", f"{d}/author.csv", f"{d}/trade.csv", f"{d}/dji.csv")["R1"].startswith("판정 불가")
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1] == "--selftest":
        selftest()
        sys.exit(0)
    out_dir, author_csv, trade_csv, dji_csv, out_json = sys.argv[1:6]
    r = judge(out_dir, author_csv, trade_csv, dji_csv)
    json.dump(r, open(out_json, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: r.get(k) for k in ("R0", "R1", "R1_aux_AR", "R2", "R2_seeds_above_EW", "seeds_done")},
                     ensure_ascii=False))
