# 보정 계산(심사 지적): 사전 등록 문구 그대로 2009–2015 지수의 분위를 0 포함으로 계산한 문턱(주 결과로 삼음).
# replication/turbulence_returns.py의 함수를 그대로 쓰고 문턱만 바꾼다. 현금 전환 횟수(현금 진입 수)도 기록.
import json, pathlib, sys
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "replication"))
import turbulence_returns as tr, funnel_f7_ensemble_judge as ej
from ew_comparison import ew_values
cd, new_csv = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
raw = pd.read_csv(cd / "f4work/ensemble/repo/data/dow_30_2009_2020.csv"); raw = raw[raw.datadate >= 20090000].copy(); raw["adjcp"] = raw.prccd / raw.ajexdi
piv = raw.pivot(index="datadate", columns="tic", values="adjcp").sort_index(); d_all = tr.returns_turbulence(piv.to_numpy(float))
ins = d_all[(piv.index >= 20090102) & (piv.index <= 20151231)]
taus = {"q90_zero_incl": float(np.quantile(ins, 0.90)), "q95_zero_incl": float(np.quantile(ins, 0.95)),
        "q90_pos_only": float(np.quantile(ins[ins > 0], 0.90)), "q95_pos_only": float(np.quantile(ins[ins > 0], 0.95))}
def run(pv, dates, d, tag):
    pos = {x: i for i, x in enumerate(pv.index)}; P = pv.loc[dates].to_numpy(float); dd = np.array([d[pos[x]] for x in dates])
    o = {"ew": round(ej.metrics(list(ew_values(P, tr.C)))["sharpe"], 3)}
    for k, t in taus.items():
        f = dd >= t; o[k] = {"sharpe": tr.sh(tr.rule_series(P, f)), "cash_days": int(f.sum()), "cash_entries": int(((~f[:-1]) & f[1:]).sum() + f[0])}
    return o
utd = raw[(raw.datadate > 20151001) & (raw.datadate <= 20200707)].datadate.unique()
res = {"tau": {k: round(v, 3) for k, v in taus.items()}, "A": run(piv, utd[63:63 + ej.ROWS], d_all, "A")}
nw = pd.read_csv(new_csv); nw["adjcp"] = nw.prccd / nw.ajexdi; pB = nw.pivot(index="datadate", columns="tic", values="adjcp").sort_index()
assert not pB.isna().any().any(), "NaN in 29-stock prices"
plan = json.loads((ROOT / "replication/ensemble_postpub29/out/plan.json").read_text())
uB = nw[(nw.datadate > 20200707) & (nw.datadate <= int(plan["END"]))].datadate.unique()
res["B"] = run(pB, uB[63:63 + 63 * len(plan["ITERS"])], tr.returns_turbulence(pB.to_numpy(float)), "B")
(ROOT / "replication/turbulence_returns_zeroincl.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
