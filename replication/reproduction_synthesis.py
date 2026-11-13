"""재현 종합표(기술 통계, 탐색적). 판정을 새로 내리지 않고, 행을 합산한 재현율을 만들지 않는다.

각 행은 논문과 같은 방식으로 집계한 값을 보고값과 나란히 적는다. 시드 분포는 참고용이다.

값의 출처
- 우리 값·시드 값·등급: 아래 judge JSON에서 직접 읽는다(손으로 옮겨 적지 않음).
    DeepAries  replication/deeparies/judge_o1.json, replication/deeparies/e10/judge_e1.json·judge_e10.json·judge_e.json
    AlphaMix+  replication/alphamix_t2/judge_o1.json
    FinRL      replication/finrl_t3/o1/judge_W0.json
    MARS       data/mars_t4/judge_o1.json, data/mars_t4/aux_o1.json
    Ensemble   replication/funnel_f7/ensemble_judge_result.json (깔때기 F7, 순서 규칙으로 선택)
    RAT        replication/funnel_f7/rat_f7_result.json (깔때기 F7)
- 논문 보고값: judge JSON에 들어 있는 값을 쓰고, JSON에 없는 것만 아래 PAPER_ONLY에 둔다.
  보고값은 모두 논문 원문과 대조해야 한다(notes/claim_ledger.csv).

실행: python3 replication/reproduction_synthesis.py → replication/reproduction_synthesis.csv
"""
import csv
import json
import pathlib
import statistics as st

ROOT = pathlib.Path(__file__).resolve().parent.parent

# judge JSON에 없는 논문 값. 원문 대조 전에는 인용하지 않는다.
PAPER_ONLY = {
    "deeparies_dji_cagr": 6.15,                      # DeepAries 논문의 ^DJI CAGR
    "alphamix_sigma": {"S2021": 1.8, "S2020": 1.7, "S2019": 1.42},  # AlphaMix+ 보고 시드 σ(arXiv v3)
    "finrl_djia": 32.84,                             # FinRL 논문의 DJIA 연수익
    "mars_tol_cr": 7.07,                             # = replication/mars_t4.py TOL["CR"](사전 등록)
}


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def r2(x):
    return None if x is None else round(x, 2)


def row(name, metric, agg, rep, tol, how, ours, paper_base, our_base, seeds, grade, note):
    return {"대상": name, "지표": metric, "논문 집계": agg, "보고값": rep, "허용 폭": tol, "우리 집계 방식": how,
            "우리 값": r2(ours), "차이(우리-보고)": r2(ours - rep),
            "논문 우위": "" if paper_base is None else r2(rep - paper_base), "우리 우위": r2(ours - our_base),
            "시드 수": len(seeds), "시드 최소": r2(min(seeds)), "시드 최대": r2(max(seeds)),
            "시드 SD": r2(st.stdev(seeds)) if len(seeds) > 1 else "",
            # 공통 기술 지표(탐색적, 2026-11-13 추가, 판정 아님): 대상마다 다른 등급을 비교 가능하게 보조
            "허용 폭 안 시드": f"{sum(abs(x - rep) <= tol for x in seeds)}/{len(seeds)}",
            "보고값 이하 시드 비율": round(sum(x <= rep for x in seeds) / len(seeds), 2),
            "등급": grade, "비고": note}


def deeparies_rows():
    out = []
    o1 = load("replication/deeparies/judge_o1.json")
    e = load("replication/deeparies/e10/judge_e.json")
    specs = [("DeepAries O1(맥)", o1, o1["R1"], o1["등급"], "주 판정"),
             ("DeepAries e1(Colab, 탐색적)", load("replication/deeparies/e10/judge_e1.json"), e["R1"]["e1"], "환경 대조",
              f"맥과 환경만 다름(judge 등급: {e['등급']['e1']})"),
             ("DeepAries E(10 epoch, Colab)", load("replication/deeparies/e10/judge_e10.json"), e["R1"]["e10"], e["등급"]["e10"],
              "e1과 다섯 시드가 같아 독립 아님")]
    for name, j, r1, grade, note in specs:
        per = j["시드별"]
        sel = min(per, key=lambda s: s["검증 손실"])
        assert abs(sel["CAGR(%)"] - r1["선택 CAGR"]) < 1e-9, name  # 선택 시드가 judge와 같은지
        out.append(row(name, "CAGR", "10시드 중 검증 손실 최소" if not out else "같음", r1["보고값"][0], r1["허용 폭"][0], "선택 시드",
                       sel["CAGR(%)"], PAPER_ONLY["deeparies_dji_cagr"], sel["^DJI CAGR(%)"],
                       [s["CAGR(%)"] for s in per], grade, note))
    return out


def alphamix_rows():
    j = load("replication/alphamix_t2/judge_o1.json")
    out = []
    for stage in ("S2021", "S2020", "S2019"):
        s = j["stages"][stage]
        seeds = [v["tr"] for v in s["seeds"].values()]
        assert abs(st.mean(seeds) - s["tr_mean"]) < 1e-9
        out.append(row(f"AlphaMix+ {stage}", "TR", f"5시드 평균(σ {PAPER_ONLY['alphamix_sigma'][stage]})", s["paper_tr"], s["tol"],
                       "시드 평균", s["tr_mean"], None, s["ew_tr"], seeds, j["grade"] + "*", "R1 ✓" if s["R1"] else "R1 ✗"))
    return out


def finrl_rows():
    j = load("replication/finrl_t3/o1/judge_W0.json")
    extra = {"a2c": "28종목(논문 30)", "ppo": "28종목", "td3": "28종목",
             "ddpg": "28종목, R1 허용 폭 초과(차이 0.005%p, 반올림 전 값 기준 — JSON 값은 소수 2자리라 여기서 재계산 불가)"}
    out = []
    for a in j["알고리즘"]:
        seeds = a["seed별 연수익(%)"]
        out.append(row(f"FinRL {a['algo'].upper()}", "연수익", "미기재", a["보고값"], a["허용폭"], "시드 중앙값", a["중앙값"],
                       PAPER_ONLY["finrl_djia"], j["DJIA 연수익(%)"], seeds, a["등급"], extra[a["algo"]]))
    return out


def mars_rows():
    j = load("data/mars_t4/judge_o1.json")
    aux = load("data/mars_t4/aux_o1.json")
    p, pd_, tol = j["paper"], j["paper_dji"], PAPER_ONLY["mars_tol_cr"]
    dji = j["reference"]["DJI"]["W240"]["CR"]
    ew = j["reference"]["EW_cost0"]["W240"]
    out = []
    for cond, name, lead in (("L", "MARS L(논문 시점 코드)", "주 판정"), ("N", "MARS N(저자 수정본)", "병기")):
        c, a = j[cond], aux[cond]
        seeds = [v["W240"]["CR"] for v in c["seeds"].values()]
        w251 = a["windows"]["W251"]
        note = (f"{lead}. SR 중앙 {c['median']['SR']:.2f}(보고 {p['SR']}±0.715). "
                f"시드 42 CR {c['seed42_W240']['CR']:.2f}({c['n_seeds']}개 중 {a['seed42_rank_CR']}위). "
                f"허용 폭 안 시드 {c['within_tol']}/{c['n_seeds']}. "
                f"DJI·1/N(무비용 {ew['CR']:.2f}/{ew['SR']:.2f}) CR·SR 모두 넘은 시드 {c['beat_dji']}/{c['n_seeds']}·{c['beat_ew_cost0']}/{c['n_seeds']}. "
                f"W251(탐색적): R1 {'통과' if w251['R1'] else '실패'}(SR 차 {w251['SR_gap']:.3f}), "
                f"R2 {'통과' if w251['R2_computed'] else '실패'}(DJI 초과 {w251['beat_DJI_computed']})")
        if cond == "N":  # 코드 읽기 관찰(JSON 밖): notes/mars_t4_o1_result.md
            note += ". BMID 대역이 체크포인트 추가 커밋에서 넓어짐"
        out.append(row(name, "CR(W240)", "미기재(시드 42 명시)" if cond == "L" else "같음", p["CR"], tol, "10시드 중앙값",
                       c["median"]["CR"], pd_["CR"], dji, seeds, c["grade"], note))
    cc = j["C"]["W240"]
    note = (f"R1만 판정. SR {cc['SR']:.2f}, AVol {cc['AVol']:.2f}(보고 {p['AVol']}), MDD {cc['MDD']:.2f}(보고 {p['MDD']}). "
            f"결정적={j['C']['deterministic']}. 체크포인트 선택 경위 미기재라 일반 성능 근거로 쓰지 않음")
    out.append(row("MARS C(번들 체크포인트)", "CR(W240)", "같음", p["CR"], tol, "결정적 1회", cc["CR"], pd_["CR"], dji, [cc["CR"]],
                   "R1 통과" if j["C"]["R1"] else "R1 실패", note))
    return out


def funnel_f7_rows():
    """깔때기 F7(프로토콜 3.3 순서로 선택된 논문). T1~T4와 따로 집계한다."""
    out = []
    j = load("replication/funnel_f7/ensemble_judge_result.json")
    seeds = [j["runs"][k]["main"]["sharpe"] for k in sorted(j["runs"]) if j["runs"][k]["status"] == "ok"]
    assert abs(st.mean(seeds) - j["R1"]["mean_sharpe"]) < 1e-12
    tol = round((j["R1"]["band"][1] - j["R1"]["band"][0]) / 2, 3)
    out.append(row("Ensemble F7(깔때기, 서버 CPU)", "Sharpe(1,097행)", "미기재", 1.30, tol, "5회 산술평균(시드 미고정)",
                   j["R1"]["mean_sharpe"], 0.47, j["aux_djia"]["ours"]["sharpe"], seeds, j["grade"],
                   f"R1 통과·R2 실패({j['R2']['count']}/5 > {j['R2']['bar']}); 비교 대상 DJIA"))
    r = load("replication/funnel_f7/rat_f7_result.json")
    seeds = [x["fAPV"] for x in r["P_runs"]]
    assert abs(st.mean(seeds) - r["P_summary"]["mean_fAPV"]) < 1e-6
    lo, hi = r["R1_A_range"]
    out.append(row("RAT F7 P(깔때기, GTX 1650)", "fAPV(Crypto-A)", "5회 평균", r["report"]["APV"], round((hi - lo) / 2, 2),
                   "5회 산술평균(시드 미고정, 시험 구간 체크포인트 선택=코드)", r["P_summary"]["mean_fAPV"], r["MTL"]["APV"],
                   r["UCRP(점검)"]["APV"], seeds, r["grade_P"],
                   f"R1 {r['R1_A(주)']}(보고값보다 높음)·R2 {r['R2']}; 논문 비교 대상 MTL, 우리 비교 대상 열은 UCRP(점검용)"))
    return out


def main():
    out = deeparies_rows() + alphamix_rows() + finrl_rows() + mars_rows() + funnel_f7_rows()
    with open(ROOT / "replication/reproduction_synthesis.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for r in out:
        print(" | ".join(str(r[k]) for k in ["대상", "보고값", "허용 폭", "우리 값", "차이(우리-보고)", "논문 우위", "우리 우위",
                                             "시드 최소", "시드 최대", "등급"]))


if __name__ == "__main__":
    main()
