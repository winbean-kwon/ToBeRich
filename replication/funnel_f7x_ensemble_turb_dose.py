# 사용: python3 funnel_f7x_ensemble_turb_dose.py <dow_30_2009_2020.csv·dow30_turbulence_index.csv 폴더> <출력 json>
# 데이터만으로 사이클별 난류 문턱(P: f02a762 하드코딩, T: ed22d27 규칙)과 거래 구간 문턱 이상 일수를 계산. 성과 없음.
import sys, json, numpy as np, pandas as pd
D = sys.argv[1]
df = pd.read_csv(f'{D}/dow_30_2009_2020.csv'); df = df[df.datadate >= 20090000]
d = df[['datadate','tic','prccd','ajexdi']].copy(); d['ajexdi'] = d['ajexdi'].apply(lambda x: 1 if x == 0 else x)
d['adjcp'] = d['prccd'] / d['ajexdi']
# 저자 calcualte_turbulence 그대로(벡터화 없이 같은 식)
piv = d.pivot(index='datadate', columns='tic', values='adjcp'); ud = d.datadate.unique()
ti = [0]*252; cnt = 0
for i in range(252, len(ud)):
    cur = piv[piv.index == ud[i]]; hist = piv[[n in ud[0:i] for n in piv.index]]
    t = (cur - np.mean(hist, axis=0)).values.dot(np.linalg.inv(hist.cov())).dot((cur - np.mean(hist, axis=0)).values.T)
    if t > 0:
        cnt += 1; ti.append(t[0][0] if cnt > 2 else 0)
    else: ti.append(0)
tb = pd.DataFrame({'datadate': piv.index, 'turbulence': ti})
bundle = pd.read_csv(f'{D}/dow30_turbulence_index.csv')
m = tb.merge(bundle, on='datadate', suffixes=('', '_b'))
print('vs bundle max abs diff', float((m.turbulence - m.turbulence_b).abs().max()), len(m), len(tb))
dfx = d.merge(tb, on='datadate').sort_values(['datadate','tic']).reset_index(drop=True)
udt = dfx[(dfx.datadate > 20151001) & (dfx.datadate <= 20200707)].datadate.unique()
ins = dfx[(dfx.datadate < 20151000) & (dfx.datadate >= 20090000)].drop_duplicates(subset=['datadate'])
q90 = np.quantile(ins.turbulence.values, .90); q99 = np.quantile(ins.turbulence.values, .99); q100 = np.quantile(ins.turbulence.values, 1)
print('insample q90', q90, 'q99', q99)
rw = vw = 63; out = []; thrP = 140
for i in range(rw + vw, len(udt), rw):
    if (i >= 692) & (i < 1090): thrP = 100
    if i >= 1090: thrP = 90
    h = dfx[(dfx.datadate < udt[i-rw-vw]) & (dfx.datadate >= udt[i-rw-vw-63])].drop_duplicates(subset=['datadate'])
    hm = np.mean(h.turbulence.values) if len(h) else float('nan')
    thrT = q90 if hm > q90 else q99
    thrA6 = q90 if hm > q90 else q100  # 6fada35(분위수 1), T 선택 후 기술용으로 계산
    tr = dfx[(dfx.datadate >= udt[i-rw]) & (dfx.datadate < (udt[i] if i < len(udt) else 99999999))].drop_duplicates(subset=['datadate'])
    va = dfx[(dfx.datadate >= udt[i-rw-vw]) & (dfx.datadate < udt[i-rw])].drop_duplicates(subset=['datadate'])
    out.append({'iter': i, 'trade_start': int(udt[i-rw]), 'hist_n': int(len(h)), 'hist_mean': None if np.isnan(hm) else round(float(hm),2),
                'thrP': thrP, 'thrT': round(float(thrT),2), 'trade_days': int(len(tr)),
                'trade_ge_P': int((tr.turbulence >= thrP).sum()), 'trade_ge_T': int((tr.turbulence >= thrT).sum()),
                'val_ge_P': int((va.turbulence >= thrP).sum()), 'val_ge_T': int((va.turbulence >= thrT).sum()),
                'trade_ge_C140': int((tr.turbulence >= 140).sum()), 'val_ge_C140': int((va.turbulence >= 140).sum()),
                'thrA6': round(float(thrA6), 2), 'trade_ge_A6': int((tr.turbulence >= thrA6).sum()), 'val_ge_A6': int((va.turbulence >= thrA6).sum())})
for o in out: print(o)
tot = {k: sum(o[k] for o in out) for k in ('trade_days','trade_ge_P','trade_ge_T','val_ge_P','val_ge_T','trade_ge_C140','val_ge_C140','trade_ge_A6','val_ge_A6')}
print(tot)
json.dump({'q90': float(q90), 'q99': float(q99), 'q100': float(q100), 'cycles': out, 'total': tot}, open(sys.argv[2], 'w'), indent=1)
