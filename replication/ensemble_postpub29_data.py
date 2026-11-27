# Ensemble 출판 이후 검정 — 탐색판(WBA 제외 29종목). 사전 등록 notes/ensemble_postpub_29_prereg.md(33f5819)와
# 주 사전 등록 notes/ensemble_postpub_prereg.md 2장 규칙(원천·필드 대응·종료일·겹침 대조)을 29종목에 그대로 적용한다.
# replication/ensemble_postpub_data.py를 고친 것: 종목 목록에서 WBA를 뺐고(번들 30 − WBA), "30종목" 조건을 "29종목"으로,
# 학습 구간(2009-01~2020-07-07)에 29종목 미만인 날이 있으면 관문 실패로 기록한다(코드의 STOCK_DIM 가정 점검, 대체 규칙 없음).
# ^DJI(비교군 (d))도 같은 방식으로 받는다.
# 사용: python3 replication/ensemble_postpub29_data.py <번들 CSV> <출력 폴더>
# 출력: <출력 폴더>/dow_29_2009_2025.csv(번들 형식), <출력 폴더>/DJI.csv, replication/ensemble_postpub29/data_check.json
import json, pathlib, sys
import numpy as np
import pandas as pd
import yfinance as yf

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUNDLE, OUTDIR = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
OUTDIR.mkdir(parents=True, exist_ok=True)
RES = ROOT / "replication" / "ensemble_postpub29"; RES.mkdir(parents=True, exist_ok=True)
TICS30 = ["AAPL", "AXP", "BA", "CAT", "CSCO", "CVX", "DD", "DIS", "GS", "HD", "IBM", "INTC", "JNJ", "JPM", "KO",
          "MCD", "MMM", "MRK", "MSFT", "NKE", "PFE", "PG", "RTX", "TRV", "UNH", "V", "VZ", "WBA", "WMT", "XOM"]
TICS = [t for t in TICS30 if t != "WBA"]
N = len(TICS); assert N == 29
CAP, MIN_END = 20251231, 20250630

b = pd.read_csv(BUNDLE)
assert sorted(b.tic.unique()) == sorted(TICS30), "번들 종목이 사전 등록 목록과 다름"


def get(t):
    d = yf.download(t, start="2009-01-01", end="2026-01-01", auto_adjust=False, actions=False, progress=False)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    return d.dropna(subset=["Close"])


frames = []
for t in TICS:
    d = get(t)
    frames.append(pd.DataFrame({"datadate": d.index.strftime("%Y%m%d").astype(int), "tic": t,
                                "prccd": d["Close"].values, "ajexdi": 1.0, "prcod": d["Open"].values,
                                "prchd": d["High"].values, "prcld": d["Low"].values, "cshtrd": d["Volume"].values}))
new = pd.concat(frames, ignore_index=True)
new = new[new.datadate >= 20090000]

# 종료일: 29종목 모두 가격이 있는 마지막 날(≤ CAP). 2020-07-07 이후 29종목 미만 첫날이 있으면 그 전 마지막 완전한 날.
cnt = new[new.datadate <= CAP].groupby("datadate").tic.nunique()
last_per_tic = new.groupby("tic").datadate.max()
early = last_per_tic[last_per_tic < MIN_END]
full_days = cnt[cnt == N].index
after = cnt[cnt.index > 20200707]
first_gap = after[after < N].index.min() if (after < N).any() else None
end = int(full_days.max()) if first_gap is None else int(full_days[full_days < first_gap].max())
pre_gaps = [int(x) for x in cnt[(cnt.index <= 20200707) & (cnt < N)].index]
check = {"사전 등록": "notes/ensemble_postpub_29_prereg.md (33f5819), notes/ensemble_postpub_prereg.md 2장",
         "종목": TICS, "종목별 첫날": {k: int(v) for k, v in new.groupby("tic").datadate.min().items()},
         "종목별 마지막 날": {k: int(v) for k, v in last_per_tic.items()}, "2025-06-30 이전 끊긴 종목": list(early.index),
         "종료일": end, "2020-07-07 이후 29종목 미만 첫날": None if first_gap is None else int(first_gap),
         "2009-01~2020-07-07 29종목 미만 날": pre_gaps}

# 겹침 대조 2016-01-04~2020-07-07: adjcp 일별 수익률 상관 ≥ 0.99, |차이| 중앙값 ≤ 0.001
b["adjcp"] = b.prccd / b.ajexdi
new["adjcp"] = new.prccd / new.ajexdi
ov = {}
for t in TICS:
    x = b[(b.tic == t) & (b.datadate >= 20160104) & (b.datadate <= 20200707)].set_index("datadate").adjcp
    y = new[(new.tic == t) & (new.datadate >= 20160104) & (new.datadate <= 20200707)].set_index("datadate").adjcp
    j = x.index.intersection(y.index)
    rx, ry = x.loc[j].pct_change().dropna(), y.loc[j].pct_change().dropna()
    rx, ry = rx.drop([d for d in {"DD": [20190402, 20190603], "RTX": [20200403]}.get(t, []) if d in rx.index]), ry.drop([d for d in {"DD": [20190402, 20190603], "RTX": [20200403]}.get(t, []) if d in ry.index])  # 수정 v2: 분사일 3일 제외
    corr = float(np.corrcoef(rx, ry)[0, 1]); med = float(np.median(np.abs(rx - ry)))
    ov[t] = {"n": len(j), "n_bundle": len(x), "상관": round(corr, 5), "차이 중앙값": round(med, 6),
             "통과": bool(corr >= 0.99 and med <= 0.001)}
check["겹침 대조"] = ov
check["관문 통과"] = bool(all(v["통과"] for v in ov.values()) and not len(early) and not pre_gaps)

dj = get("^DJI")
dj = pd.DataFrame({"Date": dj.index.strftime("%Y-%m-%d"), "Close": dj["Close"].values, "Adj Close": dj["Adj Close"].values})
dj.to_csv(OUTDIR / "DJI.csv", index=False)
check["DJI 행 수"] = len(dj)

if check["관문 통과"]:
    out = new[new.datadate <= end].drop(columns="adjcp").sort_values(["datadate", "tic"]).reset_index(drop=True)
    out.insert(0, "", range(len(out)))
    out.to_csv(OUTDIR / "dow_29_2009_2025.csv", index=False)
    check["CSV 행 수"] = len(out)
    check["CSV 날짜 수"] = int(out.datadate.nunique())
(RES / "data_check.json").write_text(json.dumps(check, ensure_ascii=False, indent=1))
print(json.dumps({k: check[k] for k in ("종료일", "2025-06-30 이전 끊긴 종목", "2020-07-07 이후 29종목 미만 첫날",
                                        "2009-01~2020-07-07 29종목 미만 날", "관문 통과")}, ensure_ascii=False))
print("실패 종목:", {t: v for t, v in ov.items() if not v["통과"]})
