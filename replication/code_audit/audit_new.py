# 공개 코드 감사 — 신규 대상 동적 점검(notes/prereg_code_audit.md 3장 3단계, 정적 예측 d1b1b30 이후 실행)
# 사용: python3 -I audit_new.py <.audit 경로> <작업 폴더(쓰지 않음, 호환용)>
# 각 어댑터는 원 저장소의 비용 계산 코드를 그대로 호출하고, 행동은 목표 가중치로 넣는다. 학습 없음.
import ast, json, os, sys, types
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I 실행 시 이 폴더(자체 코드)만 추가
from harness import synth_prices, c1, s1, cost_defect, standard_actions

AUD = os.path.abspath(sys.argv[1]); WORK = os.path.abspath(sys.argv[2])
HERE = os.path.dirname(os.path.abspath(__file__))
T = 40
COV_LB, RISK_DEFAULT = 5, 0.017   # MASA config.py 82·70행 기본값


def extract(path, name, ns):
    """모듈을 실행하지 않고 클래스·함수 정의 하나만 꺼낸다(모듈 머리의 학습 스크립트·import를 피함)."""
    src = open(path).read()
    node = next(n for n in ast.parse(src).body if getattr(n, 'name', None) == name)
    exec(ast.get_source_segment(src, node), ns)
    return ns[name]


# ---------- #4 RAT: Test_Loss(main.py 1074–1133) ----------
def rat_factory(N):
    import torch, torch.nn as nn
    torch.Tensor.cuda = lambda self, *a, **k: self          # 장치만 CPU로, 계산 불변(정적 문서 0장)
    _ones = torch.ones
    ns = {'torch': torch, 'nn': nn}
    ns['max_drawdown'] = extract(f'{AUD}/rat/main.py', 'max_drawdown', ns)
    TL = extract(f'{AUD}/rat/main.py', 'Test_Loss', ns)
    Y = synth_prices(N, T, seed=0)

    class Env:
        def __init__(self, c):
            self.loss = TL(c, 0.0, 0.0, 0.0, size_average=False); self.ws = []
        def step(self, w):
            self.ws.append(np.asarray(w, float)); t = len(self.ws)
            W = torch.tensor(np.array(self.ws), dtype=torch.float32).view(1, t, 1, N + 1)
            y = torch.ones(1, t, N, 4, dtype=torch.float32); y[0, :, :, 0] = torch.tensor(Y[:t])
            if t == 1:   # Test_Loss는 스텝 2개 이상을 가정(squeeze) → 첫 스텝은 비용 없는 총수익과 같다(1100행)
                pc = np.array([float(W[0, 0, 0] @ torch.cat([torch.ones(1), y[0, 0, :, 0]]))])
            else:
                out = self.loss(W, y); pc = out[5].detach().numpy().reshape(-1)
            V = float(np.prod(pc))
            return {'reward': float(np.log(pc[-1])), 'value': V, 'w_exec': self.ws[-1], 'y': np.concatenate([[1.0], Y[t - 1]])}
    return Env, True


# ---------- #6 DeepTrader: PortfolioSim(portfolio_env.py 263–380) ----------
def deeptrader_factory(N, allow_short):
    from collections import namedtuple
    ns = {'np': np, 'Reward': namedtuple('Reward', ('total', 'long', 'short')), 'EPS': 1e-20}   # 7·9행과 같음
    portfolio_env = types.SimpleNamespace(
        PortfolioSim=extract(f'{AUD}/deeptrader/src/environment/portfolio_env.py', 'PortfolioSim', ns))
    Y = synth_prices(N, T, seed=0)

    class Env:
        def __init__(self, c):
            self.sim = portfolio_env.PortfolioSim(N, c, 0.0, allow_short=allow_short); self.sim.reset(1); self.t = 0
        def step(self, w):
            w = np.asarray(w, float); risky = w[1:] / w[1:].sum()
            w0 = np.zeros((1, 2 * N)); w0[0, :N] = risky; w0[0, N:] = 1 / N   # 공매도 칸은 p=1이라 쓰이지 않음
            r, info, _ = self.sim._step(w0, Y[self.t][None, :], np.array([1.0]))
            y = np.concatenate([[1.0], Y[self.t]]); self.t += 1
            return {'reward': float(r.total[0]), 'value': float(info['total_value'][0]),
                    'w_exec': np.concatenate([[0.0], risky]), 'y': y}
    return Env, True


# ---------- #8 WaveCorr: calculateMu(wavecorr_agent.py 122–134) + 평가 경로(144–158) ----------
def wavecorr_factory(N):
    calc = extract(f'{AUD}/wavecorr/src/wavecorr_agent.py', 'agent_manager', {'np': np, 'pd': None, 'tf': None,
                   'os': os, 'time': None, 'datetime': None, 'neuralNetwork': None}).calculateMu
    Y = synth_prices(N, T, seed=0)

    class Env:
        def __init__(self, c):
            self.tradeFee = c; self.prev = np.full(N, 1 / N); self.V = 1.0; self.t = 0   # reset(): 등가중(102–104행)
        def step(self, w):
            w = np.asarray(w, float)
            mu = calc(self, self.prev[None, None, :], w[None, None, :])[0, 0]
            g = float(w @ Y[self.t]) * mu; V0, self.V = self.V, self.V * g
            self.prev = w * Y[self.t] / (w @ Y[self.t]); y = Y[self.t]; self.t += 1
            return {'reward': float(np.log(g)), 'value': self.V, 'w_exec': w, 'y': y}
    return Env, False


# ---------- #13 MASA: StockPortfolioEnv(tradeEnv.py) 원본 step ----------
def masa_factory(N):
    import copy, time, gym, pandas as pd, scipy.stats as spstats
    from gym import spaces
    from gym.utils import seeding
    ns = {'np': np, 'pd': pd, 'copy': copy, 'time': time, 'gym': gym, 'spaces': spaces, 'seeding': seeding,
          'spstats': spstats, 'entropy': None, 'DummyVecEnv': None, 'os': os}
    StockPortfolioEnv = extract(f'{AUD}/masa/utils/tradeEnv.py', 'StockPortfolioEnv', ns)
    # Config()는 폴더를 만들고 학습 모듈을 import하므로 쓰지 않는다. env가 읽는 속성만 config.py 기본값으로 둔다.
    # 시장 관측기·제어기는 학습된 모델과 외부 데이터가 필요해 끈다. 비용 행(164·189·203행)은 이 설정과 무관하다.
    cfg = types.SimpleNamespace(
        enable_cov_features=False, enable_market_observer=False, enable_controller=False,
        is_enable_dynamic_risk_bound=False, benchmark_algo='MASA-dc', only_long_algo_lst=['CRP', 'EG', 'OLMAR', 'PAMR', 'RMR'],
        trade_pattern=1, otherRef_indicator_ma_window=5, dailyRetun_lookback=COV_LB, mode='RLonly',
        trained_best_model_type='js_loss', lambda_1=1000.0, lambda_2=10.0, mkt_rf={'DJIA': 1.6575},
        market_name='DJIA', risk_default=RISK_DEFAULT, tech_indicator_input_lst=['CHANGE'])
    cfg.otherRef_indicator_lst = ['MA-5', f'DAILYRETURNS-{COV_LB}']
    kw = {'max_shares': 100, 'initial_asset': 1000000, 'reward_scaling': 1, 'norm_method': 'sum',
          'transaction_cost': 0.0003, 'slippage': 0.001, 'seed_num': 2022}   # config.py 156–157행
    Y = synth_prices(N, T + 2, seed=0)
    px = np.vstack([np.ones(N), np.cumprod(Y, axis=0)])
    lb = cfg.dailyRetun_lookback
    rng = np.random.default_rng(1)
    rows = []
    for d in range(px.shape[0]):
        for i in range(N):
            rows.append({'date': f'd{d:04d}', 'stock': f's{i:02d}', 'close': px[d, i], 'CHANGE': 0.0,
                         f'MA-{cfg.otherRef_indicator_ma_window}': px[d, i],
                         f'DAILYRETURNS-{lb}': list(rng.normal(0, 0.01, lb))})
    raw = pd.DataFrame(rows)

    class Env:
        def __init__(self, c):
            np.random.seed(0)                                  # 슬리피지 난수(48행)를 두 실행에서 같게
            k = dict(kw); k['transaction_cost'] = c
            self.e = StockPortfolioEnv(cfg, raw.copy(), 'test', N, N, cfg.tech_indicator_input_lst, **k)
            self.e.reset()
        def step(self, w):
            w = np.asarray(w, float); a = w[1:] / w[1:].sum()
            last = self.e.curData['close'].values * (1 + self.e.cur_slippage_drift)
            self.e.step(a)
            cur = self.e.lastDayData['close'].values * (1 + self.e.last_slippage_drift)
            now = self.e.curData['close'].values * (1 + self.e.cur_slippage_drift)
            y = np.concatenate([[1.0], now / cur])
            V = float(self.e.asset_lst[-1]) / kw['initial_asset']
            return {'reward': float(self.e.reward), 'value': V,   # RL 보상 변수(tradeEnv.py 354행)
                    'w_exec': np.concatenate([[0.0], a]), 'y': y}
    return Env, True


# ---------- #14 jackieli19/PGPortfolio: calculate_pv_after_commission + backtest 74–77행 ----------
def jackieli_factory(N):
    calc = extract(f'{AUD}/jackieli/pgportfolio/tools/trade.py', 'calculate_pv_after_commission', {'np': np})
    Y = synth_prices(N, T, seed=0)

    class Env:
        def __init__(self, c):
            self.c = c; self.last = np.zeros(N + 1); self.last[0] = 1.0; self.V = 1.0; self.t = 0   # 현금 시작
        def step(self, w):
            w = np.asarray(w, float); fp = np.concatenate([[1.0], Y[self.t]])
            pv = calc(w, self.last, self.c); change = pv * float(w @ fp)
            self.last = pv * w * fp / change; self.V *= change; self.t += 1
            return {'reward': float(np.log(change)), 'value': self.V, 'w_exec': w, 'y': fp}
    return Env, True


TARGETS = [
    ('#4 RAT', 11, 0.0025, lambda N: rat_factory(N)),
    ('#6 DeepTrader (allow_short=True, DJIA 주 설정)', 30, 0.001, lambda N: deeptrader_factory(N, True)),
    ('#6 DeepTrader (allow_short=False, CSI100, 기술)', 30, 0.001, lambda N: deeptrader_factory(N, False)),
    ('#8 WaveCorr', 50, 0.0005, lambda N: wavecorr_factory(N)),
    ('#13 MASA', 10, 0.0003, lambda N: masa_factory(N)),
    ('#14 jackieli19/PGPortfolio', 11, 0.0025, lambda N: jackieli_factory(N)),
]

res = {}
for name, N, c, fac in TARGETS:
    try:
        Env, has_cash = fac(N)
        acts = standard_actions(N, has_cash=True)          # 모든 어댑터가 [현금, 위험자산…] 목표 가중치를 받는다
        if not has_cash:
            acts = [a[1:] / a[1:].sum() for a in acts]
        mk = lambda cc, Env=Env: Env(cc)
        r1 = c1(mk, c, acts); r2 = s1(mk, c, acts, has_cash=has_cash)
        res[name] = {'N': N, 'c_test': c, 'C1': r1, 'S1': r2,
                     'cost_defect': cost_defect('명시 비용', r1, r2)}
    except Exception as ex:
        res[name] = {'error': repr(ex)}
json.dump(res, open(f'{HERE}/results_new.json', 'w'), ensure_ascii=False, indent=1)
for k, v in res.items():
    if 'error' in v:
        print(k, 'ERROR', v['error'][:300])
    else:
        print(k, '| C1', v['C1']['verdict'], '| S1', round(v['S1']['ratio'], 4), v['S1']['timing'], v['S1']['verdict'],
              '| 결함', v['cost_defect'])


# ---------- P1 동적: env가 행동을 가중치로 바꾸는 대상만(MASA). 나머지는 env가 가중치를 그대로 받는다 ----------
from harness import p1_dynamic
Env, _ = masa_factory(10)
e = Env(0.0003).e
p1 = {'#13 MASA': dict(p1_dynamic(e.weights_normalization, 0.0, 1.0, 10), layer='env sum 정규화(Box(0,1))')}
for k, note in [('#4 RAT', '정책: 2·softmax(선형) − softmax(선형), env 정규화 없음(main.py 645–650행)'),
                ('#6 DeepTrader (allow_short=True, DJIA 주 설정)', '정책: sigmoid 점수 상위 G=4 softmax, 나머지 0(agent.py 41–61행, ASU.py 267행)'),
                ('#8 WaveCorr', '정책: softmax(선형), env 정규화 없음(wavecorr_network.py 222–224행)'),
                ('#14 jackieli19/PGPortfolio', '정책: 현금 편향 + softmax(선형)(network.py 115–122행)')]:
    p1[k] = {'layer': note, 'R': 'inf(코드 행 판정)'}
p1['#6 DeepTrader (allow_short=True, DJIA 주 설정)']['held_ratio_bound'] = float(np.e)
p1['#6 DeepTrader (allow_short=True, DJIA 주 설정)']['w_max_bound'] = float(np.e / (np.e + 3))
res2 = json.load(open(f'{HERE}/results_new.json'))
for k, v in p1.items():
    res2.setdefault(k, {})['P1'] = v
json.dump(res2, open(f'{HERE}/results.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(p1, ensure_ascii=False, indent=1))
