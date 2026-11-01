# 공개 코드 감사 하네스 — notes/prereg_code_audit.md 2장 판정 계산(학습 없음, 합성 가격)
# 어댑터 규약: reset(c) 후 step(action) → dict(reward, value, w_exec, y)
#   w_exec: 이번 스텝에 실제로 수익을 받는 가중치(현금 칸 포함 시 0번), y: 그 가중치에 적용된 가격 상대비
import numpy as np

EPS_DIFF = 1e-12


def synth_prices(n_assets, T, seed=0, sigma=0.02):
    """로그정규 일간 가격 상대비 (T, n_assets)."""
    rng = np.random.default_rng(seed)
    return np.exp(rng.normal(0.0, sigma, size=(T, n_assets)))


def run_actions(make_env, c, actions):
    env = make_env(c)
    out = [env.step(a) for a in actions]
    return {k: np.array([o[k] for o in out]) for k in ('reward', 'value', 'w_exec', 'y')}


def c1(make_env, c_test, actions):
    """C1 설정 반영: 보상열·가치열이 c=0과 다른가."""
    a, b = run_actions(make_env, 0.0, actions), run_actions(make_env, c_test, actions)
    r_diff = np.max(np.abs(a['reward'] - b['reward'])) > EPS_DIFF
    v_diff = np.max(np.abs(a['value'] - b['value'])) > EPS_DIFF
    if r_diff and v_diff:
        v = '통과'
    elif not r_diff and not v_diff:
        v = '부과 안 됨'
    else:
        v = '부분 부과(' + ('보상만' if r_diff else '가치만') + ')'
    return {'verdict': v, 'reward_differs': bool(r_diff), 'value_differs': bool(v_diff)}


def s1(make_env, c_test, actions, has_cash):
    """S1 크기·시점: 측정 비용 ÷ 양방향 c·τ(현금 제외)."""
    a, b = run_actions(make_env, 0.0, actions), run_actions(make_env, c_test, actions)
    g0 = a['value'][1:] / a['value'][:-1]
    gc = b['value'][1:] / b['value'][:-1]
    meas = np.concatenate([[1 - b['value'][0] / a['value'][0]], 1 - gc / g0])
    w, y = b['w_exec'], b['y']
    ref = np.zeros(len(w))
    prev = None
    for t in range(len(w)):
        cur = w[t][1:] if has_cash else w[t]
        if prev is None:
            prev_d = np.zeros_like(cur) if has_cash else np.full_like(cur, 1 / len(cur))
        ref[t] = c_test * np.abs(cur - prev_d).sum()
        full = w[t] * y[t]
        full = full / full.sum()
        prev_d = full[1:] if has_cash else full
        prev = cur
    if np.max(np.abs(meas)) < EPS_DIFF:
        return {'ratio': 0.0, 'timing': '미반영', 'verdict': '미반영', 'meas': meas.tolist(), 'ref': ref.tolist()}
    e0 = np.abs(meas - ref).sum()
    e1 = np.abs(meas[1:] - ref[:-1]).sum()
    lag = 0 if e0 <= e1 else 1
    mref = ref[:len(ref) - lag]
    mm = meas[lag:]
    sel = mref > 0.05 * c_test
    ratio = float(np.median(mm[sel] / mref[sel])) if sel.any() else float('nan')
    timing = '일치' if lag == 0 else '1스텝 지연'
    if 0.9 <= ratio <= 1.1:
        v = '정상'
    elif abs(ratio - 0.5) <= 0.02 or abs(ratio - 2) <= 0.04:
        v = '관례 차이'
    else:
        v = '과소' if ratio < 0.9 else '과다'
    return {'ratio': ratio, 'timing': timing, 'verdict': v, 'meas': meas.tolist(), 'ref': ref.tolist()}


def cost_defect(cost_status, c1r, s1r):
    """2.1 비용 결함: '명시 비용' 대상에서만 판정."""
    if cost_status != '명시 비용':
        return None
    if c1r['verdict'] != '통과':
        return True
    if s1r['timing'] == '미반영':
        return True
    r = s1r['ratio']
    return bool(s1r['verdict'] != '관례 차이' and not (0.5 <= r <= 2))


def p1_dynamic(weights_from_action, low, high, n):
    """P1 동적: 경계 안 극단 행동의 w_max, 경계 밖 행동(±5)을 env가 자르는지."""
    a = np.full(n, low, float); a[0] = high
    w_in = np.asarray(weights_from_action(a))
    b = np.full(n, -5.0); b[0] = 5.0
    w_out = np.asarray(weights_from_action(b))
    return {'w_max_in_bounds': float(w_in.max()),
            'ratio_in_bounds': float(w_in.max() / w_in.min()) if w_in.min() > 0 else float('inf'),
            'w_max_out_of_bounds': float(w_out.max()),
            'env_clips': bool(np.allclose(w_in, w_out))}


def standard_actions(n, has_cash, n_hold=3, eps=1e-6):
    """S1 행동열(목표 가중치): 등가중 → 1종목 집중 → 다른 1종목 집중 → 유지."""
    k = n + (1 if has_cash else 0)
    off = 1 if has_cash else 0
    ew = np.full(k, eps); ew[off:] = 1 / n; ew = ew / ew.sum()
    def conc(i):
        w = np.full(k, eps); w[off + i] = 1.0; return w / w.sum()
    return [ew, conc(0), conc(1)] + [conc(1)] * n_hold
