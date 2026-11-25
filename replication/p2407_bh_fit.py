"""Exploratory (post-hoc) check for P24-07: is each author KDD run curve a buy-and-hold curve of the 5 tickers?

Rule fixed before opening richard1-3 (notes/funnel_f7x_p2407_prereg.md section 7):
  For start day d = 1..30 (trading-day index; day 0 is the 10,000 cash row), fit
      V_t = c + sum_i n_i * close_{i,t},  t >= d
  by least squares, round n_i to the nearest integer, refit c as the mean residual, and record the max absolute
  residual. The curve is "buy-and-hold from day d" if n_i >= 0 for all i and max |residual| <= 0.01 USD.
  Report the smallest such d (or "none up to day 30").
  Classes: d <= 5 -> "사실상 매수 후 보유(처음 며칠 매수)"; 5 < d <= 30 -> "초반 거래 후 보유"; none -> "매수 후 보유 아님(5종목 기준)".
  Control: the already-checked author curve (richard.csv = originate_ddpg.csv) must come out as d = 1, UNH 96, AAPL 1.

Usage: python p2407_bh_fit.py TRADE_CSV CURVE_CSV [CURVE_CSV ...]
"""
import json
import sys

import numpy as np
import pandas as pd

TOL = 0.01
MAX_D = 30


def fit(px, v):
    out = None
    for d in range(1, MAX_D + 1):
        P, y = px[d:], v[d:]
        X = np.column_stack([np.ones(len(P)), P])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        n = np.rint(coef[1:])
        c = float(np.mean(y - P @ n))
        res = float(np.max(np.abs(y - c - P @ n)))
        if out is None or res < out["max_abs_resid"]:
            out = {"best_d": d, "max_abs_resid": res, "shares": n.tolist(), "cash": c}
        if (n >= 0).all() and res <= TOL:
            return {"d": d, "max_abs_resid": res, "shares": n.tolist(), "cash": c}
    return {"d": None, "closest": out}


def main(trade_csv, curves):
    t = pd.read_csv(trade_csv, index_col=0, parse_dates=["date"])
    px = t.pivot(index="date", columns="tic", values="close").sort_index()
    tics = list(px.columns)
    res = {"tickers": tics}
    for path in curves:
        c = pd.read_csv(path, index_col=0, parse_dates=["date"])
        assert list(c["date"]) == list(px.index), path
        r = fit(px.values, c["account_value"].values)
        if r["d"] is None:
            r["class"] = "매수 후 보유 아님(5종목 기준)"
        else:
            r["class"] = "사실상 매수 후 보유(처음 며칠 매수)" if r["d"] <= 5 else "초반 거래 후 보유"
            r["holdings"] = {k: int(s) for k, s in zip(tics, r["shares"]) if s}
        res[path.split("/")[-1]] = r
    return res


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1], sys.argv[2:]), ensure_ascii=False, indent=1))
