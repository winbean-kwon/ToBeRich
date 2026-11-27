# 탐색적 — 사전 등록 notes/ew_comparison2_prereg.md(ead5e08) 그대로. 실행 전 커밋.
# (1) Margin Trader(탐색적 F7x, 조건 P 시드 0–4): 같은 비용 롱 전용 등가중과 Sharpe 비교.
#     등가중 = replication/ew_comparison.py의 ew_values(ew_comparison_prereg.md 2장 규칙), 해석 = 같은 파일의 verdict(3장).
#     종목·가격: env가 쓰는 data.csv(서버 ~/f4work/mt/out/data.csv, sha256 7b824748…)의 `close` 열(env가 data.close를 가격으로 씀),
#       trade 구간 날짜 = 각 실행 trade_result.csv의 날짜(시드마다 같아야 함, assert).
#     c = 0.001: runs/P_s0/trading_margin_a2c.py:95 `buy_cost_list = sell_cost_list = [0.001] * stock_dimension`.
#       marginEnv.py에서 롱 매수·매도는 현금에 (1±c)로 한 번 부과(state[2] 감소는 _update_state에서 현금+시가−대출로 재계산되어 덮어씀),
#       공매도·환매는 credit에서 c로 한 번 부과 → 구현 율 = 0.001(양방향).
#     Sharpe: F7x 판정 스크립트가 읽는 pyfolio perf_stats Sharpe(= sqrt(252)·mean/std(ddof=1), 무위험률 0, 일간 수익률).
#       등가중에도 같은 식(selection_inflation.sharpe) 적용. 실행의 Sharpe는 perf_stats_trade.csv 값을 쓰고,
#       account value에서 같은 식으로 다시 계산한 값과 1e-6 이내로 일치하는지 assert.
# (2) Ensemble 대 난류 규칙: selection_inflation.py B부와 같은 계산을 블록 5·10·20·40일로(4,999회, 시드 0).
# 사용: PYTHONPATH=.t3env/pylib OMP_NUM_THREADS=1 python3 replication/ew_comparison2.py <MT 사본 폴더> <Ensemble 사본 폴더>
#   MT 사본 폴더: runs/P_s{0-4}/results/*/a2c/{trade_result.csv,perf_stats_trade.csv}, data_2020_2023.csv(data.csv의 2020–2023 행).
import csv, glob, json, pathlib, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "replication"))
from ew_comparison import ew_values, verdict
from selection_inflation import boot_ci, sharpe

C_MT = 0.001
BLOCKS = [5, 10, 20, 40]


def margin_trader(md):
    md = pathlib.Path(md)
    runs, dates = [], None
    for s in range(5):
        rd = pathlib.Path(glob.glob(str(md / f"runs/P_s{s}/results/*/a2c"))[0])
        tr = pd.read_csv(rd / "trade_result.csv")
        assert tr["a2c"].notna().all(), "a2c 결측"
        d = list(tr["date"].astype(str))
        if dates is None:
            dates = d
        assert d == dates, "시드 간 날짜 불일치"
        v = tr["a2c"].to_numpy(float)
        perf = {r[0]: float(r[1]) for r in csv.reader(open(rd / "perf_stats_trade.csv")) if len(r) >= 2 and r[0] == "Sharpe ratio"}
        sh_re = sharpe(np.diff(v) / v[:-1])
        assert abs(sh_re - perf["Sharpe ratio"]) < 1e-6, (s, sh_re, perf)
        runs.append({"시드": s, "Sharpe": round(perf["Sharpe ratio"], 3)})
    px = pd.read_csv(md / "data_2020_2023.csv", index_col=0)
    px["date"] = px["date"].astype(str)
    piv = px.pivot(index="date", columns="tic", values="close").sort_index()
    sub = piv.loc[dates[0]:dates[-1]]
    assert list(sub.index) == dates, f"가격 날짜와 가치 계열 날짜 불일치: {len(sub)} vs {len(dates)}"
    P = sub.to_numpy(float)
    ew = {}
    for cc in (C_MT, 0.0):
        ve = ew_values(P, cc)
        ew[cc] = sharpe(np.diff(ve) / ve[:-1])
    for r in runs:
        r["EW 초과"] = bool(r["Sharpe"] > ew[C_MT])
    k = sum(r["EW 초과"] for r in runs)
    mean = float(np.mean([r["Sharpe"] for r in runs]))
    return {"c": C_MT, "c 출처": "trading_margin_a2c.py:95 (P 판), marginEnv.py 롱 123·187행, 숏 238·281행",
            "종목 수": int(P.shape[1]), "결측 가격 칸": int(np.isnan(P).sum()), "기간": f"{dates[0]}~{dates[-1]}", "일수": len(dates),
            "EW Sharpe(c)": round(ew[C_MT], 3), "EW Sharpe(0)": round(ew[0.0], 3),
            "시드별": runs, "등가중(c) 초과": f"{k}/5", "해석": verdict(k, 5),
            "평균 Sharpe": round(mean, 3), "평균 − EW(c)": round(mean - ew[C_MT], 3),
            "비고": "롱 전용 등가중 대 마진·공매도 방법(비교 기준이 롱 전용)"}


def block_sensitivity(cd):
    import funnel_f7_ensemble_judge as ej
    import ensemble_rule_arm_series as ra
    rule_v = ra.rule_values(cd)
    rr = np.diff(rule_v) / rule_v[:-1]
    allr, names = [], []
    for k in range(1, 6):
        vals, _ = ej.read_run(pathlib.Path(cd) / f"ToBeRich/data/funnel/ensemble_f7/E{k}")
        v = np.array(vals[:ej.ROWS]); allr.append(np.diff(v) / v[:-1]); names.append(f"E{k}")
    m = np.mean(allr, axis=0)
    out = {"rule_sharpe": round(sharpe(rr), 3),
           "sharpe_minus_rule": {**{n: round(sharpe(r) - sharpe(rr), 3) for n, r in zip(names, allr)},
                                 "mean_series": round(sharpe(m) - sharpe(rr), 3)},
           "blocks": {}}
    for b in BLOCKS:
        row = {}
        for n, r in list(zip(names, allr)) + [("mean_series", m)]:
            ci = boot_ci(r, rr, b=b)
            row[n] = {"ci95": ci, "contains_0": bool(ci[0] <= 0 <= ci[1])}
        out["blocks"][str(b)] = row
    ref = out["blocks"]["20"]
    out["0 포함 여부가 블록 20과 다른 경우"] = [f"b={b} {n}" for b in BLOCKS for n in ref
                                       if out["blocks"][str(b)][n]["contains_0"] != ref[n]["contains_0"]]
    return out


if __name__ == "__main__":
    res = {"사전 등록": "notes/ew_comparison2_prereg.md (ead5e08)", "지위": "탐색적",
           "1_margin_trader": margin_trader(sys.argv[1]), "2_block_sensitivity": block_sensitivity(sys.argv[2])}
    (ROOT / "replication" / "ew_comparison2.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))
