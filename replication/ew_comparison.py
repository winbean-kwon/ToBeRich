# 탐색적 등가중 비교 — 사전 등록 notes/ew_comparison_prereg.md(2a8945b) 그대로.
# 사용: PYTHONPATH=.t3env/pylib python3 replication/ew_comparison.py <Ensemble 사본 폴더>
#   Ensemble 사본 폴더 = 서버 ~/f4work/ensemble/repo/data/dow_30_2009_2020.csv 와 ~/ToBeRich/data/funnel/ensemble_f7/E1–E5 를
#   같은 상대 경로로 복사한 곳. 결과: replication/ew_comparison.json
# 공통 등가중(2장): 그날 가격이 있는 종목 등가중, 매 거래일 종가에 재조정, 비용 = c × Σ|w_EW − w_표류|(현금 제외),
#   첫날 종가에 현금에서 매수(회전율 1, 비용 c). 가치 계열의 첫 값 = 1(첫날 매수 전 현금).
import json, os, pathlib, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "replication"))


def ew_values(P, c):
    """P: (T, n) 가격(NaN = 거래 불가). 반환 길이 T 가치 계열(첫 값 1)."""
    T, n = P.shape
    v = np.ones(T)
    ok0 = ~np.isnan(P[0])
    w = np.where(ok0, 1.0 / ok0.sum(), 0.0)
    val = 1.0 * (1 - c * 1.0)          # 첫날 종가에 현금 → 등가중 매수
    for t in range(1, T):
        ok = ~np.isnan(P[t]) & ~np.isnan(P[t - 1])
        r = np.where(ok, P[t] / np.where(ok, P[t - 1], 1.0) - 1, 0.0)
        g = 1 + float(w @ r)
        drift = w * (1 + r) / g
        tgt_ok = ~np.isnan(P[t])
        tgt = np.where(tgt_ok, 1.0 / tgt_ok.sum(), 0.0)
        val *= g * (1 - c * np.abs(tgt - drift).sum())
        v[t] = val
        w = tgt
    return v


def verdict(k, n):
    s = k / n
    return "실행 대부분이 같은 비용의 등가중을 넘었다" if s >= 0.8 else (
        "실행 대부분이 같은 비용의 등가중을 넘지 못했다" if s <= 0.2 else "실행에 따라 엇갈렸다")


# ------------------------------------------------------------------ DeepAries (T1)
def deeparies():
    import deeparies_run as dr
    c = 0.0001  # 구현 fee_rate(코드 기본, 헤더 고정 사항)
    px = dr.daily_panel("W0")
    sel = json.loads((ROOT / "replication/deeparies/judge_o1.json").read_text())["선택 시드(검증 손실 최소)"]
    rows, ew_cache = [], {}
    for s in range(10):
        df, meta = dr.load_run("W0", "a", s)
        cagr, _, d0, d1 = dr.code_metrics(df, meta)
        key = (d0, d1)
        if key not in ew_cache:
            sub = px.loc[d0.strftime("%Y-%m-%d"):d1.strftime("%Y-%m-%d")]
            days = (d1 - d0).days
            ew_cache[key] = {cc: (ew_values(sub.to_numpy(float), cc)[-1] ** (365 / days) - 1) * 100 for cc in (c, 0.0)}
        e = ew_cache[key]
        rows.append({"시드": s, "CAGR(%)": round(cagr, 3), "EW CAGR(%) c": round(e[c], 3), "EW CAGR(%) 0": round(e[0.0], 3),
                     "기간": f"{d0.date()}~{d1.date()}", "EW 초과": bool(cagr > e[c])})
    k = sum(r["EW 초과"] for r in rows)
    sr = next(r for r in rows if r["시드"] == sel) if isinstance(sel, int) else None
    if sr is None:
        sel_seed = sel.get("시드") if isinstance(sel, dict) else None
        sr = next(r for r in rows if r["시드"] == sel_seed)
    return {"c": c, "시드별": rows, "등가중(c) 초과": f"{k}/10", "해석": verdict(k, 10),
            "논문 규칙 선택 시드": sr["시드"], "선택 시드 CAGR − EW(c) (%p)": round(sr["CAGR(%)"] - sr["EW CAGR(%) c"], 3)}


# ------------------------------------------------------------------ MARS (T4)
def mars():
    import mars_t4 as m
    c = 0.001  # config.TRANSACTION_COST
    base = ROOT / ".marswork" / "L" / "data"
    t = pd.read_csv(base / "test_data.csv")
    t["date"] = t["Date"].astype(str).str[:10]
    cols = [k for k in t.columns if k.endswith("_Adj Close")]
    lo, hi = m.W240
    sub = t[(t.date >= lo) & (t.date <= hi)]
    P = sub[cols].to_numpy(float)
    ew = {cc: m.metrics(ew_values(P, cc)) for cc in (c, 0.0)}
    res = {"c": c, "EW(c) W240": {k: round(ew[c][k], 3) for k in ("CR", "SR")},
           "EW(0) W240": {k: round(ew[0.0][k], 3) for k in ("CR", "SR")}}
    for cond in ("L", "N"):
        rows = []
        for s in m.SEEDS:
            d = ROOT / "data" / "mars_t4" / cond / f"seed_{s}"
            if not (d / "done.json").exists():
                continue
            df = pd.read_csv(d / "test_results_detailed.csv")
            vals = m.slice_w240(df)
            dd = pd.to_datetime(df["date"].astype(str).str[:10])
            dsel = dd[(dd >= lo) & (dd <= hi)]
            assert list(dsel.dt.strftime("%Y-%m-%d")) == list(sub.date), "날짜 불일치"
            mm = m.metrics(vals)
            rows.append({"시드": s, "CR": round(mm["CR"], 3), "SR": round(mm["SR"], 3),
                         "CR>EW": bool(mm["CR"] > ew[c]["CR"]), "SR>EW": bool(mm["SR"] > ew[c]["SR"])})
        n = len(rows)
        kcr, ksr = sum(r["CR>EW"] for r in rows), sum(r["SR>EW"] for r in rows)
        med = {"CR": float(np.median([r["CR"] for r in rows])), "SR": float(np.median([r["SR"] for r in rows]))}
        res[cond] = {"시드별": rows, "CR 초과": f"{kcr}/{n}", "SR 초과": f"{ksr}/{n}",
                     "해석(CR)": verdict(kcr, n), "해석(SR)": verdict(ksr, n),
                     "중앙값 − EW(c)": {"CR(%p)": round(med["CR"] - ew[c]["CR"], 3), "SR": round(med["SR"] - ew[c]["SR"], 3)}}
    return res


# ------------------------------------------------------------------ Ensemble (Yang 2020)
def ensemble(copy_dir):
    import funnel_f7_ensemble_judge as ej
    c = 0.001  # TRANSACTION_FEE_PERCENT(env/EnvMultipleStock_*.py)
    cd = pathlib.Path(copy_dir)
    raw = pd.read_csv(cd / "f4work/ensemble/repo/data/dow_30_2009_2020.csv")
    raw["adjcp"] = raw.prccd / raw.ajexdi
    utd = raw[(raw.datadate > 20151001) & (raw.datadate <= 20200707)].datadate.unique()
    dates = utd[63:63 + ej.ROWS]      # 행 j ↔ unique_trade_date[63 + j] (정렬 가정, 결과 노트에 기록)
    P = raw.pivot(index="datadate", columns="tic", values="adjcp").loc[dates].to_numpy(float)
    ew = {cc: ej.metrics(list(ew_values(P, cc)))["sharpe"] for cc in (c, 0.0)}
    rows = []
    for k in range(1, 6):
        rd = cd / f"ToBeRich/data/funnel/ensemble_f7/E{k}"
        vals, _ = ej.read_run(rd)
        sh = ej.metrics(vals[:ej.ROWS])["sharpe"]
        rows.append({"실행": f"E{k}", "Sharpe": round(sh, 3), "EW 초과": bool(sh > ew[c])})
    kk = sum(r["EW 초과"] for r in rows)
    mean = float(np.mean([r["Sharpe"] for r in rows]))
    return {"c": c, "EW Sharpe(c)": round(ew[c], 3), "EW Sharpe(0)": round(ew[0.0], 3), "기간": f"{dates[0]}~{dates[-1]}",
            "실행별": rows, "등가중(c) 초과": f"{kk}/5", "해석": verdict(kk, 5), "평균 − EW(c)": round(mean - ew[c], 3)}


if __name__ == "__main__":
    out = {"사전 등록": "notes/ew_comparison_prereg.md (2a8945b)", "DeepAries": deeparies(), "MARS": mars(),
           "Ensemble": ensemble(sys.argv[1])}
    (ROOT / "replication" / "ew_comparison.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: {x: v.get(x) for x in ("등가중(c) 초과", "해석", "EW(c) W240", "EW Sharpe(c)")} if isinstance(v, dict) else v
                      for k, v in out.items()}, ensure_ascii=False, indent=1))
    print(json.dumps({c: {x: out["MARS"][c][x] for x in ("CR 초과", "SR 초과", "해석(CR)", "해석(SR)", "중앙값 − EW(c)")} for c in ("L", "N")},
                     ensure_ascii=False, indent=1))
