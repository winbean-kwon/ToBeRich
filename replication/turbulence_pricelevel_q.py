# 탐색적(사전 등록 notes/turbulence_pricelevel_q_prereg.md, 계산 전 커밋): 가격 수준 난류 지수 + 시험 전 분위 문턱.
# 사용: PYTHONPATH=.t3env/pylib python3 replication/turbulence_pricelevel_q.py <Ensemble F7 사본 폴더> <dow_29_2009_2025.csv>
import json, pathlib, sys
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "replication"))
import turbulence_returns as tr, funnel_f7_ensemble_judge as ej
from ew_comparison import ew_values


def price_level_turbulence(P):
    """코드 calcualte_turbulence와 같은 식(ensemble_rule_arm.py에서 코드 함수와 6e-11 일치 확인)."""
    d = np.zeros(len(P)); count = 0
    for i in range(252, len(P)):
        h = P[:i]; dl = P[i] - h.mean(axis=0); t = float(dl @ np.linalg.inv(np.cov(h, rowvar=False)) @ dl)
        if t > 0:
            count += 1; d[i] = t if count > 2 else 0.0
    return d


def run(pv, dates, d, taus):
    pos = {x: i for i, x in enumerate(pv.index)}; P = pv.loc[dates].to_numpy(float); dd = np.array([d[pos[x]] for x in dates])
    o = {"ew": round(ej.metrics(list(ew_values(P, tr.C)))["sharpe"], 3), "index_median": round(float(np.median(dd)), 2)}
    for k, t in taus.items():
        f = dd >= t
        o[k] = {"sharpe": tr.sh(tr.rule_series(P, f)), "cash_days": int(f.sum()), "cash_entries": int(((~f[:-1]) & f[1:]).sum() + f[0])}
    return o


cd, new_csv = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
raw = pd.read_csv(cd / "f4work/ensemble/repo/data/dow_30_2009_2020.csv"); raw = raw[raw.datadate >= 20090000].copy(); raw["adjcp"] = raw.prccd / raw.ajexdi
piv = raw.pivot(index="datadate", columns="tic", values="adjcp").sort_index(); dA = price_level_turbulence(piv.to_numpy(float))
ins = dA[(piv.index >= 20090102) & (piv.index <= 20151231)]
taus = {"q90": float(np.quantile(ins, 0.90)), "q95": float(np.quantile(ins, 0.95))}
utd = raw[(raw.datadate > 20151001) & (raw.datadate <= 20200707)].datadate.unique()
res = {"prereg": "notes/turbulence_pricelevel_q_prereg.md", "tau": {k: round(v, 2) for k, v in taus.items()},
       "A": run(piv, utd[63:63 + ej.ROWS], dA, taus)}
nw = pd.read_csv(new_csv); nw["adjcp"] = nw.prccd / nw.ajexdi; pB = nw.pivot(index="datadate", columns="tic", values="adjcp").sort_index()
plan = json.loads((ROOT / "replication/ensemble_postpub29/out/plan.json").read_text())
uB = nw[(nw.datadate > 20200707) & (nw.datadate <= int(plan["END"]))].datadate.unique()
dB = price_level_turbulence(pB.to_numpy(float))
insB = dB[(pB.index >= 20090102) & (pB.index <= 20151231)]
tausB = {"q90": float(np.quantile(insB, 0.90)), "q95": float(np.quantile(insB, 0.95))}
res["tau_B_29stocks"] = {k: round(v, 2) for k, v in tausB.items()}
res["B"] = run(pB, uB[63:63 + 63 * len(plan["ITERS"])], dB, taus)            # 주: A의 문턱을 같이 적용(사전 등록)
res["B_aux_own_tau"] = run(pB, uB[63:63 + 63 * len(plan["ITERS"])], dB, tausB)  # 보조: 29종목 자체 분위
ew = res["A"]["ew"]; s = res["A"]["q90"]["sharpe"]
res["verdict_A"] = ("가격 수준 지수만으로도 우위가 남는다" if s >= ew + 0.3 else
                    ("가격 수준 지수에 시험 전 문턱을 쓰면 우위가 없다" if s < ew else "우위는 코드의 문턱 일정에 의존한다"))
(ROOT / "replication/turbulence_pricelevel_q.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps(res, ensure_ascii=False, indent=1))
