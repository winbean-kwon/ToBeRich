"""Exploratory F7 FRONTIER judge. Pre-registered in notes/funnel_f7x_frontier_prereg.md.

Reads only the per-seed backtest CSVs (author format: gamma_trade, gamma_risk, seed,
excess_return, excess_risk, sharpe). Pareto set and mean frontier use the author's own
functions (frontier_tools.py, copied verbatim below; added to the repo after publication).

Usage: python funnel_f7x_frontier_judge.py <backtests_dir> <out_json>
       python funnel_f7x_frontier_judge.py --selftest
"""
import glob
import json
import sys

import numpy as np
import pandas as pd
import scipy.stats

# ---- fixed reported values (Claude figure reading of Fig. 7(a), see prereg 1) ----
R_EW = 14.78        # EW excess risk (%)
EW_RET = 9.77       # EW excess return (%)
F_REP = 11.79       # FRONTIER (log-return) mean frontier at R_EW (%)
HALF = 0.5 * (F_REP - EW_RET)   # 1.01
SEEDS = [0, 1111, 2222, 3333, 4444]
GRID = [2, 4, 6, 8, 10, 12, 14]
MIN_IN_BIN = 15   # author used 30 for 10 seeds; scaled to 5 seeds (same points per seed per bin), prereg 3


# ---- author code (ruankie/frontier-rl main: src/utilities/frontier_tools.py), verbatim logic ----
def get_pareto_points(input_df):
    df = input_df.copy()
    df['is_pareto'] = False
    updated_df = df.copy()
    for idx, row in df.iterrows():
        dominated_by = df[(df['excess_return'] > row['excess_return']) &
                          (df['excess_risk'] < row['excess_risk'])]
        if dominated_by.shape[0] == 0:
            updated_df.loc[idx, 'is_pareto'] = True
    return updated_df[updated_df['is_pareto'] == True].sort_values(by='excess_risk', ascending=True)  # noqa: E712


def get_critical_t(n, alpha=0.05):
    return scipy.stats.t.ppf(q=1 - alpha / 2, df=n - 1)


def get_mean_margin_of_err(data_list, conf_lvl=0.95):
    data = np.array(data_list)
    n = len(data)
    mean = data.mean()
    stdev = data.std(ddof=1)
    t_star = get_critical_t(n, 1.0 - conf_lvl)
    return mean, t_star * (stdev / np.sqrt(n))


def get_bin_means_min_in_bin(x_data, y_data, min_in_bin=30):
    nb_bins = int(np.ceil(len(x_data) / min_in_bin))
    x_mids, y_means, moes = [], [], []
    for i in range(nb_bins):
        by = y_data[i * min_in_bin:(i + 1) * min_in_bin]
        bx = x_data[i * min_in_bin:(i + 1) * min_in_bin]
        m, e = get_mean_margin_of_err(by)
        x_mids.append((bx[0] + bx[-1]) / 2.0)
        y_means.append(m)
        moes.append(e)
    return np.array(x_mids), np.array(y_means), np.array(moes)


def mean_frontier(frontiers_df, xmax=25.0, min_in_bin=MIN_IN_BIN):
    data = frontiers_df.sort_values(by=['excess_risk']).reset_index(drop=True)
    data = data[data['excess_risk'] <= xmax]
    return get_bin_means_min_in_bin(data['excess_risk'].values, data['excess_return'].values, min_in_bin)


def interp(xs, ys, x):
    """linear interpolation inside [min(xs), max(xs)], else None (no extrapolation)."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    if len(xs) == 0 or x < xs.min() or x > xs.max():
        return None
    o = np.argsort(xs)
    return float(np.interp(x, xs[o], ys[o]))


def judge(df_in):
    n_nan = int(df_in[['excess_return', 'excess_risk']].isna().any(axis=1).sum())
    df = df_in.dropna(subset=['excess_return', 'excess_risk'])
    seeds_present = sorted(int(s) for s in df['seed'].unique())
    fronts = {s: get_pareto_points(df[df['seed'] == s]) for s in seeds_present}
    all_f = pd.concat(fronts.values(), ignore_index=True)
    xm, ym, em = mean_frontier(all_f)
    f_at = interp(xm, ym, R_EW)
    per_seed = {s: interp(f['excess_risk'], f['excess_return'], R_EW) for s, f in fronts.items()}  # descriptive
    # R2 dominance: best return among points with risk <= R_EW (no interpolation)
    per_seed_dom = {s: (float(f.loc[f['excess_risk'] <= R_EW, 'excess_return'].max())
                        if (f['excess_risk'] <= R_EW).any() else None) for s, f in fronts.items()}
    mean_dom = float(ym[xm <= R_EW].max()) if (xm <= R_EW).any() else None
    n_seeds = len(seeds_present)

    # R1
    if n_seeds < 3:
        r1 = "판정 불가(시드 3개 미만)"
    elif f_at is None:
        r1 = "판정 불가(평균 프런티어가 R_EW에 닿지 않음)"
    else:
        r1 = "통과" if abs(f_at - F_REP) <= HALF else "미통과"
    # R2
    if n_seeds < 5:
        r2 = "판정 불가(시드 5개 미만)"
    elif mean_dom is None:
        r2 = "판정 불가(평균 프런티어에 R_EW 이하 점 없음)"
    else:
        n_above = sum(1 for v in per_seed_dom.values() if v is not None and v > EW_RET)
        r2 = "통과" if (mean_dom > EW_RET and n_above >= 4) else "미통과"

    return {
        "seeds": seeds_present, "n_points_per_seed": {s: int((df['seed'] == s).sum()) for s in seeds_present},
        "n_nan_rows_dropped": n_nan,
        "reported": {"R_EW": R_EW, "EW_RET": EW_RET, "F_REP": F_REP, "band": [F_REP - HALF, F_REP + HALF]},
        "mean_frontier_at_R_EW": f_at, "per_seed_frontier_at_R_EW": per_seed,
        "mean_frontier_max_risk": float(xm.max()) if len(xm) else None,
        "R2_mean_best_at_or_below_R_EW": mean_dom, "R2_per_seed_best_at_or_below_R_EW": per_seed_dom,
        "descriptive_at_12": {"ours": interp(xm, ym, 12.0), "fig": 10.42, "band_same_width": [10.42 - HALF, 10.42 + HALF]},
        "sensitivity_min_in_bin_30_at_R_EW": (lambda a: interp(a[0], a[1], R_EW))(mean_frontier(all_f, min_in_bin=30)),
        "R1": r1, "R2": r2,
        "descriptive_grid": {g: interp(xm, ym, g) for g in GRID},
        "mean_frontier": {"x": xm.tolist(), "y": ym.tolist(), "moe": em.tolist()},
    }


def selftest():
    rng = np.random.default_rng(1)
    rows = []
    for s in SEEDS:
        for i in range(504):
            r = rng.uniform(0.3, 18)
            rows.append(dict(gamma_trade=0, gamma_risk=i, seed=s, excess_risk=r,
                             excess_return=3.0 * np.sqrt(r) - rng.uniform(0, 4), sharpe=0))
    df = pd.DataFrame(rows)
    out = judge(df)
    print("synthetic:", out["R1"], out["R2"], round(out["mean_frontier_at_R_EW"], 2))
    df5 = df.copy(); df5.loc[df5['excess_risk'] > 13, 'excess_return'] = -50   # frontier ends ~13% but dominates EW
    out5 = judge(df5); print("ends at 13% but dominates:", out5["R1"], out5["R2"])
    df2 = df.copy(); df2['excess_return'] -= 5
    out2 = judge(df2); print("shifted -5:", out2["R1"], out2["R2"])
    df3 = df[df['seed'].isin(SEEDS[:3])]
    out3 = judge(df3); print("3 seeds:", out3["R1"], out3["R2"])
    df4 = df.copy(); df4['excess_risk'] *= 0.5
    out4 = judge(df4); print("short range (x0.5 risk):", out4["R1"], out4["R2"])


if __name__ == "__main__":
    if sys.argv[1] == "--selftest":
        selftest()
        sys.exit(0)
    d, outp = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(f"{d}/DOW_30_RL_CNN_seeds_*_etc.csv"))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    res = judge(df)
    res["files"] = files
    json.dump(res, open(outp, "w"), indent=1, ensure_ascii=False, default=str)
    print(json.dumps({k: res[k] for k in ("seeds", "mean_frontier_at_R_EW", "R1", "R2")}, ensure_ascii=False, default=str))
