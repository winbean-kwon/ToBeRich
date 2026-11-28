import pandas as pd, numpy as np, json, sys
true = json.loads(sys.argv[1])
df = pd.read_csv('/home/ksbda/f4work/mt/out_fix/data.csv', index_col=0)
r = df[(df.tic == 'AAPL') & (df.date == '2009-01-02')].iloc[0]
out = {'rows': len(df), 'aapl_2009_01_02': {k: float(r[k]) for k in ('open', 'high', 'low', 'close')}}
out['close_rel_diff_vs_true_adj'] = abs(r.close - true['Adj Close']) / true['Adj Close']
out['gate1_pass'] = bool(out['close_rel_diff_vs_true_adj'] < 1e-6)
viol_h = df.high < np.maximum(df.open, df.close)
viol_l = df.low > np.minimum(df.open, df.close)
out['viol_high'] = int(viol_h.sum()); out['viol_low'] = int(viol_l.sum()); out['viol_any'] = int((viol_h | viol_l).sum())
out['gate2_pass'] = out['viol_any'] == 0
# diagnostics (not gate): raw OHL consistency and ordering vs true raw values
out['diag_raw_ohl_viol'] = int(((df.high < df.open) | (df.low > df.open) | (df.high < df.low)).sum())
out['diag_aapl_open_high_low_reldiff_vs_raw'] = {k: abs(float(r[k]) - true[K]) / true[K] for k, K in (('open', 'Open'), ('high', 'High'), ('low', 'Low'))}
out['diag_close_lt_low'] = int((df.close < df.low).sum()); out['diag_close_gt_high'] = int((df.close > df.high).sum())
out['diag_zero_price_rows'] = int(((df.open == 0) | (df.close == 0)).sum())
out['diag_viol_by_tic'] = (viol_h | viol_l).groupby(df.tic).sum().astype(int).to_dict()
print(json.dumps(out, indent=1))
