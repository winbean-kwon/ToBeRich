# -*- coding: utf-8 -*-
# Ensemble 출판 이후 검정 — 탐색판(WBA 제외 29종목) 판정 계산. 사전 등록 notes/ensemble_postpub_29_prereg.md(33f5819),
# 주 사전 등록 notes/ensemble_postpub_prereg.md 3·4·5장. 탐색판이므로 k1·k2와 문장은 "탐색적 기술"로만 쓴다.
# 계산(고정):
#   - 날짜: 새 데이터 unique_trade_date = datadate > 20200707, ≤ END(plan.json). 사이클 ITERS(plan.json)의 account_value
#     파일을 순서대로 이어 붙인 행 j ↔ unique_trade_date[63 + j](7.7 비교·replication/ew_comparison.py와 같은 대응,
#     창 첫 행 반복 포함). 행 수 = 63·len(ITERS), 모두 사용(F7의 1,097행 자르기는 논문 구간 전용이라 쓰지 않음).
#   - (a) Ensemble E1–E5, (b) EW = ew_comparison.ew_values(P, 0.001), (c) EW+난류 = ensemble_rule_arm.py와 같은 규칙
#     (난류 ≥ 그날 문턱이면 전량 현금, 문턱 = 사이클 i = 63·(d//63+1)에 대해 i<692→140, <1090→100, 그 밖→90),
#     난류 지수는 코드 preprocessing.calcualte_turbulence를 새 데이터(calcualte_price 결과)에 직접 호출해 얻는다.
#     (c′) 문턱 140 고정판(탐색적, 5장). (d) ^DJI 종가, 비용 없음.
#   - 지표: replication/funnel_f7_ensemble_judge.metrics(empyrical식 Sharpe·누적·MDD).
#   - k1 = #{Sharpe(E) > Sharpe(b)}, k2 = #{Sharpe(E) > Sharpe(c)}. ≥4 / ≤1 / 그 밖 문장은 4장.
#   - 보조: 평균 Sharpe − (b)·(c)·(d); 블록 부트스트랩은 7장 효과 크기와 같은 도구 replication/stat_power/run.py의
#     test()(원형 블록, 블록 20일 주, 5·10일 민감도, 4,999회, 스튜던트화 95% 구간, 같은 날짜 블록을 기준선과 5회 모두에
#     공통 적용 = 실행 조건부)로 ΔSR(5회 평균 SR − 기준선 SR, ddof=0)과 ΔG(연율 로그 성장 차)를 계산한다. 유의성 주장 없음.
#     난류 규칙 현금 일수, 누적 수익·MDD.
# 사용: python3 replication/ensemble_postpub29_judge.py <사본 폴더(out/E1..E5, out/plan.json)> <dow_29 CSV> <DJI.csv>
#        <저장소 코드 폴더(preprocessing/preprocessors.py)>
# 결과: replication/ensemble_postpub29/judge_result.json
import hashlib, importlib.util, json, pathlib, sys, types
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "replication"))
import ew_comparison as ec, funnel_f7_ensemble_judge as ej

C = 0.001
PRE_SHA = "46a27892e237ff1b71aeef66073d04b985f393ef87203949ffb4def0ca370a9d"  # 서버 repo preprocessors.py
B, BLOCKS, B_MAIN = 4999, (20, 5, 10), 20


def load_stat_power():
    spec = importlib.util.spec_from_file_location("sp_run", ROOT / "replication/stat_power/run.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def code_turbulence(code_dir, raw):
    p = pathlib.Path(code_dir) / "preprocessing/preprocessors.py"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == PRE_SHA, "preprocessors.py 해시 다름"
    sys.modules.setdefault("stockstats", types.SimpleNamespace(StockDataFrame=None))
    cfg = types.ModuleType("config"); cfg.config = types.SimpleNamespace(); sys.modules["config"] = cfg
    spec = importlib.util.spec_from_file_location("ens_pre", p)
    pre = importlib.util.module_from_spec(spec); spec.loader.exec_module(pre)
    d = pre.calcualte_price(raw[raw.datadate >= 20090000])
    t = pre.calcualte_turbulence(d)
    return t.set_index("datadate").turbulence


def verdict(k, hi, lo, mid):
    return hi if k >= 4 else (lo if k <= 1 else mid)


def rule_values(Pt, tu, thr):
    n = Pt.shape[1]; ew = np.full(n, 1 / n)
    v = np.ones(len(tu)); val = 1.0
    cash = tu[0] >= thr[0]
    w = np.zeros(n) if cash else ew.copy()
    val *= (1 - C * (0 if cash else 1.0))
    days_cash = int(cash); spells = int(cash)
    for t in range(1, len(tu)):
        r = Pt[t] / Pt[t - 1] - 1
        g = 1 + float(w @ r)
        drift = w * (1 + r) / g if w.sum() > 0 else w
        if tu[t] >= thr[t]:
            tgt = np.zeros(n); days_cash += 1; spells += int(tu[t - 1] < thr[t - 1])
        else:
            tgt = ew
        held = drift * (w.sum() > 0)
        val *= g * (1 - C * np.abs(tgt - held).sum())
        v[t] = val; w = tgt.copy()
    return v, days_cash, spells


def rets(v):
    v = np.asarray(v, float); return v[1:] / v[:-1] - 1


def main(cd, data_csv, dji_csv, code_dir):
    cd = pathlib.Path(cd)
    plan = json.loads((cd / "out/plan.json").read_text())
    ITERS, END = plan["ITERS"], plan["END"]
    raw = pd.read_csv(data_csv)
    raw = raw[raw.datadate >= 20090000].copy()
    raw["adjcp"] = raw.prccd / raw.ajexdi
    piv = raw.pivot(index="datadate", columns="tic", values="adjcp").sort_index()
    utd = np.array(sorted(raw[(raw.datadate > 20200707) & (raw.datadate <= END)].datadate.unique()))
    assert len(utd) == plan["n_utd"]
    rows = 63 * len(ITERS)
    dates = utd[63:63 + rows]
    assert len(dates) == rows
    Pt = piv.loc[dates].to_numpy(float)
    assert not np.isnan(Pt).any()

    # (a) Ensemble
    runs, R = {}, {}
    for k in range(1, 6):
        rd = cd / f"out/E{k}"
        st = json.loads((rd / "done.json").read_text()).get("status") if (rd / "done.json").exists() else "missing"
        if st != "ok":
            runs[f"E{k}"] = {"status": st}; continue
        vals, per = [], []
        for i in ITERS:
            x = pd.read_csv(rd / "account_value" / f"account_value_trade_ensemble_{i}.csv")["0"].tolist()
            per.append(len(x)); vals += x
        assert len(vals) == rows, (k, len(vals), rows)
        m = ej.metrics(vals)
        runs[f"E{k}"] = {"status": "ok", "rows_per_file": sorted(set(per)), **{q: m[q] for q in ("sharpe", "cum", "ann", "vol", "mdd")}}
        R[f"E{k}"] = rets(vals)
    ok = [k for k in runs if runs[k]["status"] == "ok"]

    # (b) EW
    ewv = ec.ew_values(Pt, C); ewm = ej.metrics(list(ewv))
    # (c) EW + 코드 난류 규칙, (c′) 문턱 140 고정
    turb = code_turbulence(code_dir, raw)
    tu = turb.reindex(dates).to_numpy(float)
    assert not np.isnan(tu).any()
    thr = np.array([140 if (63 * (d // 63 + 1)) < 692 else (100 if (63 * (d // 63 + 1)) < 1090 else 90)
                    for d in range(63, 63 + rows)])
    rv, cash_days, spells = rule_values(Pt, tu, thr); rm = ej.metrics(list(rv))
    rv140, cash140, sp140 = rule_values(Pt, tu, np.full(rows, 140)); rm140 = ej.metrics(list(rv140))
    # (d) DJIA
    dj = pd.read_csv(dji_csv)
    dj["datadate"] = dj.Date.str.replace("-", "").astype(int)
    djs = dj.set_index("datadate").Close.reindex(dates)
    dj_missing = int(djs.isna().sum())
    djv = djs.ffill().bfill().to_numpy(float); djm = ej.metrics(list(djv))

    out = {"사전 등록": "notes/ensemble_postpub_29_prereg.md (33f5819) + notes/ensemble_postpub_prereg.md (탐색판, 판정 수 미포함)",
           "기간": [int(dates[0]), int(dates[-1])], "행 수": rows, "사이클 수": len(ITERS), "END": END,
           "n_completed": len(ok), "runs": runs,
           "EW": {q: ewm[q] for q in ("sharpe", "cum", "ann", "vol", "mdd")},
           "EW+난류": {**{q: rm[q] for q in ("sharpe", "cum", "ann", "vol", "mdd")}, "현금 일수": cash_days, "현금 구간 수": spells,
                     "문턱 일정(행 수)": {str(x): int((thr == x).sum()) for x in (140, 100, 90)}},
           "EW+난류 140 고정(탐색적)": {**{q: rm140[q] for q in ("sharpe", "cum", "mdd")}, "현금 일수": cash140, "현금 구간 수": sp140},
           "DJIA": {**{q: djm[q] for q in ("sharpe", "cum", "ann", "vol", "mdd")}, "결측 날짜(앞값 채움)": dj_missing},
           "난류 지수(시험 구간)": {"max": float(tu.max()), "median": float(np.median(tu)),
                              "문턱 이상 날짜": [int(d) for d, a, b in zip(dates, tu, thr) if a >= b][:200]}}
    if len(ok) == 5:
        sh = np.array([runs[k]["sharpe"] for k in ok])
        k1, k2 = int((sh > ewm["sharpe"]).sum()), int((sh > rm["sharpe"]).sum())
        out["k1 (Sharpe > EW)"] = k1
        out["k1 기술(탐색적)"] = verdict(k1, "출판 이후 기간에도 같은 비용의 등가중을 넘은 것으로 관찰됐다",
                                       "같은 비용의 등가중을 넘지 못한 것으로 관찰됐다", "엇갈렸다")
        out["k2 (Sharpe > EW+난류)"] = k2
        out["k2 기술(탐색적)"] = verdict(k2, "RL 정책이 같은 난류 규칙의 등가중보다 나은 것으로 관찰됐다",
                                       "같은 규칙의 등가중보다 낫지 않은 것으로 관찰됐다", "엇갈렸다")
        out["k (Sharpe > EW+난류 140 고정, 탐색적)"] = int((sh > rm140["sharpe"]).sum())
        out["k (Sharpe > DJIA, 참고)"] = int((sh > djm["sharpe"]).sum())
        out["평균 Sharpe"] = {"Ensemble": float(sh.mean()), "EW": ewm["sharpe"], "EW+난류": rm["sharpe"], "DJIA": djm["sharpe"],
                            "Ensemble − EW": float(sh.mean() - ewm["sharpe"]), "Ensemble − EW+난류": float(sh.mean() - rm["sharpe"]),
                            "Ensemble − DJIA": float(sh.mean() - djm["sharpe"])}
        out["평균 누적·MDD(Ensemble)"] = {"cum": float(np.mean([runs[k]["cum"] for k in ok])),
                                     "mdd": float(np.mean([runs[k]["mdd"] for k in ok]))}
        sp = load_stat_power()
        E = np.column_stack([R[k] for k in ok])
        boot = {}
        for name, base in (("EW", rets(ewv)), ("EW+난류", rets(rv)), ("DJIA", rets(djv))):
            X = np.column_stack([base, E])
            boot[name] = {"rho(실행, 기준선)": [float(np.corrcoef(base, E[:, j])[0, 1]) for j in range(5)]}
            for metric in ("SR", "G"):
                for b in BLOCKS:
                    r = sp.test([X], metric, B, b, sp.rng_for("postpub29", name, metric, b))
                    boot[name][f"{metric}/b{b}"] = {q: r[q] for q in ("theta", "ci95", "se_hac", "sd_boot", "mde80")}
        out["블록 부트스트랩(보조, 7장 도구, 실행 조건부)"] = boot
    (ROOT / "replication/ensemble_postpub29").mkdir(exist_ok=True)
    (ROOT / "replication/ensemble_postpub29/judge_result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float))
    return out


if __name__ == "__main__":
    o = main(*sys.argv[1:5])
    print(json.dumps({k: v for k, v in o.items() if k not in ("runs", "난류 지수(시험 구간)", "블록 부트스트랩(보조, 7장 도구, 실행 조건부)")},
                     ensure_ascii=False, indent=1, default=float))
