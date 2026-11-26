# Ensemble 출판 이후 검정 — 데이터 만들기와 겹침 대조(사전 등록 notes/ensemble_postpub_prereg.md 2장 그대로).
# 사용: PYTHONPATH=.t3env/pylib python3 replication/ensemble_postpub_data.py <번들 CSV> <출력 폴더>
# 출력: <출력 폴더>/dow_30_2009_2025.csv(번들 형식), replication/ensemble_postpub/data_check.json
import json, pathlib, sys
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUNDLE, OUTDIR = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUTDIR.mkdir(parents=True, exist_ok=True)
RES = ROOT / "replication" / "ensemble_postpub"; RES.mkdir(parents=True, exist_ok=True)
TICS = ["AAPL", "AXP", "BA", "CAT", "CSCO", "CVX", "DD", "DIS", "GS", "HD", "IBM", "INTC", "JNJ", "JPM", "KO",
        "MCD", "MMM", "MRK", "MSFT", "NKE", "PFE", "PG", "RTX", "TRV", "UNH", "V", "VZ", "WBA", "WMT", "XOM"]
CAP, MIN_END = 20251231, 20250630

b = pd.read_csv(BUNDLE)
assert sorted(b.tic.unique()) == sorted(TICS), "번들 종목이 사전 등록 목록과 다름"

frames = []
for t in TICS:
    d = yf.download(t, start="2009-01-01", end="2026-01-01", auto_adjust=False, actions=False, progress=False)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d = d.dropna(subset=["Close"])
    frames.append(pd.DataFrame({"datadate": d.index.strftime("%Y%m%d").astype(int), "tic": t,
                                "prccd": d["Close"].values, "ajexdi": 1.0, "prcod": d["Open"].values,
                                "prchd": d["High"].values, "prcld": d["Low"].values, "cshtrd": d["Volume"].values}))
new = pd.concat(frames, ignore_index=True)

# 종료일: 30종목 모두 가격이 있는 마지막 날(≤ CAP). 2009 이후 30종목이 다 있는 날짜 집합에서, 마지막 연속 구간 끝.
cnt = new[new.datadate <= CAP].groupby("datadate").tic.nunique()
last_per_tic = new.groupby("tic").datadate.max()
early = last_per_tic[last_per_tic < MIN_END]
full_days = cnt[cnt == 30].index
after = cnt[cnt.index > 20200707]
first_gap = after[after < 30].index.min() if (after < 30).any() else None
end = int(full_days.max()) if first_gap is None else int(full_days[full_days < first_gap].max())
check = {"종목별 마지막 날": {k: int(v) for k, v in last_per_tic.items()}, "2025-06-30 이전 끊긴 종목": list(early.index),
         "종료일": end, "2020-07-07 이후 30종목 미만 첫날": None if first_gap is None else int(first_gap)}

# 겹침 대조 2016-01-04~2020-07-07: adjcp 일별 수익률 상관 ≥ 0.99, |차이| 중앙값 ≤ 0.001
b["adjcp"] = b.prccd / b.ajexdi
new["adjcp"] = new.prccd / new.ajexdi
ov = {}
for t in TICS:
    x = b[(b.tic == t) & (b.datadate >= 20160104) & (b.datadate <= 20200707)].set_index("datadate").adjcp
    y = new[(new.tic == t) & (new.datadate >= 20160104) & (new.datadate <= 20200707)].set_index("datadate").adjcp
    j = x.index.intersection(y.index)
    rx, ry = x.loc[j].pct_change().dropna(), y.loc[j].pct_change().dropna()
    corr = float(np.corrcoef(rx, ry)[0, 1]); med = float(np.median(np.abs(rx - ry)))
    ov[t] = {"n": len(j), "상관": round(corr, 5), "차이 중앙값": round(med, 6), "통과": bool(corr >= 0.99 and med <= 0.001)}
check["겹침 대조"] = ov
check["관문 통과"] = bool(all(v["통과"] for v in ov.values()) and not len(early))
(RES / "data_check.json").write_text(json.dumps(check, ensure_ascii=False, indent=1))
if check["관문 통과"]:
    out = new[new.datadate <= end].drop(columns="adjcp").sort_values(["datadate", "tic"]).reset_index(drop=True)
    out.insert(0, "", range(len(out)))
    out.to_csv(OUTDIR / "dow_30_2009_2025.csv", index=False)
print(json.dumps({k: check[k] for k in ("종료일", "2025-06-30 이전 끊긴 종목", "2020-07-07 이후 30종목 미만 첫날", "관문 통과")}, ensure_ascii=False))
print("실패 종목:", {t: v for t, v in ov.items() if not v["통과"]})
