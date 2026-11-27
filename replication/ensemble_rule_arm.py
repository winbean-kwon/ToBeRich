# 탐색적(사전 고정, 실행 전 커밋): Ensemble F7 구간(2016-01-04~2020-05-12, 1,097행)에서 RL 없이
# "등가중 + 같은 난류 현금 규칙"만 쓴 포트폴리오를 Ensemble 5회 실행과 비교한다. 이미 본 구간이라 판정이 아니다.
# 규칙(고정, notes/ensemble_postpub_prereg.md 3장 (c)와 같음):
#   - 난류 지수: 코드 preprocessing.calcualte_turbulence와 같은 식(가격 수준 adjcp, 첫 252일 0, 양수 3번째부터)으로
#     번들 dow_30_2009_2020.csv에서 다시 계산하고, 번들 dow30_turbulence_index.csv와 대조해 보고한다.
#   - 문턱: 코드 일정 그대로. 날짜 인덱스 d(unique_trade_date 기준)는 사이클 i = 63·(d//63 + 1)의 거래 창에 속하고,
#     i < 692 → 140, 692 ≤ i < 1090 → 100, i ≥ 1090 → 90.
#   - 매일 종가: 난류 ≥ 문턱이면 전량 현금(비용 0.1% × 매도액), 아니면 등가중 재조정(비용 0.1% × 회전율).
#     현금에서 시작(첫날 매수 비용). 현금 수익 0.
#   - 지표: replication/funnel_f7_ensemble_judge.py의 metrics(Sharpe 등), 행–날짜 대응은 replication/ew_comparison.py와 같다.
#   - 보고: 규칙 포트폴리오 Sharpe, 등가중 Sharpe, Ensemble 5회 Sharpe, Ensemble > 규칙인 실행 수, 2020 전·후 분할.
# 사용: PYTHONPATH=.t3env/pylib python3 replication/ensemble_rule_arm.py <Ensemble 사본 폴더> <번들 난류 CSV>
import json, pathlib, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "replication"))
import ew_comparison as ec, funnel_f7_ensemble_judge as ej

C = 0.001
cd, turb_csv = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
raw = pd.read_csv(cd / "f4work/ensemble/repo/data/dow_30_2009_2020.csv")
raw = raw[raw.datadate >= 20090000].copy()
raw["adjcp"] = raw.prccd / raw.ajexdi
piv = raw.pivot(index="datadate", columns="tic", values="adjcp").sort_index()
dates_all = piv.index.to_numpy()

# 난류(코드 식 그대로: hist = 그날 이전 전체, cov, (x−mean)·inv(cov)·(x−mean)ᵀ, 양수 셋째부터 기록)
turb = np.zeros(len(dates_all)); count = 0
P = piv.to_numpy(float)
for i in range(252, len(dates_all)):
    hist = P[:i]; cur = P[i]
    cov = np.cov(hist, rowvar=False)
    dlt = cur - hist.mean(axis=0)
    t = float(dlt @ np.linalg.inv(cov) @ dlt)
    if t > 0:
        count += 1
        turb[i] = t if count > 2 else 0.0
tb = pd.read_csv(turb_csv).set_index("datadate").turbulence.reindex(dates_all).to_numpy()
turb_check = {"max_abs_diff": float(np.nanmax(np.abs(turb - tb))), "corr": float(np.corrcoef(turb[300:], tb[300:])[0, 1])}

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
days_cash = int(cash)
for t in range(1, len(dates)):
    r = Pt[t] / Pt[t - 1] - 1
    g = 1 + float(w @ r)
    drift = w * (1 + r) / g if w.sum() > 0 else w
    if tu[t] >= thr[t]:
        tgt = np.zeros(n); days_cash += 1
    else:
        tgt = ew
    held = drift * (w.sum() > 0)
    val *= g * (1 - C * np.abs(tgt - held).sum())
    v[t] = val; w = tgt.copy()

rule = ej.metrics(list(v))["sharpe"]
ewv = ec.ew_values(Pt, C); ews = ej.metrics(list(ewv))["sharpe"]
cut = int(np.searchsorted(dates, 20200101))
runs = []
for k in range(1, 6):
    vals, _ = ej.read_run(cd / f"ToBeRich/data/funnel/ensemble_f7/E{k}"); vals = vals[:ej.ROWS]
    runs.append({"run": f"E{k}", "sharpe": round(ej.metrics(vals)["sharpe"], 3),
                 "sharpe_pre2020": round(ej.metrics(vals[:cut])["sharpe"], 3)})
out = {"turbulence_check_vs_bundle": turb_check, "cash_days": days_cash, "rows": len(dates),
       "rule_sharpe": round(rule, 3), "rule_sharpe_pre2020": round(ej.metrics(list(v[:cut]))["sharpe"], 3),
       "ew_sharpe": round(ews, 3), "ew_sharpe_pre2020": round(ej.metrics(list(ewv[:cut]))["sharpe"], 3),
       "ensemble_runs": runs, "ensemble_above_rule": sum(r["sharpe"] > rule for r in runs),
       "rule_cum": round(v[-1] - 1, 4), "rule_mdd": round(ej.metrics(list(v))["mdd"], 4)}
(ROOT / "replication" / "ensemble_rule_arm.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
