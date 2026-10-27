# O5 동적 점검(T1 DeepAries) — TradingEnvironment 원문을 그대로 실행, 스크립트 행동 주입
import ast, types, json, sys
import numpy as np, pandas as pd
src = open('exp_DeepAries.py').read()
tree = ast.parse(src)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'TradingEnvironment')
cls_src = ast.get_source_segment(src, cls)
try:
    import torch
except ImportError:
    torch = types.SimpleNamespace(Tensor=type('Tensor', (), {}))  # isinstance 검사용 자리표시(행동은 numpy로 넣음)
ns = {'np': np, 'torch': torch}; exec(cls_src, ns); TradingEnvironment = ns['TradingEnvironment']

d = pd.read_csv('dj30_head.csv').iloc[:-1]
px = d.pivot(index='date', columns='tic', values='close')
px = px.dropna()                       # 26종목 모두 있는 날만
R = (px.shift(-1) / px - 1).dropna().values   # d일 보유 → d+1 종가 (h=1)
tics = list(px.columns); N = len(tics); assert N == 26, N
c = 0.001
args = types.SimpleNamespace(seq_len=20, fee_rate=c, complex_fee=False, num_stocks=20, total_stocks=N)

def ew(idx):
    w = np.zeros(N); w[idx] = 1 / len(idx); return w

def run(actions):
    env = TradingEnvironment(args); env.reset()
    meas, ref = [], []
    w_prev_drift = np.zeros(N)         # 참조: 현금 시작
    for t, w in enumerate(actions):
        r = R[t]; V0 = env.portfolio_value
        env.step(w.copy(), r)
        V1 = env.portfolio_value
        gross = 1 + w @ r
        fee_frac = 1 - V1 / (V0 * gross)      # 코드가 실제로 뗀 비용 / V
        meas.append(fee_frac)
        ref.append(c * np.abs(w - w_prev_drift).sum())   # v2 2장 참조 명세
        w_prev_drift = w * (1 + r) / (w @ (1 + r))
    return np.array(meas), np.array(ref)

T = 50
top20 = list(range(20)); A = list(range(10)); B = list(range(10, 20))
scen = {'가_EW20_유지': [ew(top20)] * T, '나_AB_교대': [ew(A) if t % 2 == 0 else ew(B) for t in range(T)]}
out = {}
for k, acts in scen.items():
    m, r = run(acts)
    out[k] = {'ratio_all_steps': float(m.sum() / r.sum()), 'ratio_steps3plus': float(m[2:].sum() / r[2:].sum()),
              'meas_sum': float(m.sum()), 'ref_sum': float(r.sum())}
m, r = run(scen['가_EW20_유지'][:3])
out['다_현금시작_첫3스텝'] = {'meas_turnover': (m / c).round(4).tolist(), 'ref_turnover': (r / c).round(4).tolist()}
out['meta'] = {'dates': [str(px.index[0]), str(px.index[T])], 'N': N, 'c': c, 'tickers_top20': tics[:20]}
print(json.dumps(out, ensure_ascii=False, indent=1))
