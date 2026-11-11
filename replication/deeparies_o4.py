# T1 DeepAries O4 — notes/deeparies_o4_prereg.md 3장 그대로. 새 학습 없음, O1·E 기록만 사용.
# 사용: python3 replication/deeparies_o4.py → replication/deeparies/o4.json
import sys, json, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deeparies_run as da
from finrl_t3_run import u1_returns, ann_log

px = da.daily_panel('W0')
out = {}
for cond, folder in (('a', HERE / 'deeparies' / 'runs'), ('e1', HERE / 'deeparies' / 'e10'), ('e10', HERE / 'deeparies' / 'e10')):
    da.RUNS = folder
    rows = {}
    for s in range(10):
        df, meta = da.load_run('W0', cond, s)
        W, R, err, h = da.expand(df, px)
        net, taus = u1_returns(W, R, 0.0001)
        net3, _ = u1_returns(W, R, 0.001)
        N = len(net)
        orig = 252 / N * np.log(df.pv.iloc[-1])
        rows[s] = {'O4_%p': round((orig - ann_log(net)) * 100, 4),
                   'orig_ann_log_%': round(orig * 100, 3), 'u1_0.0001_ann_log_%': round(ann_log(net) * 100, 3),
                   'turnover_mean': round(float(taus[2:][taus[2:] > 0].mean()) if (taus[2:] > 0).any() else 0.0, 4),
                   'expand_err': float(err),
                   '탐색적_U1_c0.0001−c0.001_%p': round((ann_log(net) - ann_log(net3)) * 100, 3)}
    v = [r['O4_%p'] for r in rows.values()]
    out[cond] = {'seeds': rows, 'O4_median': round(float(np.median(v)), 4), 'O4_min': min(v), 'O4_max': max(v),
                 'expand_err_max': max(r['expand_err'] for r in rows.values())}
(HERE / 'deeparies' / 'o4.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
for c, r in out.items():
    print(c, {k: r[k] for k in ('O4_median', 'O4_min', 'O4_max', 'expand_err_max')},
          'turnover', [x['turnover_mean'] for x in r['seeds'].values()],
          '탐색적 c=0.001 비용', [x['탐색적_U1_c0.0001−c0.001_%p'] for x in r['seeds'].values()])
