# 탐색적(규칙 고정, 실행 전 커밋). 이미 있는 출력만 쓴다. 학습 없음.
# A. AlphaMix+ DJ30(T2 O1 출력, replication/alphamix_t2/o1/<단계>_s<시드>/result.csv): 결과 선택 규칙에 따른 시드 평균 시험 TR.
#    규칙: (i) 시드별 검증 TR 최고 epoch, (ii) 시드별 시험 TR 최고 epoch(시험 기반 선택 = 부풀림 상한),
#    (iii) 고정 epoch e* = argmax_e (시드 평균 시험 TR)(저자 SZ50 노트북처럼 시험 평균으로 하나를 고름),
#    (iv) 마지막 평가 epoch, (v) 모든 epoch 평균. 각 규칙의 R1(논문 TR ± 허용 폭, T2 판정 스크립트 상수) 통과 여부.
#    보고: (ii) − (i), (iii) − (i) = 시험 기반 선택이 시드 평균을 얼마나 올리는가.
# B. Ensemble F7 구간: Ensemble 각 실행 vs "등가중 + 같은 난류 규칙"(replication/ensemble_rule_arm.py와 같은 계열)의
#    Sharpe 차이에 대한 짝지은 순환 블록 부트스트랩 95% 구간(블록 20일, 4,999회, 시드 0). 실행별 + 5회 평균 계열.
# 사용: PYTHONPATH=.t3env/pylib python3 replication/selection_inflation.py <Ensemble 사본 폴더>
import json, pathlib, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "replication"))
PAPER_TR = {"S2021": 20.7, "S2020": 12.7, "S2019": 25.1}
TOL_TR = {"S2021": 1.61, "S2020": 1.52, "S2019": 1.27}


def part_a():
    out = {}
    for st in PAPER_TR:
        runs = sorted((ROOT / "replication/alphamix_t2/o1").glob(f"{st}_s*/result.csv"))
        dfs = [pd.read_csv(f, index_col=0) for f in runs]
        n_ep = min(len(d) for d in dfs)
        dfs = [d.iloc[:n_ep] for d in dfs]
        tr = np.array([d.test_tr.values for d in dfs]) * 100   # (시드, epoch), %
        ev = np.array([d.eval_tr.values for d in dfs])
        rules = {
            "i_val_best": float(np.mean([tr[s, ev[s].argmax()] for s in range(len(dfs))])),
            "ii_test_best": float(np.mean(tr.max(axis=1))),
            "iii_fixed_epoch_by_test_mean": float(tr.mean(axis=0).max()),
            "iv_last_epoch": float(tr[:, -1].mean()),
            "v_all_epoch_mean": float(tr.mean()),
        }
        out[st] = {"n_seeds": len(dfs), "n_epochs": n_ep, "paper": PAPER_TR[st], "tol": TOL_TR[st],
                   **{k: round(v, 3) for k, v in rules.items()},
                   "R1": {k: bool(abs(v - PAPER_TR[st]) <= TOL_TR[st]) for k, v in rules.items()},
                   "ii_minus_i": round(rules["ii_test_best"] - rules["i_val_best"], 3),
                   "iii_minus_i": round(rules["iii_fixed_epoch_by_test_mean"] - rules["i_val_best"], 3)}
    return out


def sharpe(r):
    return float(np.sqrt(252) * r.mean() / r.std(ddof=1))


def boot_ci(ra, rb, B=4999, b=20, seed=0):
    rng = np.random.default_rng(seed); n = len(ra); k = int(np.ceil(n / b)); ds = np.empty(B)
    for j in range(B):
        st = rng.integers(0, n, k); idx = ((st[:, None] + np.arange(b)[None, :]) % n).ravel()[:n]
        ds[j] = sharpe(ra[idx]) - sharpe(rb[idx])
    return [round(float(np.percentile(ds, 2.5)), 3), round(float(np.percentile(ds, 97.5)), 3)]


def part_b(cd):
    import funnel_f7_ensemble_judge as ej
    import ensemble_rule_arm_series as ra   # 아래에서 만드는 규칙 계열(같은 규칙)
    rule_v = ra.rule_values(cd)
    rr = np.diff(rule_v) / rule_v[:-1]
    out = {"rule_sharpe": round(sharpe(rr), 3), "runs": []}
    allr = []
    for k in range(1, 6):
        vals, _ = ej.read_run(pathlib.Path(cd) / f"ToBeRich/data/funnel/ensemble_f7/E{k}")
        v = np.array(vals[:ej.ROWS]); r = np.diff(v) / v[:-1]; allr.append(r)
        out["runs"].append({"run": f"E{k}", "sharpe_minus_rule": round(sharpe(r) - sharpe(rr), 3), "ci95": boot_ci(r, rr)})
    m = np.mean(allr, axis=0)
    out["mean_series"] = {"sharpe_minus_rule": round(sharpe(m) - sharpe(rr), 3), "ci95": boot_ci(m, rr)}
    return out


if __name__ == "__main__":
    res = {"A_alphamix_dj30": part_a(), "B_ensemble_vs_rule": part_b(sys.argv[1])}
    (ROOT / "replication" / "selection_inflation.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))
