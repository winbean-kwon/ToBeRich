# 목적 함수 수준 비용 감사 — 동적 점검, 서버 대상 4개(#1 PGPortfolio, #7 WaveCorr, #12 jackieli, #15 Margin Trader)
# 사전 등록 notes/objective_cost_audit_prereg.md 3.2·3.3, 정적 예측 3fcd18e. 기준은 run_dynamic.py와 같다.
# 실행(서버 WSL, 기존 환경만 사용, 설치·다운로드 없음):
#   ~/f4work/adrl/p37/bin/python run_dynamic_server.py pgp ~/f4work/eiie_inspect/repo  '#1 PGPortfolio'
#   ~/f4work/adrl/p37/bin/python run_dynamic_server.py pgp ~/f4work/objdyn/jackieli    '#12 jackieli PGPortfolio'
#   ~/f4work/wavecorr/p37/bin/python run_dynamic_server.py wavecorr ~/f4work/wavecorr/repo/src
#   ~/f4work/mt/py310/bin/python run_dynamic_server.py mt ~/f4work/mt/repo
#   각 명령은 '@@JSON@@{...}' 한 줄을 출력한다. 맥에서: python3 run_dynamic_server.py merge <json 파일들>
# 원칙: 대상 코드는 고치지 않는다(파일을 그대로 import). 비용 계수는 설정값(config dict, 생성자 인자)으로만 넣는다.
#   학습(optimizer step)은 하지 않는다. TF1 손실은 tf.gradients(loss, trainable_variables)를 고정 초기값·같은 feed로 계산한다.
#   TF 그래프는 float32(대상 코드의 placeholder 정밀도)다.
from __future__ import print_function
import copy, json, os, sys, time
import numpy as np

C_TEST = 0.01
L_HI, L_LO, R_EPS = 1e-3, 1e-4, 1e-12


def l_judge(g_c, g_0):
    rel = float(np.linalg.norm(g_c - g_0) / np.linalg.norm(g_0))
    return {'rel_grad_diff': rel, 'grad_norm_0': float(np.linalg.norm(g_0)), 'grad_norm_c': float(np.linalg.norm(g_c)),
            'cost_seen': True if rel > L_HI else (False if rel <= L_LO else None)}


def r_judge(r_c, r_0, turn, v_c=None, v_0=None):
    r_c, r_0, turn = [np.asarray(x, float) for x in (r_c, r_0, turn)]
    d = np.abs(r_c - r_0); sel = turn > 0
    md = float(d[sel].max()) if sel.any() else 0.0
    out = {'max_abs_dr_turnover_steps': md, 'reward_c': r_c.tolist(), 'reward_0': r_0.tolist(),
           'turnover': turn.tolist(), 'cost_seen': bool(md > R_EPS)}
    if v_c is not None:
        dv = float(np.max(np.abs(np.asarray(v_c, float) - np.asarray(v_0, float))))
        out['value_max_abs_diff'] = dv; out['value_charged'] = bool(dv > R_EPS)
    return out


def flat(gs, vs):
    return np.concatenate([(np.zeros(v.shape) if g is None else np.asarray(g, np.float64)).ravel() for g, v in zip(gs, vs)])


# ---------------------------------------------------------------- #1·#12 PGPortfolio (L, TF1)
def t_pgp(repo):
    sys.path.insert(0, repo)
    import tensorflow as tf, tflearn
    from pgportfolio.tools.configprocess import preprocess_config
    from pgportfolio.learn.nnagent import NNAgent
    cfg0 = preprocess_config(json.load(open(os.path.join(repo, 'pgportfolio', 'net_config.json'))))
    F, N, W, B = (cfg0['input']['feature_number'], cfg0['input']['coin_number'], cfg0['input']['window_size'],
                  cfg0['training']['batch_size'])
    # 합성 global data [F, N, T]: close 로그정규(고정 시드), high/low = close × exp(±|e|). 특성 순서 close, high, low(get_type_list)
    rs = np.random.RandomState(0); T = 50 + B + W + 2
    close = np.cumprod(np.exp(rs.normal(0.0, 0.02, size=(T, N))), axis=0)
    high = close * np.exp(np.abs(rs.normal(0, 0.005, size=(T, N))))
    low = close * np.exp(-np.abs(rs.normal(0, 0.005, size=(T, N))))
    G = np.stack([close, high, low])[:F].transpose(0, 2, 1)                       # (F, N, T)
    idx = np.arange(50, 50 + B)                                                     # 연속 배치(replay buffer next_experience_batch와 같은 형태)
    M = np.array([G[:, :, i:i + W + 1] for i in idx])                              # datamatrices.__pack_samples 그대로
    X = M[:, :, :, :-1]; y = M[:, :, :, -1] / M[:, 0, None, :, -2]
    last_w = np.full((B, N), 1.0 / N)                                               # PVM 초기값 fillna(1/coin_no)

    def run(c, init=None):
        tf.reset_default_graph()
        tf.set_random_seed(cfg0['random_seed']); np.random.seed(cfg0['random_seed'])   # tradertrainer 47·62행과 같은 시드
        cfg = copy.deepcopy(cfg0); cfg['trading']['trading_consumption'] = c
        agent = NNAgent(cfg, None, 'cpu')
        sess = agent.session
        tv = tf.trainable_variables()
        if init is not None:
            for v, val in zip(tv, init):
                v.load(val, sess)
        grads = tf.gradients(agent.loss, tv)
        tflearn.is_training(True, sess)                                             # NNAgent.train과 같은 학습 모드
        net = agent._NNAgent__net
        feed = {net.input_tensor: X, agent._NNAgent__y: y, net.previous_w: last_w, net.input_num: B}
        gv = [g for g in grads if g is not None]
        out = sess.run(gv + [agent.loss] + tv, feed)
        it = iter(out[:len(gv)]); g_full = [None if g is None else next(it) for g in grads]
        loss, vals = out[len(gv)], out[len(gv) + 1:]
        names = [v.name for v in tv]; dtypes = sorted(set(str(v.dtype.base_dtype.name) for v in tv))
        agent.recycle()
        return flat(g_full, vals), float(loss), vals, names, dtypes

    g0, l0, init, names, dt = run(0.0)
    gc, lc, init_c, _, _ = run(C_TEST, init)
    g0b, _, init_b, _, _ = run(0.0, init)
    init_same = max(float(np.max(np.abs(a - b))) for a, b in zip(init, init_b))
    res = l_judge(gc, g0)
    res.update({'repeat_c0_rel_diff': float(np.linalg.norm(g0b - g0) / np.linalg.norm(g0)),
                'init_max_abs_diff_between_runs': init_same, 'loss_c': lc, 'loss_0': l0,
                'precision': 'float32 그래프(placeholder·변수 ' + ','.join(dt) + '); 기울기 노름·차이는 float64로 집계',
                'n_params': int(g0.size), 'tf_version': tf.__version__,
                'setup': ('net_config.json 그대로(layers %s, loss %s, batch %d, window %d, coin %d, feature %d), '
                          'trading_consumption만 0.01/0으로 바꿈, tf.set_random_seed(random_seed=%d) 후 NNAgent 생성, '
                          '두 번째 그래프에 첫 그래프 초기값 load, tflearn.is_training(True), tf.gradients(loss, trainable_variables), '
                          '합성 가격 RandomState(0) σ=0.02, 연속 배치 %d, last_w = 1/coin(PVM 초기값)')
                         % ([l['type'] for l in cfg0['layers']], cfg0['training']['loss_function'], B, W, N, F,
                            cfg0['random_seed'], B)})
    return 'L', res


# ---------------------------------------------------------------- #7 WaveCorr (L, TF1.14)
def t_wavecorr(src):
    sys.path.insert(0, src)
    import tensorflow as tf
    from wavecorr_agent import agent_manager
    # wavecorr_run.py 기본값: can, 50종목, tradeFee 0.0005, lr 1e-4, decay 0.9999, min 1e-5, minibatch 1, epochs 3000,
    # lookback 32, horizon 32, seed 1111 → differentSeedExperiments 첫 실행 1112, depth 8, reg 1e-6, RNN True, keep 0.5
    T, N, TRAIN = 4220, 50, 2766
    rs = np.random.RandomState(0)
    y = np.exp(rs.normal(0.0, 0.02, size=(T, N)))                     # 가격 상대비(데이터의 y_close 역할)
    xr = np.vstack([np.zeros((1, N)), np.log(y[:-1])])[:, :, None]     # x_close 역할(직전 로그수익, 첫 행 0) — 합성
    x_min = np.min(xr, axis=1, keepdims=True); x_max = np.max(xr, axis=1, keepdims=True)
    x = (2 * np.divide((xr - x_min), (x_max - x_min) + 1e-8) - 1) / 10   # loadInput capped_norm 식 그대로
    LB = PH = 32

    def run(fee, keep_first=0.5):
        ag = agent_manager('can', x, y, 1e-4, 0.9999, 1e-5, 1, 3000, N, LB, PH, fee, 1112, constrain_action=False,
                           maxStockWeight=0.25, network_model='waveCorr', net_depth=8, regularizer_multiplier=1e-6,
                           RNN=True, keep_prob_value=0.5)
        tv = tf.compat.v1.trainable_variables()
        grads = tf.gradients(ag.loss, tv)
        with tf.compat.v1.Session() as sess:
            sess.run(ag.init_op); ag.initPvm(y)
            # train_test 첫 epoch의 순전파(do_backprop=False)로 PVM을 채운다(코드 그대로 호출)
            ag.reset()
            last_index = y.shape[0] - LB - PH
            ts = [1 + i * ag.minibatchCount for i in range(int(last_index / ag.minibatchCount) + 1)] + [last_index]
            ts = ts + [last_index] * (ag.minibatchSize - len(ts) % ag.minibatchSize)
            ts = np.reshape(np.array(ts), [-1, ag.minibatchSize])
            for t_ in range(ts.shape[0]):
                ag.trainOnMinibatch_PG(sess, ts[t_], x, y, do_backprop=False, is_train=False, trainSetLen=TRAIN)
            # 첫 역전파 배치: seed_counter=1, randint(1, trainSetLen − lookback − horizon, minibatch) — train_test 그대로
            np.random.seed(1)
            index = np.random.randint(1, TRAIN - LB - PH, ag.minibatchSize)
            wb = LB + PH - 1     # trainOnMinibatch_PG do_backprop=True 분기의 feed 구성 그대로
            mIn = np.array([x[index[i]:index[i] + wb, :, :] for i in range(len(index))])
            yy = np.array([y[index[i] + LB - 1:index[i] + wb, :] for i in range(len(index))])
            wIn = np.array([ag.pvm[index[i] - 1:index[i] + wb - 1] for i in range(len(index))])
            wPrime = ag.updateRateShift(wIn, np.array([y[index[i] - 1:index[i] + wb - 1] for i in range(len(index))]))
            gv = [g for g in grads if g is not None]
            outs = {}
            for kp in ([keep_first, 1.0] if keep_first != 1.0 else [1.0]):
                o = sess.run(gv + [ag.loss], {ag.mIn: mIn, ag.wIn: wPrime, ag.y: yy, ag.keep_prob: kp, ag.is_train: True})
                it = iter(o[:-1]); outs[kp] = (flat([None if g is None else next(it) for g in grads], tv), float(np.squeeze(o[-1])))
            vals = sess.run(tv)
            dt = sorted(set(str(v.dtype.base_dtype.name) for v in tv))
        return outs, vals, int(index[0]), dt

    o0, v0, i0, dt = run(0.0)
    oc, vc, ic, _ = run(C_TEST)
    o0b, v0b, _, _ = run(0.0)
    res = l_judge(oc[0.5][0], o0[0.5][0])
    res.update({'repeat_c0_rel_diff': float(np.linalg.norm(o0b[0.5][0] - o0[0.5][0]) / np.linalg.norm(o0[0.5][0])),
                'init_max_abs_diff_between_runs': max(float(np.max(np.abs(a - b))) for a, b in zip(v0, vc)),
                'keep_prob_1_rel_grad_diff': float(np.linalg.norm(oc[1.0][0] - o0[1.0][0]) / np.linalg.norm(o0[1.0][0])),
                'keep_prob_1_grad_norm_0': float(np.linalg.norm(o0[1.0][0])),
                'loss_c': oc[0.5][1], 'loss_0': o0[0.5][1], 'batch_index': i0, 'n_params': int(o0[0.5][0].size),
                'precision': 'float32 그래프(' + ','.join(dt) + '); 노름·차이는 float64로 집계', 'tf_version': tf.__version__,
                'setup': ('wavecorr_run.py 기본값(waveCorr, RNN=True, 50종목, lookback·horizon 32, minibatch 1, depth 8, '
                          'reg 1e-6, seed 1112=첫 실험), tradeFee만 0.01/0(생성자 인자), 첫 epoch 순전파로 PVM 채운 뒤 '
                          '첫 역전파 배치(np.random.seed(1))의 feed 그대로, keep_prob 0.5(학습값; 같은 그래프 시드라 드롭아웃 마스크 동일, '
                          'c=0 반복으로 확인), tf.gradients(loss, trainable_variables). 합성 가격 RandomState(0) σ=0.02, T=4220, '
                          'x = 직전 로그수익을 loadInput capped_norm 식으로 정규화(합성; 실제 x_close 정의는 미확인)')})
    return 'L', res


# ---------------------------------------------------------------- #15 Margin Trader (R)
def t_mt(repo):
    sys.path.insert(0, repo)
    import pandas as pd
    from env.marginEnv import MarginTradingEnv
    IND = ['macd', 'boll_ub', 'boll_lb', 'rsi_30', 'cci_30', 'dx_30', 'close_30_sma', 'close_60_sma']  # finrl.config.INDICATORS(서버 환경에서 확인)
    N, T, H = 28, 12, 100        # 6장 실행 로그 'Stock Dimension: 28', hmax 100, initial 1e6, 비용 0.001, penalty 0.05(argparse 기본)
    rs = np.random.RandomState(0)
    px = 100 * np.vstack([np.ones(N), np.cumprod(np.exp(rs.normal(0.0, 0.02, size=(T, N))), axis=0)])
    dates = pd.bdate_range('2020-01-01', periods=T + 1).strftime('%Y-%m-%d')
    rows = []
    for t in range(T + 1):
        for i in range(N):
            r = {'idx': t, 'date': dates[t], 'tic': 'S%02d' % i, 'close': px[t, i]}
            r.update({k: 0.0 for k in IND}); rows.append(r)
    df = pd.DataFrame(rows).set_index('idx'); df.index.name = None
    eq = np.full(N, 1.0 / N); a1 = np.zeros(N); a1[0] = 1; a2 = np.zeros(N); a2[1] = 1
    tg = [eq, a1, a2, a2]        # S1 행동열(롱만): 등가중 → 1종목 → 다른 1종목 → 유지

    def run(c):
        e = MarginTradingEnv(df=df, stock_dim=N, hmax=H, initial_amount=1000000, num_stock_shares=[0] * N,
                             buy_cost_pct=[c] * N, sell_cost_pct=[c] * N, reward_scaling=1e-4,
                             state_space=2 * 3 + 2 * N + len(IND) * N, action_space=2 * N, tech_indicator_list=IND,
                             penalty_sharpe=0.05)
        venv, _ = e.get_sb_env()              # 학습 스크립트와 같은 DummyVecEnv(A2C가 받는 보상)
        r_vec, r_env, v, tv = [], [], [], []
        for w in tg:
            s = e.state; p = np.array(s[6:6 + N]); h = np.array(s[6 + N:6 + 2 * N]); V = s[0] + p @ np.maximum(h, 0)
            a = np.r_[np.clip((w * V / p - h) / H, -1, 1), np.zeros(N)].astype(np.float32)
            _, rew, done, _ = venv.step(a[None])
            h2 = np.array(e.state[6 + N:6 + 2 * N]); tv.append(float(np.abs(h2 - h) @ p / V))
            r_vec.append(float(rew[0])); r_env.append(float(e.reward)); v.append(float(e.asset_memory[-1]))
        return r_vec, r_env, v, tv, str(np.asarray(rew).dtype)

    (rv_c, re_c, v_c, _, dtp), (rv_0, re_0, v_0, tv0, _) = run(C_TEST), run(0.0)
    res = r_judge(rv_c, rv_0, tv0, v_c, v_0)
    renv = r_judge(re_c, re_0, tv0)
    res.update({'env_reward_max_abs_dr': renv['max_abs_dr_turnover_steps'], 'env_reward_c': re_c, 'env_reward_0': re_0,
                'precision': 'DummyVecEnv 보상 ' + dtp + '(A2C가 받는 값), env 보상 float64',
                'setup': ('MarginTradingEnv @7b7fa9e 그대로 import, N=28, hmax 100, initial 1e6, reward_scaling 1e-4, '
                          'penalty_sharpe 0.05, 비용만 0.01/0, DummyVecEnv.step 보상 비교. 행동 = 롱 clip((목표 주식수 − 보유)/HMAX), '
                          '숏 0; HMAX 100 상한으로 집중은 일부만 체결; 회전율 = 실제 체결 금액/롱 가용 자본(c=0 실행)'),
                'eval_note': '평가(test·trade)도 같은 env 클래스(스크립트 139·191행) — 같은 가치 경로로 부과'})
    return 'R', res


# ---------------------------------------------------------------- 맥: results.json 병합
STATIC = {'#1 PGPortfolio': 'S', '#7 WaveCorr': 'S', '#12 jackieli PGPortfolio': 'S', '#15 Margin Trader': 'S'}
STATIC_EVAL = {k: True for k in STATIC}


def classify(res, name):
    seen = res.get('cost_seen')
    if seen is None:
        return 'X'
    if seen:
        return 'S'
    ev = res.get('value_charged', STATIC_EVAL[name])
    return 'B' if ev else 'N'


def merge(paths):
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, 'results.json')
    allres = json.load(open(p))
    for fp in paths:
        r = json.load(open(fp))
        nm = r.pop('name')
        allres[nm] = r
        print(nm, r['class'], r.get('measured', {}).get('rel_grad_diff', r.get('measured', {}).get('max_abs_dr_turnover_steps')))
    sw = [k for k in allres['_meta'].get('server_wait', []) if not any(n.startswith(k + ' ') for n in allres
                                                                      if allres[n].get('class') != '서버 대기')]
    allres['_meta']['server_wait'] = sw
    json.dump(allres, open(p, 'w'), ensure_ascii=False, indent=1, default=float)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'merge':
        merge(sys.argv[2:]); sys.exit(0)
    t0 = time.time()
    name = {'wavecorr': '#7 WaveCorr', 'mt': '#15 Margin Trader'}.get(cmd, sys.argv[3] if len(sys.argv) > 3 else '')
    try:
        kind, res = {'pgp': t_pgp, 'wavecorr': t_wavecorr, 'mt': t_mt}[cmd](sys.argv[2])
        out = {'type': kind, 'measured': res, 'class': classify(res, name)}
    except Exception as e:
        import traceback
        out = {'type': None, 'class': 'X', 'error': '%s: %s' % (type(e).__name__, e), 'trace': traceback.format_exc()[-1500:]}
    out['name'] = name
    out['static_prediction'] = STATIC.get(name)
    out['match'] = (out['class'] == out['static_prediction'])
    out['runtime_s'] = round(time.time() - t0, 1)
    print('@@JSON@@' + json.dumps(out, ensure_ascii=False, default=float))
