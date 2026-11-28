# 탐색적(사전 등록 notes/turbulence_returns_prereg.md 그대로, 계산 전 커밋).
# 사용: PYTHONPATH=.t3env/pylib python3 replication/turbulence_returns.py <Ensemble F7 사본 폴더> <dow_29_2009_2025.csv>
import json, pathlib, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "replication"))
import funnel_f7_ensemble_judge as ej
import ensemble_rule_arm_series as ra
from ew_comparison import ew_values

C = 0.001


def returns_turbulence(P):
    """P: (T, n) 가격. d_t = (r_t − μ)ᵀ Σ⁻¹ (r_t − μ), μ·Σ는 t 이전 수익률 전체. 처음 252일 0."""
    R = P[1:] / P[:-1] - 1
    d = np.zeros(len(P))
    for t in range(252, len(P)):
        hist = R[:t - 1]                 # r_1..r_{t-1} (t일 수익 r_t = R[t-1]은 제외)
        dl = R[t - 1] - hist.mean(axis=0)
        d[t] = float(dl @ np.linalg.pinv(np.cov(hist, rowvar=False)) @ dl)
    return d


def rule_series(P, cash_flag):
    n = P.shape[1]; ew = np.full(n, 1 / n); v = np.ones(len(P)); val = 1.0
    w = np.zeros(n) if cash_flag[0] else ew.copy(); val *= (1 - C * (0 if cash_flag[0] else 1.0))
    for t in range(1, len(P)):
        r = P[t] / P[t - 1] - 1; g = 1 + float(w @ r)
        drift = w * (1 + r) / g if w.sum() > 0 else w
        tgt = np.zeros(n) if cash_flag[t] else ew
        val *= g * (1 - C * np.abs(tgt - drift).sum()); v[t] = val; w = tgt.copy()
    return v


def sh(v):
    return round(ej.metrics(list(v))["sharpe"], 3)


def period(piv, dates, d_all, taus, runs):
    pos = {x: i for i, x in enumerate(piv.index)}
    P = piv.loc[dates].to_numpy(float); dd = np.array([d_all[pos[x]] for x in dates])
    out = {"rows": len(dates), "start": int(dates[0]), "end": int(dates[-1]), "ew": sh(ew_values(P, C)), "ensemble_runs": runs}
    for name, tau in taus.items():
        flag = dd >= tau
        s = sh(rule_series(P, flag))
        out[f"rule_returns_{name}"] = {"sharpe": s, "cash_days": int(flag.sum()),
                                       "ensemble_runs_above": sum(r > s for r in runs)}
    return out


if __name__ == "__main__":
    cd, new_csv = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    res = {"prereg": "notes/turbulence_returns_prereg.md (62e1f41)"}
    # (A) 원 시험 구간, 번들 30종목
    raw = pd.read_csv(cd / "f4work/ensemble/repo/data/dow_30_2009_2020.csv"); raw = raw[raw.datadate >= 20090000].copy()
    raw["adjcp"] = raw.prccd / raw.ajexdi
    piv = raw.pivot(index="datadate", columns="tic", values="adjcp").sort_index()
    d_all = returns_turbulence(piv.to_numpy(float))
    insample = d_all[(piv.index >= 20090102) & (piv.index <= 20151231)]
    insample = insample[insample > 0]
    taus = {"q90": float(np.quantile(insample, 0.90)), "q95": float(np.quantile(insample, 0.95))}
    res["tau"] = {k: round(v, 3) for k, v in taus.items()}
    utd = raw[(raw.datadate > 20151001) & (raw.datadate <= 20200707)].datadate.unique()
    datesA = utd[63:63 + ej.ROWS]
    runsA = []
    for k in range(1, 6):
        vals, _ = ej.read_run(cd / f"ToBeRich/data/funnel/ensemble_f7/E{k}"); runsA.append(sh(vals[:ej.ROWS]))
    A = period(piv, datesA, d_all, taus, runsA)
    A["rule_code_price_level"] = sh(ra.rule_values(cd))
    res["A_2016_2020"] = A
    # (B) 출판 이후, 29종목
    nw = pd.read_csv(new_csv); nw["adjcp"] = nw.prccd / nw.ajexdi
    pivB = nw.pivot(index="datadate", columns="tic", values="adjcp").sort_index()
    d_allB = returns_turbulence(pivB.to_numpy(float))
    plan = json.loads((ROOT / "replication/ensemble_postpub29/out/plan.json").read_text())
    utdB = nw[(nw.datadate > 20200707) & (nw.datadate <= int(plan["END"]))].datadate.unique()
    rowsB = 63 * len(plan["ITERS"])
    datesB = utdB[63:63 + rowsB]
    runsB = []
    for k in range(1, 6):
        rd = ROOT / f"replication/ensemble_postpub29/out/E{k}"
        vals = []
        for i in plan["ITERS"]:
            vals += pd.read_csv(rd / "account_value" / f"account_value_trade_ensemble_{i}.csv")["0"].tolist()
        runsB.append(sh(vals[:rowsB]))
    B = period(pivB, datesB, d_allB, taus, runsB)
    jr = json.loads((ROOT / "replication/ensemble_postpub29/judge_result.json").read_text())
    B["judge_result_keys_for_reference"] = list(jr)[:12]
    res["B_2020_2025"] = B
    (ROOT / "replication" / "turbulence_returns.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float))
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
