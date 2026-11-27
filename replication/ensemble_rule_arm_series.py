# replication/ensemble_rule_arm.py와 같은 규칙의 가치 계열을 함수로 제공한다(계산 동일, 탐색적 재사용용).
import pathlib
import numpy as np
import pandas as pd

C = 0.001


def rule_values(cd):
    import funnel_f7_ensemble_judge as ej
    cd = pathlib.Path(cd)
    raw = pd.read_csv(cd / "f4work/ensemble/repo/data/dow_30_2009_2020.csv")
    raw = raw[raw.datadate >= 20090000].copy()
    raw["adjcp"] = raw.prccd / raw.ajexdi
    piv = raw.pivot(index="datadate", columns="tic", values="adjcp").sort_index()
    P = piv.to_numpy(float); dates_all = piv.index.to_numpy()
    turb = np.zeros(len(dates_all)); count = 0
    for i in range(252, len(dates_all)):
        hist = P[:i]; dlt = P[i] - hist.mean(axis=0)
        t = float(dlt @ np.linalg.inv(np.cov(hist, rowvar=False)) @ dlt)
        if t > 0:
            count += 1
            turb[i] = t if count > 2 else 0.0
    utd = raw[(raw.datadate > 20151001) & (raw.datadate <= 20200707)].datadate.unique()
    dates = utd[63:63 + ej.ROWS]
    pos = {d: k for k, d in enumerate(dates_all)}
    Pt = piv.loc[dates].to_numpy(float)
    thr = np.array([140 if (63 * (d // 63 + 1)) < 692 else (100 if (63 * (d // 63 + 1)) < 1090 else 90)
                    for d in range(63, 63 + len(dates))])
    tu = np.array([turb[pos[d]] for d in dates])
    n = Pt.shape[1]; ew = np.full(n, 1 / n)
    v = np.ones(len(dates)); val = 1.0
    cash = tu[0] >= thr[0]
    w = np.zeros(n) if cash else ew.copy()
    val *= (1 - C * (0 if cash else 1.0))
    for t in range(1, len(dates)):
        r = Pt[t] / Pt[t - 1] - 1
        g = 1 + float(w @ r)
        drift = w * (1 + r) / g if w.sum() > 0 else w
        tgt = np.zeros(n) if tu[t] >= thr[t] else ew
        val *= g * (1 - C * np.abs(tgt - drift).sum())
        v[t] = val; w = tgt.copy()
    return v
