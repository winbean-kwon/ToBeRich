# 개정 관문 2 (notes/margintrader_fix_prereg.md 수정 2026-11-28, 2c2cbc3)
import pandas as pd, json, sys, hashlib
P = '/home/ksbda/f4work/mt/out_fix/data.csv'
raw = {"Open": 3.067142963409424, "High": 3.2514290809631348, "Low": 3.041429042816162}  # 맥 yfinance 0.2.66, auto_adjust=False
df = pd.read_csv(P, index_col=0)
r = df[(df.tic == 'AAPL') & (df.date == '2009-01-02')].iloc[0]
rel = {k: abs(float(r[k.lower()]) - v) / v for k, v in raw.items()}
v = {'high_lt_open': int((df.high < df.open).sum()), 'low_gt_open': int((df.low > df.open).sum()), 'high_lt_low': int((df.high < df.low).sum())}
out = {'sha256': hashlib.sha256(open(P, 'rb').read()).hexdigest(), 'rows': len(df), 'aapl_rel_diff': rel, 'violations': v}
out['gate2_amended_pass'] = all(x < 1e-6 for x in rel.values()) and sum(v.values()) == 0
print(json.dumps(out, indent=1))
