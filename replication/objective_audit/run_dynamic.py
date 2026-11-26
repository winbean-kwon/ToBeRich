# 목적 함수 수준 비용 감사 — 동적 점검(notes/objective_cost_audit_prereg.md 3.2·3.3, 정적 예측 3fcd18e 이후)
# 실행(맥): PYTHONPATH=.t3env/pylib python3 replication/objective_audit/run_dynamic.py [대상 키 ...]
#   대상마다 새 프로세스에서 실행한다(모듈 이름 충돌·.cuda 패치 격리). 결과: replication/objective_audit/results.json
# 원칙: 대상 코드는 고치지 않는다. AST로 클래스·함수만 꺼내거나 파일을 그대로 import하고, import 차단용 스텁만 둔다.
#   설정값(비용 계수, 결과 폴더)은 생성자 인자나 설정 모듈 속성으로 넣는다. 학습(optimizer step)은 하지 않는다.
# 판정(사전 등록 3.2, 고정): c_test = 0.01 대 0.
#   L: ‖g_c − g_0‖/‖g_0‖ > 1e-3 → 비용 반영, ≤ 1e-4 → 비용 무시, 사이 → X
#   R: 회전율 > 0인 스텝 중 |r_c − r_0| > 1e-12가 하나라도 → 비용 반영, 아니면 비용 무시
#   분류: 반영 → S, 무시 + 평가 경로 부과 → B, 무시 + 평가 미부과 → N
import ast, json, os, subprocess, sys, time, types
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SCR = os.environ.get('OA_SCRATCH', '/private/tmp/claude-501/-Users-seungbin-school-4-1-------/'
                     'e9f6f6e8-2d56-4c96-a326-738b6cf12ec5/scratchpad')
DL = os.path.join(SCR, 'dl')                 # 정적 단계에서 받은 고정 커밋 개별 파일
WORK = os.path.join(SCR, 'oa_work')          # 어댑터 임시 출력(그림·CSV·로그)
C_TEST = 0.01
L_HI, L_LO, R_EPS = 1e-3, 1e-4, 1e-12


# ---------------------------------------------------------------- 공통
def extract(path, name, ns):
    """모듈을 실행하지 않고 최상위 클래스·함수 정의 하나만 꺼낸다(데코레이터 제외)."""
    src = open(path, encoding='utf-8').read()
    node = next(n for n in ast.parse(src).body if getattr(n, 'name', None) == name)
    exec(compile(ast.get_source_segment(src, node), path, 'exec'), ns)
    return ns[name]


def synth_rel(T, n, seed=0, sigma=0.02):
    """로그정규 가격 상대비 (T, n), 고정 시드."""
    return np.exp(np.random.default_rng(seed).normal(0.0, sigma, size=(T, n)))


def s1_targets(n, cash, eq_n=None):
    """S1 행동열(목표 가중치): 등가중 → 1종목 집중 → 다른 1종목 집중 → 유지. cash=True면 0번이 현금."""
    k, off = n + (1 if cash else 0), (1 if cash else 0)
    eq = np.zeros(k); eq[off:off + (eq_n or n)] = 1.0 / (eq_n or n)
    a1 = np.zeros(k); a1[off] = 1.0
    a2 = np.zeros(k); a2[off + 1] = 1.0
    return [eq, a1, a2, a2]


def drift_turnover(targets, rel, cash):
    """참조 회전율: Σ|w_t − w'_{t−1}|(위험자산), w'는 직전 목표가 rel로 표류한 것. 시작은 전액 현금(또는 0)."""
    out, prev = [], None
    for t, w in enumerate(targets):
        risky = w[1:] if cash else w
        if prev is None:
            pd_ = np.zeros_like(risky)
        else:
            full = prev * (np.r_[1.0, rel[t - 1]] if cash else rel[t - 1]); full = full / full.sum()
            pd_ = full[1:] if cash else full
        out.append(float(np.abs(risky - pd_).sum())); prev = w
    return out


def r_judge(r_c, r_0, turn, v_c=None, v_0=None):
    r_c, r_0, turn = map(lambda x: np.asarray(x, float), (r_c, r_0, turn))
    d = np.abs(r_c - r_0)
    sel = turn > 0
    md = float(d[sel].max()) if sel.any() else 0.0
    out = {'max_abs_dr_turnover_steps': md, 'reward_c': r_c.tolist(), 'reward_0': r_0.tolist(),
           'turnover': turn.tolist(), 'cost_seen': bool(md > R_EPS)}
    if v_c is not None:
        dv = float(np.max(np.abs(np.asarray(v_c, float) - np.asarray(v_0, float))))
        out['value_max_abs_diff'] = dv; out['value_charged'] = bool(dv > R_EPS)
    return out


def l_judge(g_c, g_0):
    import torch
    rel = float(torch.norm(g_c - g_0) / torch.norm(g_0))
    return {'rel_grad_diff': rel, 'grad_norm_0': float(torch.norm(g_0)),
            'cost_seen': True if rel > L_HI else (False if rel <= L_LO else None)}


def flat_grads(params):
    import torch
    return torch.cat([(p.grad if p.grad is not None else torch.zeros_like(p)).detach().flatten().clone()
                      for p in params])


# ---------------------------------------------------------------- #2 FinRL POE (L)
def t2_finrl_poe():
    import shutil, importlib, torch
    pkg = os.path.join(WORK, 'pkgs', 'finrl_poe'); os.makedirs(pkg, exist_ok=True)
    for src, dst in [('finrl/algorithms.py', 'algorithms.py'), ('finrl2/architectures.py', 'architectures.py'),
                     ('finrl/utils.py', 'utils.py')]:
        shutil.copyfile(os.path.join(DL, src), os.path.join(pkg, dst))   # 그대로 복사(패키지 상대 import용)
    open(os.path.join(pkg, '__init__.py'), 'w').close()
    sys.path.insert(0, os.path.dirname(pkg))
    # quantstats는 맥 환경에서 import 실패(tabulate 없음) → 종료 스텝 출력용 스텁(학습 신호와 무관)
    qs = types.ModuleType('quantstats')
    qs.stats = types.SimpleNamespace(max_drawdown=lambda *a, **k: 0.0, sharpe=lambda *a, **k: 0.0)
    qs.plots = types.SimpleNamespace(snapshot=lambda *a, **k: None)
    sys.modules['quantstats'] = qs
    spec = importlib.util.spec_from_file_location('finrl_poe_env', os.path.join(DL, 'finrl/env_portfolio_optimization.py'))
    envmod = importlib.util.module_from_spec(spec); spec.loader.exec_module(envmod)
    alg = importlib.import_module('finrl_poe.algorithms'); arch = importlib.import_module('finrl_poe.architectures')
    import pandas as pd
    N, TW, T = 10, 50, 50 + 40          # 자산 수: 저장소 기본 설정에 없음(튜토리얼 의존) → 10. time_window = EIIE 기본 50
    rel = synth_rel(T, N, seed=0)
    px = 100 * np.cumprod(rel, axis=0)
    dates = pd.bdate_range('2020-01-01', periods=T).strftime('%Y-%m-%d')
    rows = [{'date': dates[t], 'tic': f'S{i:02d}', 'close': px[t, i], 'high': px[t, i] * 1.01, 'low': px[t, i] * 0.99}
            for t in range(T) for i in range(N)]
    df = pd.DataFrame(rows)

    class NoStep(torch.optim.AdamW):            # 기울기만 보존: step을 하지 않는다(학습 없음)
        def step(self, closure=None):
            self.snap = flat_grads([p for g in self.param_groups for p in g['params']])
            self.snaps = getattr(self, 'snaps', []) + [self.snap]

    def run(c, model='trf', dfx=None, full=False):
        torch.manual_seed(0); np.random.seed(0)
        env = envmod.PortfolioOptimizationEnv((df if dfx is None else dfx).copy(), initial_amount=100000, comission_fee_model=model,
                                              comission_fee_pct=c, time_window=TW, features=['close', 'high', 'low'],
                                              cwd=os.path.join(WORK, 'finrl_poe'))
        pg = alg.PolicyGradient(env, policy=arch.EIIE, policy_kwargs={'time_window': TW}, batch_size=100,
                                optimizer=NoStep)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            pg.train(episodes=1)
        if full:
            return pg.train_optimizer.snaps, env._asset_memory['final']
        return pg.train_optimizer.snap, env._asset_memory['final']

    g_c, v_c = run(C_TEST); g_0, v_0 = run(0.0)
    res = l_judge(g_c, g_0)
    res['repeat_c0_rel_diff'] = l_judge(run(0.0)[0], g_0)['rel_grad_diff']
    res['eval_value_max_abs_diff'] = float(np.max(np.abs(np.array(v_c) - np.array(v_0))))
    res['eval_charged'] = bool(res['eval_value_max_abs_diff'] > R_EPS)
    try:
        run(C_TEST, model='wvm'); res['wvm_train'] = 'ran (no error)'
    except KeyError as e:
        res['wvm_train'] = f'KeyError {e!r} (algorithms.py 123행 info["trf_mu"])'
    except Exception as e:
        res['wvm_train'] = f'{type(e).__name__}: {e}'
    # 탐색적(판정 밖, 1차 결과가 사이 값이라 원인 확인용): (a) 에피소드를 늘려 기본 batch 100이 꽉 찬 첫 갱신의 기울기,
    # (b) 같은 손실을 float64로 다시 계산(정책 출력·버퍼 값은 같은 것 사용) — trf_mu가 표본당 상수배라면 차이는 0이어야 한다
    T2 = TW + 120
    rel2 = synth_rel(T2, N, seed=0); px2 = 100 * np.cumprod(rel2, axis=0)
    d2 = pd.bdate_range('2020-01-01', periods=T2).strftime('%Y-%m-%d')
    df2 = pd.DataFrame([{'date': d2[t], 'tic': f'S{i:02d}', 'close': px2[t, i], 'high': px2[t, i] * 1.01,
                         'low': px2[t, i] * 0.99} for t in range(T2) for i in range(N)])
    a_c, _ = run(C_TEST, dfx=df2, full=True); a_0, _ = run(0.0, dfx=df2, full=True)
    ex = {'full_batch100_rel_grad_diff': l_judge(a_c[0], a_0[0])['rel_grad_diff'],
          'full_batch100_grad_norm_0': float(torch.norm(a_0[0]))}
    # (b) float64 재계산: 정책 매개변수를 double로 복제해 손실식(algorithms.py 241–248행)을 그대로 적용
    torch.manual_seed(0)
    pol = arch.EIIE(time_window=TW)
    obs = torch.tensor(np.random.default_rng(5).normal(1, 0.01, (64, 3, N, TW)))
    la = torch.softmax(torch.tensor(np.random.default_rng(6).normal(size=(64, N + 1))), dim=1)
    pv = torch.tensor(np.r_[np.ones((64, 1)).T, np.exp(np.random.default_rng(7).normal(0, .02, (N, 64)))].T)
    tm = torch.tensor(1 - C_TEST * np.random.default_rng(8).uniform(0, 2, (64, 1)))
    def g64(trf):
        q = copy.deepcopy(pol).double(); q.zero_grad()
        x = q.sequential(obs); ls, cb = q._process_last_action(la); cb = torch.zeros_like(cb)
        o = q.final_convolution(torch.cat([ls, x], dim=1)); o = torch.cat([cb, o], dim=2).squeeze(3).squeeze(1)
        mu = torch.softmax(o, dim=-1)                           # EIIE.mu와 같은 연산(.float() 캐스팅만 생략)
        (-torch.mean(torch.log(torch.sum(mu * pv * trf, dim=1)))).backward()
        return flat_grads(list(q.parameters()))
    import copy
    ex['float64_rel_grad_diff'] = l_judge(g64(tm), g64(torch.ones_like(tm)))['rel_grad_diff']
    ex['note'] = '탐색적, 판정에 넣지 않음(사전 등록 판정은 위 rel_grad_diff 그대로)'
    res['exploratory'] = ex
    res['setup'] = f'N={N}, time_window={TW}, 에피소드 {T - TW + 1}스텝, batch_size 100(기본) → 에피소드 끝 _gradient_ascent 1회의 기울기'
    return 'L', res


# ---------------------------------------------------------------- #3 FinRL SPE (R)
def t3_finrl_spe():
    import gym, pandas as pd, matplotlib
    matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from gym import spaces
    from gym.utils import seeding
    from pathlib import Path
    ns = {'np': np, 'pd': pd, 'gym': gym, 'spaces': spaces, 'seeding': seeding, 'plt': plt, 'Path': Path,
          'DummyVecEnv': None, 'matplotlib': matplotlib}
    SPE = extract(os.path.join(ROOT, '.t3env/fm/meta/env_portfolio_allocation/env_portfolio_yahoofinance.py'),
                  'StockPortfolioEnv', ns)
    N, T = 30, 12
    rel = synth_rel(T, N, seed=0); px = 100 * np.vstack([np.ones(N), np.cumprod(rel, axis=0)])
    days = pd.bdate_range('2020-01-01', periods=T + 1).strftime('%Y-%m-%d')
    rows = [{'time': days[t], 'tic': f'S{i:02d}', 'close': px[t, i], 'cov_list': np.eye(N) * 1e-4, 'macd': 0.0}
            for t in range(T + 1) for i in range(N)]
    df = pd.DataFrame(rows)
    tg = s1_targets(N, cash=False); eps = 1e-6
    turn = drift_turnover(tg, px[1:] / px[:-1], cash=False)

    def run(c):
        e = SPE(df=df.copy(), stock_dim=N, hmax=100, initial_amount=1000000, transaction_cost_pct=c,
                reward_scaling=1e-4, state_space=N, action_space=N, tech_indicator_list=['macd'],
                cwd=os.path.join(WORK, 'spe'))
        e.reset(); r, v = [], []
        for w in tg:
            ww = (w + eps) / (w + eps).sum()
            _, rew, *_ = e.step(np.log(ww))          # softmax(log w) = w (T3 O5와 같은 주입)
            r.append(rew); v.append(e.portfolio_value)
        return r, v
    (r_c, v_c), (r_0, v_0) = run(C_TEST), run(0.0)
    res = r_judge(r_c, r_0, turn, v_c, v_0)
    res['setup'] = f'N={N}, 학습 보상 = step 반환값(new_portfolio_value, reward_scaling 주석 처리)'
    return 'R', res


# ---------------------------------------------------------------- #4 RAT (L)
def t4_rat():
    import torch, torch.nn as nn, torch.nn.functional as F, math, copy
    from torch.autograd import Variable
    torch.Tensor.cuda = lambda self, *a, **k: self          # 장치만 CPU로(계산 불변)
    nn.Module.cuda = lambda self, *a, **k: self
    P = os.path.join(ROOT, '.audit/rat/main.py')
    ns = {'torch': torch, 'nn': nn, 'F': F, 'math': math, 'copy': copy, 'np': np, 'Variable': Variable, 'time': time}
    for nm in ['EncoderDecoder', 'clones', 'LayerNorm', 'Encoder', 'SublayerConnection', 'EncoderLayer', 'Decoder',
               'DecoderLayer', 'subsequent_mask', 'attention', 'MultiHeadedAttention', 'PositionwiseFeedForward',
               'PositionalEncoding', 'make_model', 'Batch_Loss', 'SimpleLossCompute', 'make_std_mask', 'train_one_step']:
        extract(P, nm, ns)
    # 기본값(main.py 36–50행, run_main.sh): batch 128, coin 11, window 31, feature 4, multihead 2, model_dim 12, lcl 5
    B, C, W, Fn, MH, MD, LCL = 128, 11, 31, 4, 2, 12, 5
    interest = 0.001 / 24 / 2
    rel = synth_rel(B + W + 2, C, seed=0)
    close = 100 * np.cumprod(rel, axis=0)
    feats = np.stack([close, close * 1.01, close * 0.99, np.roll(close, 1, axis=0)], axis=0)   # (4, T, C)
    X = np.stack([feats[:, s:s + W, :].transpose(0, 2, 1) for s in range(B)])                  # (B, 4, C, W)
    y = np.stack([feats[:, s + W, :] / feats[0, s + W - 1, :][None, :] for s in range(B)])     # (B, 4, C) 다음 시점 / 현재 종가
    last_w = np.full((B, C), 1.0 / C)

    class DM:
        def next_batch(self):
            return {'X': X.copy(), 'y': y.copy(), 'last_w': last_w.copy(), 'setw': lambda w: None}

    def run(c):
        torch.manual_seed(0)
        model = ns['make_model'](B, C, W, Fn, N=1, d_model_Encoder=MH * MD, d_model_Decoder=MH * MD,
                                 d_ff_Encoder=MH * MD, d_ff_Decoder=MH * MD, h=MH, dropout=0.01, local_context_length=LCL)
        torch.manual_seed(1)                                     # 드롭아웃 마스크를 두 실행에서 같게
        lc = ns['SimpleLossCompute'](ns['Batch_Loss'](c, interest, 0.0, 0.0, True), None)   # opt=None → backward는 여기서
        loss, _ = ns['train_one_step'](DM(), W, model, lc, LCL)
        model.zero_grad(); loss.backward()
        return flat_grads(list(model.parameters()))
    g0 = run(0.0)
    res = l_judge(run(C_TEST), g0)
    res['repeat_c0_rel_diff'] = l_judge(run(0.0), g0)['rel_grad_diff']   # 같은 c 반복 실행 차이(결정성 확인)
    res['eval_charged'] = True
    res['eval_note'] = 'Test_Loss 1095–1104행 같은 식으로 부과(이전 감사 C1 통과, 이번에 재실행 안 함)'
    res['setup'] = 'train_one_step·Batch_Loss·make_model 그대로(AST 추출), 합성 배치 128, 학습 손실 1437행 구성'
    return 'L', res


# ---------------------------------------------------------------- #5 Ensemble (R)
def t5_ensemble():
    import pandas as pd
    P = os.path.join(DL, 'ensenv/EnvMultipleStock_train.py')   # @f02a762, sha256 540146a5…(F4 기록과 일치)
    N, T, H = 30, 12, 100
    rel = synth_rel(T, N, seed=0); px = 1000 * np.vstack([np.ones(N), np.cumprod(rel, axis=0)])
    rows = []
    for t in range(T + 1):
        for i in range(N):
            rows.append({'datadate': t, 'tic': f'S{i:02d}', 'adjcp': px[t, i], 'macd': 0.0, 'rsi': 50.0, 'cci': 0.0, 'adx': 20.0})
    df = pd.DataFrame(rows); df.index = df.datadate
    tg = s1_targets(N, cash=True)
    cwd = os.getcwd(); os.makedirs(os.path.join(WORK, 'ens', 'results'), exist_ok=True); os.chdir(os.path.join(WORK, 'ens'))

    def run(c):
        ns = {'__name__': 'ens_env'}
        exec(compile(open(P).read(), P, 'exec'), ns)
        ns['TRANSACTION_FEE_PERCENT'] = c                       # 모듈 상수 = 비용 설정(코드 수정 아님)
        e = ns['StockEnvTrain'](df); e.reset()
        r, v, tv = [], [], []
        for w in tg:
            s = e.state; cashv = s[0]; p = np.array(s[1:N + 1]); h = np.array(s[N + 1:2 * N + 1])
            V = cashv + (p * h).sum()
            tgt = w[1:] * V / p
            a = np.clip((tgt - h) / H, -1, 1)
            _, rew, _, _ = e.step(a)
            h2 = np.array(e.state[N + 1:2 * N + 1])
            tv.append(float(np.abs(h2 - h) @ p / V))
            r.append(rew); v.append(e.asset_memory[-1])
        return r, v, tv
    try:
        (r_c, v_c, _), (r_0, v_0, tv0) = run(C_TEST), run(0.0)
    finally:
        os.chdir(cwd)
    res = r_judge(r_c, r_0, tv0, v_c, v_0)
    res['setup'] = f'N={N}, 행동 = clip((목표 주식수 − 보유)/HMAX), HMAX 100 상한 때문에 집중은 일부만 실행; 회전율 = 실제 체결 금액/가치(c=0 실행)'
    res['eval_note'] = '평가 env(_trade·_validation)는 맥에 없어 실행 안 함; 학습 env 가치 차이만 측정'
    return 'R', res


# ---------------------------------------------------------------- #6 DeepTrader (L, 혼합)
def t6_deeptrader():
    import torch
    # 버전 호환 심(유일한 비-import 심): 저장소 ASU.py는 nn.Conv1d에 kernel_size=(1, k)와 4차원 입력을 쓴다.
    # 옛 PyTorch(1.x)는 이를 일반 합성곱으로 처리했고(길이 1 인자는 차원 수만큼 확장), torch 2.6은 거부한다.
    # 4차원 입력일 때만 같은 가중치로 F.conv2d를 부른다(길이 1 stride·padding·dilation을 2로 확장) — 옛 동작과 같은 계산.
    import torch.nn as nn, torch.nn.functional as F
    _orig = nn.Conv1d._conv_forward

    def _conv_forward(self, input, weight, bias):
        if input.dim() == 4 and weight.dim() == 4:
            ex = lambda t: tuple(t) * 2 if len(tuple(t)) == 1 else tuple(t)
            return F.conv2d(input, weight, bias, ex(self.stride), ex(self.padding), ex(self.dilation), self.groups)
        return _orig(self, input, weight, bias)
    nn.Conv1d._conv_forward = _conv_forward
    src = os.path.join(ROOT, '.audit/deeptrader/src'); sys.path.insert(0, src)
    import importlib
    agent = importlib.import_module('agent'); penv = importlib.import_module('environment.portfolio_env')
    hy = json.load(open(os.path.join(src, 'hyper.json')))
    args = types.SimpleNamespace(**hy); args.device = 'cpu'; args.msu_bool = True; args.spatial_bool = True
    args.addaptiveadj = True
    N, T, VAL = hy['num_assets'], 1200, 900
    rel = synth_rel(T, N, seed=0); close = 100 * np.cumprod(rel, axis=0)
    rng = np.random.default_rng(3)
    assets = np.stack([close, close * 1.01, close * 0.99, rng.uniform(1, 2, (T, N)), close, close], axis=-1).transpose(1, 0, 2)
    ror = (rel - 1).T                                   # (N, T)
    mkt = rng.normal(0, 1, (T, 4))
    A = torch.from_numpy(np.load(os.path.join(src, 'data/DJIA/industry_classification.npy'))).float()

    def run(c, explore=False):
        torch.manual_seed(0); np.random.seed(0)
        if explore:   # 탐색적 변형(판정 밖): agent.py 129행 log 인자의 음수를 1e-8로 자른다(비용 경로가 없는 ASU 항)
            agent.torch = types.SimpleNamespace(**{k: getattr(torch, k) for k in dir(torch) if not k.startswith('__')})
            agent.torch.log = lambda x: torch.log(torch.clamp(x, min=1e-8))
        else:
            agent.torch = torch
        env = penv.PortfolioEnv(assets_data=assets, market_data=mkt, rtns_data=ror, in_features=args.in_features,
                                val_idx=VAL, test_idx=VAL, batch_size=args.batch_size, fee=c,
                                window_len=args.window_len, trade_len=args.trade_len, max_steps=args.max_steps,
                                mode='train', norm_type=args.norm_type, allow_short=True)   # DJIA 주 설정
        actor = agent.RLActor([A], args)
        ag = agent.RLAgent(env, actor, args)
        snap = {}
        def step(*a, **k):
            snap.update(g=flat_grads(list(actor.parameters())), asu=flat_grads(list(actor.asu.parameters())),
                        msu=flat_grads(list(actor.msu.parameters())))
        ag.optimizer.step = step
        torch.manual_seed(1); np.random.seed(1)
        _, _, mdd = ag.train_episode()
        return snap, mdd
    try:
        (s_c, mdd_c), (s_0, mdd_0) = run(C_TEST), run(0.0)
        res = l_judge(s_c['g'], s_0['g'])
        res['repeat_c0_rel_diff'] = l_judge(run(0.0)[0]['g'], s_0['g'])['rel_grad_diff']
        res['block_rel_asu'] = l_judge(s_c['asu'], s_0['asu'])['rel_grad_diff']
        res['block_rel_msu'] = l_judge(s_c['msu'], s_0['msu'])['rel_grad_diff']
        res['avg_mdd_c'] = float(mdd_c); res['avg_mdd_0'] = float(mdd_0)
    except AssertionError:
        res = {'rel_grad_diff': None, 'cost_seen': None,
               'primary_failure': 'train_episode 158행 assert not isnan(loss) 실패: 129행 log(Σ normed_ror·softmax(scores))의 인자가 '
                                  '음수가 되는 스텝이 있음(표준화 수익의 가중합은 부호가 정해지지 않음) → 원 손실로 기울기 계산 불가'}
        ex = {}
        (e_c, m_c), (e_0, m_0) = run(C_TEST, True), run(0.0, True)
        ex['rel_grad_diff'] = l_judge(e_c['g'], e_0['g'])['rel_grad_diff']
        ex['block_rel_asu'] = l_judge(e_c['asu'], e_0['asu'])['rel_grad_diff']
        ex['block_rel_msu'] = l_judge(e_c['msu'], e_0['msu'])['rel_grad_diff']
        ex['repeat_c0_rel_diff'] = l_judge(run(0.0, True)[0]['g'], e_0['g'])['rel_grad_diff']
        ex['avg_mdd_c'] = float(m_c); ex['avg_mdd_0'] = float(m_0)
        ex['note'] = '탐색적, 판정에 넣지 않음: ASU 항 log 인자를 1e-8 아래에서 자른 변형(코드 동작 변경)'
        res['exploratory_clamped_log'] = ex
    res['eval_charged'] = True
    res['eval_note'] = 'evaluation()은 같은 env의 total_value(비용 반영)로 지표 계산(이전 감사 C1 통과)'
    res['setup'] = 'RLActor·RLAgent.train_episode·PortfolioEnv 그대로, hyper.json 기본, allow_short=True, optimizer.step만 기울기 스냅샷으로 대체(클리핑 후 값)'
    return 'L', res


# ---------------------------------------------------------------- #8 TradeMaster (R)
def t8_trademaster():
    import pandas as pd, gym
    from gym import spaces
    from collections import OrderedDict

    def get_attr(args, key=None, default_value=None):        # trademaster.utils.get_attr와 같은 의미(import 차단 스텁)
        if isinstance(args, dict):
            return args[key] if key in args else default_value
        return getattr(args, key) if hasattr(args, key) else default_value
    ns = {'np': np, 'pd': pd, 'spaces': spaces, 'OrderedDict': OrderedDict, 'get_attr': get_attr,
          'print_metrics': lambda *a, **k: '', 'Environments': gym.Env}
    Env = extract(os.path.join(DL, 'tm/environment.py'), 'PortfolioManagementEnvironment', ns)
    N, T = 10, 12        # 기본 데이터(exchange) 자산 수는 로컬 데이터가 없어 미확인 → 10
    rel = synth_rel(T, N, seed=0); px = 100 * np.vstack([np.ones(N), np.cumprod(rel, axis=0)])
    tech = ['zopen', 'zclose']
    rows = [{'idx': t, 'date': f'2020-01-{t + 1:02d}', 'tic': f'S{i:02d}', 'close': px[t, i], 'zopen': 0.0, 'zclose': 0.0}
            for t in range(T + 1) for i in range(N)]
    os.makedirs(os.path.join(WORK, 'tm'), exist_ok=True)
    path = os.path.join(WORK, 'tm', 'train.csv')
    pd.DataFrame(rows).set_index('idx').to_csv(path)
    tg = s1_targets(N, cash=True); eps = 1e-6
    turn = drift_turnover(tg, px[1:] / px[:-1], cash=True)

    def run(c):
        e = Env({'dataset': {'train_path': path, 'initial_amount': 100000, 'transaction_cost_pct': c,
                             'tech_indicator_list': tech}, 'task': 'train'})
        e.reset(); r, v = [], []
        for w in tg:
            ww = (w + eps) / (w + eps).sum()
            _, rew, _, _ = e.step(np.log(ww)); r.append(rew); v.append(e.portfolio_value)
        return r, v
    (r_c, v_c), (r_0, v_0) = run(C_TEST), run(0.0)
    res = r_judge(r_c, r_0, turn, v_c, v_0)
    res['setup'] = f'N={N}(가정), PortfolioManagementEnvironment(기본 env) AST 추출, 행동 = log w(env softmax)'
    return 'R', res


# ---------------------------------------------------------------- #9 AlphaMix+ (R)
def t9_alphamix():
    import pandas as pd, gym
    from gym import spaces
    from gym.utils import seeding
    ns = {'np': np, 'pd': pd, 'gym': gym, 'spaces': spaces, 'seeding': seeding}
    Env = extract(os.path.join(DL, 'am/portfolio_management.py'), 'TrainEnv', ns)
    N, T = 50, 12        # sz50(이름 기준 50, 정제 후 실제 수는 미확인)
    rel = synth_rel(T, N, seed=0); px = 100 * np.vstack([np.ones(N), np.cumprod(rel, axis=0)])
    rows = [{'idx': t, 'date': f'2020-01-{t + 1:02d}', 'tic': f'S{i:02d}', 'close': px[t, i], 'zclose': 0.0}
            for t in range(T + 1) for i in range(N)]
    df = pd.DataFrame(rows).set_index('idx'); df.index.name = None
    tg = s1_targets(N, cash=True); eps = 1e-6
    turn = drift_turnover(tg, px[1:] / px[:-1], cash=True)

    def run(c):
        e = Env({'df': df, 'stock_dim': N, 'hmax': 100, 'initial_amount': 1000000, 'transaction_cost_pct': c,
                 'reward_scaling': 1e-4, 'state_space': N, 'action_space': N, 'tech_indicator_list': ['zclose']})
        e.reset(); r, v = [], []
        for w in tg:
            ww = (w + eps) / (w + eps).sum()
            _, rew, _, _ = e.step(np.log(ww)[None, :])   # 107행 weights[:, 1:] → 2차원 행동
            r.append(rew); v.append(e.portfolio_value)
        return r, v
    (r_c, v_c), (r_0, v_0) = run(C_TEST), run(0.0)
    res = r_judge(r_c, r_0, turn, v_c, v_0)
    res['setup'] = f'N={N}, TrainEnv AST 추출, reward_scaling 1e-4(값은 판정과 무관)'
    return 'R', res


# ---------------------------------------------------------------- #10 EarnMore (R)
def t10_earnmore():
    import pandas as pd, gym, random
    from typing import List, Any
    from sklearn.preprocessing import StandardScaler
    ns = {'np': np, 'List': List, 'Any': Any, 'StandardScaler': StandardScaler, 'random': random, 'gym': gym}
    Env = extract(os.path.join(ROOT, '.t4env/EarnMore/pm/environment/pm_based_portfolio_value.py'), 'EnvironmentPV', ns)
    N, T, DAYS = 28, 60, 10                      # configs/mask_sac_portfolio_management.py 5·26행
    rel = synth_rel(T, N, seed=0); px = 100 * np.cumprod(rel, axis=0)
    idx = pd.bdate_range('2020-01-01', periods=T)
    feats, temps, labels = ['f1', 'f2'], ['weekday', 'day', 'month'], ['ret1', 'mov1']
    stocks_df = []
    for i in range(N):
        d = pd.DataFrame({'open': px[:, i], 'high': px[:, i] * 1.01, 'low': px[:, i] * 0.99, 'close': px[:, i],
                          'f1': np.log(rel[:, i]), 'f2': np.random.default_rng(i).normal(size=T),
                          'weekday': idx.weekday, 'day': idx.day, 'month': idx.month, 'ret1': 0.0, 'mov1': 0}, index=idx)
        stocks_df.append(d)
    ds = types.SimpleNamespace(stocks=[f'S{i}' for i in range(N)], stocks2id={}, id2stocks={}, aux_stocks=[],
                               features_name=feats, temporals_name=temps, labels_name=labels, stocks_df=stocks_df)
    tg = s1_targets(N, cash=True)

    def run(c):
        random.seed(0)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            e = Env(mode='train', dataset=ds, if_norm=True, if_norm_temporal=False, days=DAYS,
                    initial_amount=1e3, transaction_cost_pct=c)
        random.seed(1); e.reset(); d0 = e.day; r, v = [], []
        for w in tg:
            _, rew, _, info = e.step(w.copy()); r.append(rew); v.append(info['portfolio_value'])
        return r, v, d0
    (r_c, v_c, d0), (r_0, v_0, _) = run(C_TEST), run(0.0)
    relp = px[d0 + 1:d0 + 1 + len(tg)] / px[d0:d0 + len(tg)]
    turn = drift_turnover(tg, relp, cash=True)
    res = r_judge(r_c, r_0, turn, v_c, v_0)
    res['setup'] = f'N={N}, EnvironmentPV(기본 설정 177행) AST 추출, 행동 = [현금, 종목] 가중치, 보상 = 포트폴리오 가치'
    return 'R', res


# ---------------------------------------------------------------- #11 MASA (R)
def t11_masa():
    import copy, gym, pandas as pd, scipy.stats as spstats
    from gym import spaces
    from gym.utils import seeding
    ns = {'np': np, 'pd': pd, 'copy': copy, 'time': time, 'gym': gym, 'spaces': spaces, 'seeding': seeding,
          'spstats': spstats, 'entropy': None, 'DummyVecEnv': None, 'os': os}
    Env = extract(os.path.join(ROOT, '.audit/masa/utils/tradeEnv.py'), 'StockPortfolioEnv', ns)
    COV_LB, N, T = 5, 10, 12          # config.py 33행 topK 10, 82행
    # 이전 감사 하네스(replication/code_audit/audit_new.py masa_factory)와 같은 설정: 관측기·제어기 끔(비용 행과 무관)
    cfg = types.SimpleNamespace(
        enable_cov_features=False, enable_market_observer=False, enable_controller=False,
        is_enable_dynamic_risk_bound=False, benchmark_algo='MASA-dc', only_long_algo_lst=['CRP', 'EG', 'OLMAR', 'PAMR', 'RMR'],
        trade_pattern=1, otherRef_indicator_ma_window=5, dailyRetun_lookback=COV_LB, mode='RLonly',
        trained_best_model_type='js_loss', lambda_1=1000.0, lambda_2=10.0, mkt_rf={'DJIA': 1.6575},
        market_name='DJIA', risk_default=0.017, tech_indicator_input_lst=['CHANGE'])
    cfg.otherRef_indicator_lst = ['MA-5', f'DAILYRETURNS-{COV_LB}']
    kw = {'max_shares': 100, 'initial_asset': 1000000, 'reward_scaling': 1, 'norm_method': 'sum',
          'slippage': 0.001, 'seed_num': 2022}
    rel = synth_rel(T + 2, N, seed=0); px = np.vstack([np.ones(N), np.cumprod(rel, axis=0)])
    rng = np.random.default_rng(1)
    rows = [{'date': f'd{d:04d}', 'stock': f's{i:02d}', 'close': px[d, i], 'CHANGE': 0.0, 'MA-5': px[d, i],
             f'DAILYRETURNS-{COV_LB}': list(rng.normal(0, 0.01, COV_LB))} for d in range(px.shape[0]) for i in range(N)]
    raw = pd.DataFrame(rows)
    tg = s1_targets(N, cash=False)

    def run(c):
        np.random.seed(0)                                   # 슬리피지 난수를 두 실행에서 같게
        e = Env(cfg, raw.copy(), 'train', N, N, cfg.tech_indicator_input_lst, transaction_cost=c, **kw); e.reset()
        r, v, rels = [], [], []
        for w in tg:
            cur = e.curData['close'].values * (1 + e.cur_slippage_drift)
            e.step(w.copy())
            now = e.curData['close'].values * (1 + e.cur_slippage_drift)
            r.append(float(e.reward)); v.append(float(e.asset_lst[-1])); rels.append(now / cur)
        return r, v, np.array(rels)
    (r_c, v_c, _), (r_0, v_0, rels) = run(C_TEST), run(0.0)
    turn = drift_turnover(tg, rels, cash=False)
    res = r_judge(r_c, r_0, turn, v_c, v_0)
    res['setup'] = f'N={N}, StockPortfolioEnv AST 추출, mode train, 학습 보상 = self.reward(354행), 슬리피지 난수 고정'
    return 'R', res


# ---------------------------------------------------------------- #13 DeepAries (R)
def t13_deeparies():
    import torch
    P = os.path.join(ROOT, '.t1env/DeepAries/exp/exp_DeepAries.py')
    Env = extract(P, 'TradingEnvironment', {'np': np, 'torch': torch})
    TOT, K, T = 30, 20, 8             # total_stocks(DJ30), num_stocks 기본 20(main.py 114행) → top-k 20개만 비영
    args = types.SimpleNamespace(seq_len=96, complex_fee=False, num_stocks=K, total_stocks=TOT, fee_rate=None)
    rel = synth_rel(T, TOT, seed=0)
    tg = s1_targets(TOT, cash=False, eq_n=K)
    turn = drift_turnover(tg, rel, cash=False)

    def run(c):
        a = types.SimpleNamespace(**vars(args)); a.fee_rate = c
        e = Env(a); e.reset(); r, v = [], []
        for t, w in enumerate(tg):
            rew = e.step(torch.tensor(w, dtype=torch.float32), torch.tensor(rel[t] - 1, dtype=torch.float32))
            r.append(float(rew) * 1.2); v.append(float(e.portfolio_value))   # 보너스 배수(222–226행): 행동만의 함수, 두 실행 같음
        return r, v
    (r_c, v_c), (r_0, v_0) = run(C_TEST), run(0.0)
    res = r_judge(r_c, r_0, turn, v_c, v_0)
    res['setup'] = f'total {TOT}, top-k {K}, complex_fee False(기본), fee_rate 주입, 보상 × 1.2(보너스 분기 고정)'
    return 'R', res


# ---------------------------------------------------------------- #14 MARS (R) — L(출판판), N(저자 수정본)
def _mars(ver):
    import importlib, pandas as pd
    d = os.path.join(ROOT, '.marswork', ver); sys.path.insert(0, d); os.chdir(d)
    config = importlib.import_module('config'); main = importlib.import_module('main')
    res_dir = os.path.join(WORK, f'mars_{ver}') + '/'; os.makedirs(res_dir + 'log', exist_ok=True)
    config.RESULT_DIR = res_dir                             # 로그 출력 위치(설정)
    N, T = config.NUM_STOCKS, 60
    rel = synth_rel(T - 1, N, seed=0); px = 100 * np.vstack([np.ones(N), np.cumprod(rel, axis=0)])
    idx = pd.bdate_range('2020-01-01', periods=T)
    data = pd.DataFrame({f'S{i:02d}_Adj Close': px[:, i] for i in range(N)}, index=idx)
    # S1(주식수 행동 [-1,1]×MAX_TRADE_SIZE): 전 종목 매수 → 0번만 남기고 매도·0번 매수 → 0번 매도·1번 매수 → 유지(0)
    eq = np.ones(N); a1 = -np.ones(N); a1[0] = 1; a2 = np.zeros(N); a2[0] = -1; a2[1] = 1
    acts = [eq, a1, a2]

    class FakeBuf:
        def __init__(self): self.r = []
        def add(self, **k): self.r.append(k['reward'])

    class FakeMA:                                            # 행동 공급자(학습·메타 제어 없음)
        def __init__(self):
            self.agents = [types.SimpleNamespace(replay_buffer=FakeBuf())]; self.agent_weights = np.ones(1); self.t = 0
        def select_action(self, state, explore, returns_history):
            a = acts[self.t] if self.t < len(acts) else np.zeros(N); self.t += 1; return a.astype(float).copy()
        def is_action_unsafe(self, **k): return False
        def update_agent_weights(self, *a, **k): pass
        def add_experience_for_meta_controller(self, *a, **k): pass
        def update_agents(self, *a, **k): return {}

    def run(c):
        config.TRANSACTION_COST = c
        ma = FakeMA()
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            st = main.run_episode(ma, data, None, train=True, batch_size=0, populate_meta_buffer=False)
        return ma.agents[0].replay_buffer.r, st['portfolio_values']
    (r_c, v_c), (r_0, v_0) = run(C_TEST), run(0.0)
    n = len(r_0)
    v0 = np.array(v_0)
    # 회전율(참조): c=0 실행의 체결 금액/가치를 직접 계산하지 않고, 행동이 0이 아닌 스텝(첫 3스텝)을 회전율 > 0으로 둔다
    turn = [1.0 if k < len(acts) else 0.0 for k in range(n)]
    res = r_judge(r_c, r_0, turn, v_c, v_0)
    dr = np.array(r_0[:len(acts)]) - np.array(r_c[:len(acts)])
    res['reward_drop_first3'] = dr.tolist()
    res['return_component_scale_first3'] = (np.diff(v0[:len(acts) + 1]) / v0[:len(acts)]).tolist()
    res['setup'] = f'{ver}: run_episode 그대로, 행동 공급자만 대체, N={N}, TRANSACTION_COST 설정 주입, 보상 = replay_buffer.add(reward=…)'
    res['config_cost'] = 0.001
    return 'R', res


def t14_mars_L():
    return _mars('L')


def t14_mars_N():
    return _mars('N')


# ---------------------------------------------------------------- #16 Markowitz Meets Bellman (R)
def t16_mmb():
    import importlib, pandas as pd
    spec = importlib.util.spec_from_file_location('mmb_env', os.path.join(DL, 'mmb/env_stocktrading.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    N, T, H = 5, 12, 100                       # 스크립트 tickers_to_keep 5개, hmax 100, initial 10000
    IND = ['macd', 'boll_ub', 'boll_lb', 'rsi_30', 'cci_30', 'dx_30', 'close_30_sma', 'close_60_sma']   # FinRL INDICATORS
    rel = synth_rel(T, N, seed=0); px = 100 * np.vstack([np.ones(N), np.cumprod(rel, axis=0)])
    rows = []
    for t in range(T + 1):
        for i in range(N):
            r = {'idx': t, 'date': f'2020-01-{t + 1:02d}', 'tic': f'S{i}', 'close': px[t, i]}
            r.update({k: 0.0 for k in IND}); rows.append(r)
    df = pd.DataFrame(rows).set_index('idx'); df.index.name = None
    tg = s1_targets(N, cash=True)

    def run(c):
        e = m.StockTradingEnv(df=df, stock_dim=N, hmax=H, initial_amount=10000, num_stock_shares=[0] * N,
                              buy_cost_pct=[c] * N, sell_cost_pct=[c] * N, reward_scaling=1e-4,
                              state_space=1 + 2 * N + len(IND) * N, action_space=N, tech_indicator_list=IND)
        e.reset(); r, v, tv = [], [], []
        for w in tg:
            s = e.state; p = np.array(s[1:N + 1]); h = np.array(s[N + 1:2 * N + 1]); V = s[0] + p @ h
            a = np.clip((w[1:] * V / p - h) / H, -1, 1)
            _, rew, *_ = e.step(a)
            h2 = np.array(e.state[N + 1:2 * N + 1]); tv.append(float(np.abs(h2 - h) @ p / V))
            r.append(rew); v.append(e.asset_memory[-1])
        return r, v, tv
    (r_c, v_c, _), (r_0, v_0, tv0) = run(C_TEST), run(0.0)
    res = r_judge(r_c, r_0, tv0, v_c, v_0)
    res['setup'] = f'FinRL StockTradingEnv @55764e8 그대로 import, N={N}, 스크립트 설정, 보상 = (end−begin)×1e-4'
    return 'R', res


TARGETS = {
    '#2 FinRL POE': ('t2_finrl_poe', 'B'),
    '#3 FinRL SPE': ('t3_finrl_spe', 'N'),
    '#4 RAT': ('t4_rat', 'S'),
    '#5 Ensemble': ('t5_ensemble', 'S'),
    '#6 DeepTrader': ('t6_deeptrader', 'S'),
    '#8 TradeMaster': ('t8_trademaster', 'S'),
    '#9 AlphaMix+': ('t9_alphamix', 'N'),
    '#10 EarnMore': ('t10_earnmore', 'N'),
    '#11 MASA': ('t11_masa', 'B'),
    '#13 DeepAries': ('t13_deeparies', 'S'),
    '#14 MARS L': ('t14_mars_L', 'S'),
    '#14 MARS N': ('t14_mars_N', 'S'),
    '#16 Markowitz Meets Bellman': ('t16_mmb', 'S'),
}
SERVER_WAIT = {'#1 PGPortfolio': 'S', '#7 WaveCorr': 'S', '#12 jackieli PGPortfolio': 'S', '#15 Margin Trader': 'S'}
STATIC_EVAL = {'#2 FinRL POE': True, '#3 FinRL SPE': False, '#4 RAT': True, '#5 Ensemble': True, '#6 DeepTrader': True,
               '#8 TradeMaster': True, '#9 AlphaMix+': False, '#10 EarnMore': False, '#11 MASA': True,
               '#13 DeepAries': True, '#14 MARS L': True, '#14 MARS N': True, '#16 Markowitz Meets Bellman': True}


def classify(kind, res, name):
    seen = res.get('cost_seen')
    if seen is None:
        return 'X'
    if seen:
        return 'S'
    ev = res.get('eval_charged', res.get('value_charged'))
    if ev is None:
        ev = STATIC_EVAL[name]
    return 'B' if ev else 'N'


def one(name):
    os.makedirs(WORK, exist_ok=True)
    fn, pred = TARGETS[name]
    t0 = time.time()
    try:
        kind, res = globals()[fn]()
        cls = classify(kind, res, name)
        out = {'type': kind, 'measured': res, 'class': cls}
    except Exception as e:
        import traceback
        out = {'type': None, 'class': 'X', 'error': f'{type(e).__name__}: {e}', 'trace': traceback.format_exc()[-1500:]}
    out['static_prediction'] = pred
    out['match'] = (out['class'] == pred)
    out['runtime_s'] = round(time.time() - t0, 1)
    return out


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--one':
        print('@@JSON@@' + json.dumps(one(sys.argv[2]), ensure_ascii=False, default=float))
        sys.exit(0)
    names = sys.argv[1:] or list(TARGETS)
    path = os.path.join(HERE, 'results.json')
    allres = json.load(open(path)) if os.path.exists(path) else {}
    allres.setdefault('_meta', {})
    allres['_meta'].update({'c_test': C_TEST, 'L_thresholds': [L_HI, L_LO], 'R_eps': R_EPS,
                            'controls': json.load(open(os.path.join(HERE, 'controls_result.json')))})
    for nm in names:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), '--one', nm], capture_output=True, text=True,
                           env=dict(os.environ), cwd=ROOT)
        line = [l for l in p.stdout.splitlines() if l.startswith('@@JSON@@')]
        r = json.loads(line[-1][8:]) if line else {'class': 'X', 'error': 'no output', 'stderr': p.stderr[-2000:],
                                                     'static_prediction': TARGETS[nm][1], 'match': False}
        prev = allres.get(nm, {})
        for k in ('notes', 'time_spent'):
            if k in prev:
                r[k] = prev[k]
        allres[nm] = r
        m = r.get('measured', {})
        stat = m.get('rel_grad_diff', m.get('max_abs_dr_turnover_steps'))
        print(f"{nm:32s} {r.get('type')} stat={stat} class={r['class']} pred={r['static_prediction']} "
              f"match={r['match']} {r.get('error', '')[:200]}")
    for nm, pred in SERVER_WAIT.items():
        allres.setdefault(nm, {'class': '서버 대기', 'static_prediction': pred, 'match': None, 'notes': '서버 대기(이번 맥 실행 대상 아님)'})
    json.dump(allres, open(path, 'w'), ensure_ascii=False, indent=1, default=float)
