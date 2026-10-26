"""
[감사 재현 · 2026-10-26] 생존 편향 점검 — 같은 규칙을 '나중 시점 44종목'과 '시점 고정(PIT) 13종목'에 적용해 비교한다.

인수인계 문서의 '44종목 1주 모멘텀 +128% → PIT 13종목 2021~24 등가중 대비 0/4년'은 스크립트 없이 계산된 수치라
재현할 수 없었다. 이 스크립트가 그 비교를 고정된 규칙으로 다시 만든다(결과를 보기 전에 아래 규칙을 커밋).

규칙(고정):
  - 데이터: crypto/data/features_5m/*.parquet 의 5분봉 종가 → UTC 일별 마지막 종가
  - 유니버스: (a) live_universe.json 44종목(2026년 거래대금 기준 선정 = 사후 선정), (b) PIT 13종목
    (2021-01-01 시가총액 상위 중 바이낸스 현물 생존 종목). 각 시점에 가격이 있는 종목만 포함.
  - 전략: 매주 월요일(UTC) 0시 리밸런싱. 직전 7일 수익률 상위 k = max(1, n // 4)개 등가중 보유(롱 온리).
  - 기준: 같은 유니버스 등가중, 매주 월요일 리밸런싱.
  - 비용: 0.1% × 회전율(양쪽 모두 동일 적용). 리밸런싱 사이에는 가격 변동에 따라 비중이 흘러간다.
  - 보고: 연도별(2021~2025) 로그 수익률, 초과 = 모멘텀 − 등가중, 초과가 양수인 연도 수.
  - 판정 없음(기술 통계). 연도 구간은 그 해 첫 월요일~다음 해 첫 월요일 직전.

실행: python -m crypto.experiments.survivorship_check  → crypto/experiments/results/survivorship_check.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FEAT = ROOT / "crypto" / "data" / "features_5m"
OUT = ROOT / "crypto" / "experiments" / "results" / "survivorship_check.csv"
PIT13 = ["BTC", "ETH", "XRP", "LTC", "BCH", "ADA", "BNB", "LINK", "XLM", "TRX", "DOT", "THETA", "XTZ"]
TC = 0.001
YEARS = [2021, 2022, 2023, 2024, 2025]


def daily_close(sym: str) -> pd.Series:
    d = pd.read_parquet(FEAT / f"{sym}USDT.parquet", columns=["datetime", "close"])
    s = d.set_index(pd.to_datetime(d["datetime"], utc=True))["close"].astype(float)
    return s.resample("1D").last().dropna().rename(sym)


def weekly_backtest(px: pd.DataFrame, momentum: bool) -> pd.Series:
    """주간 로그 수익률(비용 후). px: 일별 종가(열=종목)."""
    mondays = px.index[px.index.dayofweek == 0]
    w_prev = pd.Series(0.0, index=px.columns)
    out = {}
    for t0, t1 in zip(mondays[:-1], mondays[1:]):
        p0, p1 = px.loc[t0], px.loc[t1]
        live = p0.notna() & p1.notna()
        if momentum:
            lb = t0 - pd.Timedelta(days=7)
            if lb not in px.index:
                continue
            mom = (p0 / px.loc[lb])[live & px.loc[lb].notna()].dropna()
            if mom.empty:
                continue
            k = max(1, int(live.sum()) // 4)
            pick = mom.nlargest(k).index
        else:
            pick = live[live].index
            if len(pick) == 0:
                continue
        w = pd.Series(0.0, index=px.columns)
        w[pick] = 1.0 / len(pick)
        cost = TC * float((w - w_prev).abs().sum())
        r = (p1 / p0 - 1).fillna(0.0)
        gross = float((w * r).sum())
        out[t1] = np.log1p(gross) + np.log1p(-cost)
        w_prev = w * (1 + r) / (1 + gross)
    return pd.Series(out)


def main() -> None:
    u44 = [s.split("/")[0] for s in json.loads((ROOT / "crypto" / "data" / "live_universe.json").read_text())]
    syms = sorted(set(u44) | set(PIT13))
    px = pd.concat([daily_close(s) for s in syms], axis=1).sort_index()
    rows = []
    for name, uni in [("44종목(사후 선정)", u44), ("PIT 13종목", PIT13)]:
        mom = weekly_backtest(px[uni], momentum=True)
        ew = weekly_backtest(px[uni], momentum=False)
        for y in YEARS:
            m, e = mom[mom.index.year == y], ew[ew.index.year == y]
            if len(m) < 20:
                continue
            n_live = int(px[uni].loc[str(y)].notna().any().sum())
            rows.append({"유니버스": name, "연도": y, "주 수": len(m), "종목 수": n_live,
                         "모멘텀 로그": m.sum(), "등가중 로그": e.sum(), "초과 로그": m.sum() - e.sum()})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 200)
    print(df.round(4).to_string(index=False))
    for name, g in df.groupby("유니버스", sort=False):
        print(f"{name}: 초과 양수 {int((g['초과 로그'] > 0).sum())}/{len(g)}년, "
              f"2021~24 초과 양수 {int((g[g['연도'] <= 2024]['초과 로그'] > 0).sum())}/{int((g['연도'] <= 2024).sum())}년")


if __name__ == "__main__":
    main()
