# 대조군 점검 — 기대: 정상 env C1 통과·S1 1.00±0.01·비 상한 무한, 결함 env C1 부과 안 됨·비 상한 e²
import json, numpy as np
from harness import synth_prices, c1, s1, p1_dynamic, standard_actions
from controls import RefEnv, defect_env, LagEnv

N, c = 10, 0.001
Y = synth_prices(N, 40, seed=0)
acts = [np.log(w) for w in standard_actions(N, has_cash=True)]   # softmax env에는 logits = log w
res = {}
for name, mk, bounded in [('ref_ok', lambda cc: RefEnv(cc, Y), False), ('ref_defect', lambda cc: defect_env(cc, Y), True)]:
    a_use = acts if not bounded else [np.clip(a, -1, 1) for a in acts]
    r1, r2 = c1(mk, c, a_use), s1(mk, c, a_use, has_cash=True)
    env = mk(c)
    p = p1_dynamic(env.to_weights, -50.0, 50.0, N + 1)   # 두 env 모두 행동 공간 = 실수 전체(tanh는 env 내부)
    res[name] = {'C1': r1, 'S1': {k: v for k, v in r2.items() if k not in ('meas', 'ref')}, 'P1': p}
ok = (res['ref_ok']['C1']['verdict'] == '통과' and abs(res['ref_ok']['S1']['ratio'] - 1) <= 0.01
      and res['ref_ok']['S1']['timing'] == '일치' and res['ref_ok']['P1']['ratio_in_bounds'] > 1e30
      and res['ref_defect']['C1']['verdict'] == '부과 안 됨'
      and abs(res['ref_defect']['P1']['ratio_in_bounds'] - np.e ** 2) < 1e-6)
lag = s1(lambda cc: LagEnv(cc, Y), c, acts, has_cash=True)
res['ref_lag'] = {k: v for k, v in lag.items() if k not in ('meas', 'ref')}
ok = ok and lag['timing'] == '1스텝 지연' and abs(lag['ratio'] - 1) <= 0.01
res['controls_pass'] = bool(ok)
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open('controls_result.json', 'w'), ensure_ascii=False, indent=1)
