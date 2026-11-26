"""FinRL EIIE/EI3 cost-gradient mechanism experiment (pre-registered: notes/finrl_costgrad_prereg.md, 808c2d6).

Conditions (same data, settings, seeds):
  O  original FinRL PolicyGradient (cost factor trf_mu enters the loss as a buffer constant).
  G  PolicyGradient subclass whose only change is the loss: trf_mu is computed in-graph from the
     policy output mu and the env's drifted previous weights with the env's own TRF formula
     (env_portfolio_optimization.py lines 323-331), unrolled for 20 fixed iterations from
     1 - 2c + c^2, relu for max. The buffer additionally stores the drifted previous weights
     (env._final_weights[-1], read just before env.step).
Data / settings / alpha_eff definition are ported from replication/finrl_start_state.ipynb.

Commands (run from the repo root, PYTHONPATH=.t3env/pylib python3 replication/finrl_costgrad.py ...):
  gate                      prereg section 2 gradient gate (float64), writes replication/finrl_costgrad/gate.json
  run --worker i --nworkers N   train+measure the settings with index % N == i (skips finished settings)
  launch --nworkers N       start N background `run` workers with nohup (logs in WORK/logs)
  status                    list finished settings
  judge                     prereg section 3 (H-G1, H-G2); refuses unless all 24 settings are finished

Third-party code: FinRL files at the pinned commit are fetched unmodified (md5 checked).
Missing optional packages are replaced by import-only stubs: quantstats (used by the env only for the
terminal-step printout/plot) and torch_geometric (used only by GPM, not run here).
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import logging
import os
import pathlib
import random
import subprocess
import sys
import time
import types
import urllib.request
import warnings

REPO = pathlib.Path(__file__).resolve().parents[1]
WORK = pathlib.Path(os.environ.get(
    'COSTGRAD_WORK',
    '/private/tmp/claude-501/-Users-seungbin-school-4-1-------/e9f6f6e8-2d56-4c96-a326-738b6cf12ec5/scratchpad/costgrad'))
OUT = REPO / 'replication' / 'finrl_costgrad'
PKG = WORK / 'pkg' / 'finrl_po'
DATA_DIR, MDIR, LOGS = WORK / 'data', WORK / 'models', WORK / 'logs'

COMMIT = '7e98df461cbc7772f16a545a2f13b521e5d0b8f4'
RAW = f'https://raw.githubusercontent.com/AI4Finance-Foundation/FinRL/{COMMIT}/finrl/'
FILES = {
    'agents/portfolio_optimization/algorithms.py': '56450487266302aa4a5626960fbce53c',
    'agents/portfolio_optimization/architectures.py': '8e232d6aed40f5f3331c3e4ad1c82d0f',
    'agents/portfolio_optimization/utils.py': 'd385a1d3b58cda7511344d884b389586',
    'agents/portfolio_optimization/models.py': '8ac110764d74b5ff2ec69f0221f081dc',
    'meta/env_portfolio_optimization/env_portfolio_optimization.py': 'bf496f4f7d6ad5a20242dd41322e4419',
    'meta/preprocessor/yahoodownloader.py': 'e1c062317c1ef9edc0fdec4bec829dc8',
    'config_tickers.py': '39940cf3c3d600dd6fb7e68879ee5eb1',
}


def fetch_finrl():
    PKG.mkdir(parents=True, exist_ok=True)
    (PKG / '__init__.py').touch()
    for f, h in FILES.items():
        p = PKG / pathlib.Path(f).name
        if not p.exists():
            urllib.request.urlretrieve(RAW + f, p)
        got = hashlib.md5(p.read_bytes()).hexdigest()
        if got != h:
            raise SystemExit(f'md5 mismatch for {p}: {got} != {h}')


def install_import_stubs():
    """Import-only stubs. They never touch any computed quantity."""
    try:
        import quantstats  # noqa: F401
    except ModuleNotFoundError:
        qs = types.ModuleType('quantstats')
        qs.stats = types.SimpleNamespace(max_drawdown=lambda *a, **k: float('nan'),
                                         sharpe=lambda *a, **k: float('nan'))
        qs.plots = types.SimpleNamespace(snapshot=lambda *a, **k: None)
        sys.modules['quantstats'] = qs
    try:
        import torch_geometric  # noqa: F401
    except ModuleNotFoundError:
        def _blocked(*a, **k):
            raise RuntimeError('torch_geometric stub: GPM is not used in this experiment')
        tg = types.ModuleType('torch_geometric')
        for sub, names in {'data': ['Batch', 'Data'], 'nn': ['RGCNConv', 'Sequential'], 'utils': ['to_dense_batch']}.items():
            m = types.ModuleType(f'torch_geometric.{sub}')
            for n in names:
                setattr(m, n, _blocked)
            setattr(tg, sub, m)
            sys.modules[f'torch_geometric.{sub}'] = m
        sys.modules['torch_geometric'] = tg


fetch_finrl()
install_import_stubs()
sys.path.insert(0, str(PKG.parent))
warnings.filterwarnings('ignore')
logging.getLogger('matplotlib.font_manager').disabled = True

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from sklearn.preprocessing import MaxAbsScaler  # noqa: E402
from tqdm import tqdm  # noqa: E402

from finrl_po.yahoodownloader import YahooDownloader  # noqa: E402
from finrl_po.env_portfolio_optimization import PortfolioOptimizationEnv  # noqa: E402
from finrl_po.models import DRLAgent, MODELS  # noqa: E402
from finrl_po.algorithms import PolicyGradient  # noqa: E402
from finrl_po.architectures import EIIE, EI3  # noqa: E402
from finrl_po import utils as fu  # noqa: E402
from finrl_po.utils import apply_portfolio_noise  # noqa: E402
from finrl_po.config_tickers import DOW_30_TICKER  # noqa: E402

# ---------------------------------------------------------------- settings (fixed, = finrl_start_state.ipynb)
device = 'cpu'
TW, W, H, EPISODES, LR = 50, 60, 60, 40, 0.01
FEE = 0.0025
TRF_ITERS = 20
ARCH = {'EIIE': (EIIE, {'k_size': 3, 'time_window': TW}), 'EI3': (EI3, {'time_window': TW})}
SEEDS = [0, 1, 2]
CONDS = ['O', 'G']
MARKETS = {'BR10': ["VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "RENT3.SA", "LREN3.SA", "PRIO3.SA", "WEGE3.SA", "ABEV3.SA"],
           'DOW30': list(DOW_30_TICKER)}
# order: pairs (O,G) of the same (arch, market, seed) adjacent
CONFIGS = [(a, m, s, c) for s in SEEDS for a in ARCH for m in MARKETS for c in CONDS]
tag_of = lambda a, m, s, c: f'{c}_{a}_{m}_s{s}'  # noqa: E731
GATE_THRESHOLD = 1e-6


# ---------------------------------------------------------------- condition G
def trf_graph(mu, last_w, c, iters=TRF_ITERS):
    """env TRF formula (lines 323-331) in-graph: fixed `iters` iterations from 1-2c+c^2, relu for max.
    mu, last_w: (B, n+1) with cash at index 0. Returns (B, 1)."""
    w0 = mu[:, 0]
    t = torch.full_like(w0, 1 - 2 * c + c ** 2)
    for _ in range(iters):
        t = (1 - c * w0 - (2 * c - c ** 2) * torch.relu(last_w[:, 1:] - t.unsqueeze(1) * mu[:, 1:]).sum(dim=1)) / (1 - c * w0)
    return t.unsqueeze(1)


class PolicyGradientCostGrad(PolicyGradient):
    """Identical to PolicyGradient except: buffer stores the drifted previous weights, and the
    loss uses trf_graph(mu, prev_w, c) instead of the buffered constant trf_mu."""

    def train(self, episodes=100):
        for i in tqdm(range(1, episodes + 1)):
            obs = self.train_env.reset()
            self.train_pvm.reset()
            done = False
            while not done:
                last_action = self.train_pvm.retrieve()
                obs_batch = np.expand_dims(obs, axis=0)
                last_action_batch = np.expand_dims(last_action, axis=0)
                action = apply_portfolio_noise(
                    self.train_policy(obs_batch, last_action_batch), self.action_noise
                )
                self.train_pvm.add(action)
                prev_w = np.asarray(self.train_env._final_weights[-1], dtype=np.float64)  # [G] drifted holdings
                next_obs, reward, done, info = self.train_env.step(action)
                exp = (obs, last_action, info["price_variation"], info["trf_mu"], prev_w)  # [G] + prev_w
                self.train_buffer.append(exp)
                if len(self.train_buffer) == self.train_batch_size:
                    self._gradient_ascent()
                obs = next_obs
            self._gradient_ascent()
            if self.validation_env:
                self.test(self.validation_env)

    def test(self, env, policy=None, online_training_period=10, lr=None, optimizer=None):
        self._setup_test(env, policy, online_training_period, lr, optimizer)
        obs = self.test_env.reset()
        self.test_pvm.reset()
        done = False
        steps = 0
        while not done:
            steps += 1
            last_action = self.test_pvm.retrieve()
            obs_batch = np.expand_dims(obs, axis=0)
            last_action_batch = np.expand_dims(last_action, axis=0)
            action = self.test_policy(obs_batch, last_action_batch)
            self.test_pvm.add(action)
            prev_w = np.asarray(self.test_env._final_weights[-1], dtype=np.float64)  # [G]
            next_obs, reward, done, info = self.test_env.step(action)
            exp = (obs, last_action, info["price_variation"], info["trf_mu"], prev_w)  # [G]
            self.test_buffer.append(exp)
            if steps % online_training_period == 0:
                self._gradient_ascent(test=True)
            obs = next_obs

    def _gradient_ascent(self, test=False):
        obs, last_actions, price_variations, _trf_mu_const, prev_w = (
            next(iter(self.test_dataloader)) if test else next(iter(self.train_dataloader))
        )
        obs = obs.to(self.device)
        last_actions = last_actions.to(self.device)
        price_variations = price_variations.to(self.device)
        prev_w = prev_w.to(self.device)
        c = (self.test_env if test else self.train_env)._comission_fee_pct
        mu = self.test_policy.mu(obs, last_actions) if test else self.train_policy.mu(obs, last_actions)
        # [G] in-graph cost factor (float64 like the buffered float64 trf_mu in O)
        trf_mu = trf_graph(mu.double(), prev_w, c)
        policy_loss = -torch.mean(torch.log(torch.sum(mu * price_variations * trf_mu, dim=1)))
        if test:
            self.test_policy.zero_grad()
            policy_loss.backward()
            self.test_optimizer.step()
        else:
            self.train_policy.zero_grad()
            policy_loss.backward()
            self.train_optimizer.step()


MODELS['pg_costgrad'] = PolicyGradientCostGrad
MODEL_NAME = {'O': 'pg', 'G': 'pg_costgrad'}


# ---------------------------------------------------------------- data (= notebook cell 3)
def load_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for mk, tics in MARKETS.items():
        rp = DATA_DIR / f'raw_{mk}.csv'
        if rp.exists():
            raw = pd.read_csv(rp)
        else:
            with contextlib.redirect_stdout(io.StringIO()):
                raw = YahooDownloader(start_date='2011-01-01', end_date='2022-12-31', ticker_list=tics).fetch_data()
            raw.to_csv(rp, index=False)
        raw['date'] = raw['date'].astype(str)
        first = raw.groupby('tic')['date'].min()
        dropped = sorted(first[first > '2011-01-31'].index)
        raw = raw[~raw['tic'].isin(dropped)]
        n_t = raw['tic'].nunique()
        full = raw.groupby('date')['tic'].nunique(); keep = full[full == n_t].index
        raw = raw[raw['date'].isin(keep)].sort_values(['date', 'tic']).reset_index(drop=True)
        num = [c for c in raw.columns if c not in ('date', 'tic', 'day') and pd.api.types.is_numeric_dtype(raw[c])]
        norm = raw.copy()
        for t, g in raw.groupby('tic'):
            norm.loc[g.index, num] = MaxAbsScaler().fit_transform(g[num])
        df = norm[['date', 'tic', 'close', 'high', 'low']].copy()
        dates = sorted(df['date'].unique())
        cw = raw.pivot(index='date', columns='tic', values='close')
        years = {y: df[(df['date'] >= f'{y}-01-01') & (df['date'] < f'{y}-12-31')] for y in (2020, 2021, 2022)}
        missing = sorted(set(tics) - set(raw['tic'].unique()) - set(dropped))
        out[mk] = dict(df=df, dates=dates, close=cw, N=n_t, years=years,
                       train=df[(df['date'] >= '2011-01-01') & (df['date'] < '2019-12-31')],
                       info=dict(n=n_t, dropped=dropped, missing=missing, days=len(dates),
                                 year_days={y: int(d.date.nunique()) for y, d in years.items()}))
    return out


# ---------------------------------------------------------------- env / run helpers (= notebook cell 4)
_START = ['cash']
ENV_CWD = [str(WORK / 'envout' / 'main')]


def w0(kind, n):
    return np.array([1] + [0] * n, dtype=np.float32) if kind == 'cash' else np.array([0] + [1 / n] * n, dtype=np.float32)


_ORIG_PVM_RESET = fu.PVM.reset


def _pvm_reset(self):
    _ORIG_PVM_RESET(self)
    self.memory = [w0(_START[0], self.portfolio_size)] * (self.capacity + 1)


class StartEnv(PortfolioOptimizationEnv):
    def _reset_memory(self):
        super()._reset_memory()
        self._actions_memory[0] = w0(_START[0], self.portfolio_size); self._final_weights[0] = w0(_START[0], self.portfolio_size)


def make_env(d, fee, cls=None):
    # cwd only redirects the env's terminal-step PNG output
    return (cls or StartEnv)(d, initial_amount=100000, comission_fee_pct=fee, time_window=TW,
                             features=['close', 'high', 'low'], normalize_df=None, cwd=ENV_CWD[0])


def seed_all(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)


def new_model(D, mk, arch, cond, fee=FEE):
    cls, kw = ARCH[arch]
    with contextlib.redirect_stdout(io.StringIO()):
        return DRLAgent(make_env(D[mk]['train'], fee)).get_model(MODEL_NAME[cond], device, {'lr': LR, 'policy': cls}, dict(kw))


def run(model, policy, d, fee, start, online, seed=0):
    _START[0] = start; seed_all(seed)
    fu.PVM.reset = _pvm_reset; env = make_env(d, fee)
    with contextlib.redirect_stdout(io.StringIO()):
        DRLAgent.DRL_validation(model, env, policy=policy, online_training_period=10 if online else 10**9)
    _START[0] = 'cash'
    v = np.asarray(env._asset_memory['final'], dtype=np.float64)
    x = np.asarray([1 - float(a[0]) for a in env._actions_memory[1:]])
    return v, x, env


fu.PVM.reset = _pvm_reset


def alpha_from_gap(gn):
    S, K = float(np.clip(gn, 0, None).sum()), len(gn)
    f = lambda a: ((1 - a) ** (np.arange(K) + 1)).sum() - S  # noqa: E731
    if S <= 1e-12: return 1.0
    if f(1e-4) < 0: return 1e-4
    lo, hi = 1e-4, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def span(D, mk, first, end, before):
    p = D[mk]['dates'].index(first)
    df = D[mk]['df']
    return df[(df['date'] >= D[mk]['dates'][p - (TW - 1) - before]) & (df['date'] <= end)]


def turnover(env):
    """daily mean of sum_i |w_t,i - w'_{t-1},i| over stocks (cash excluded), all steps of the run."""
    a = np.asarray(env._actions_memory[1:], dtype=np.float64)
    f = np.asarray(env._final_weights[:len(a)], dtype=np.float64)
    return float(np.abs(a[:, 1:] - f[:, 1:]).sum(axis=1).mean())


# ---------------------------------------------------------------- gate (prereg section 2)
def collect_first_batch(model):
    """Replicates the start of PolicyGradientCostGrad.train (episode 1) until the first batch is full;
    returns the buffered experiences without any gradient step."""
    env = model.train_env
    obs = env.reset(); model.train_pvm.reset(); done = False; buf = []
    with contextlib.redirect_stdout(io.StringIO()):
        while not done and len(buf) < model.train_batch_size:
            last_action = model.train_pvm.retrieve()
            action = apply_portfolio_noise(model.train_policy(np.expand_dims(obs, 0), np.expand_dims(last_action, 0)), model.action_noise)
            model.train_pvm.add(action)
            prev_w = np.asarray(env._final_weights[-1], dtype=np.float64)
            obs2, _, done, info = env.step(action)
            buf.append((obs, last_action, np.asarray(info['price_variation']), float(info['trf_mu']), prev_w, np.asarray(action)))
            obs = obs2
    return buf


def cmd_gate(args):
    torch.set_num_threads(2)
    D = load_data()
    rows = []
    for a in ARCH:
        for m in MARKETS:
            for s in SEEDS:
                seed_all(s); _START[0] = 'cash'
                mc = new_model(D, m, a, 'G', FEE); bc = collect_first_batch(mc)
                seed_all(s)
                m0 = new_model(D, m, a, 'G', 0.0); b0 = collect_first_batch(m0)
                same = all(np.array_equal(x[5], y[5]) and np.array_equal(x[4], y[4]) for x, y in zip(bc, b0))
                obs = torch.from_numpy(np.stack([e[0] for e in bc])); la = torch.from_numpy(np.stack([e[1] for e in bc]))
                pv = torch.from_numpy(np.stack([e[2] for e in bc])).double()
                pw = torch.from_numpy(np.stack([e[4] for e in bc])).double()
                trf_c = torch.tensor([e[3] for e in bc], dtype=torch.float64).unsqueeze(1)
                trf_0 = torch.tensor([e[3] for e in b0], dtype=torch.float64).unsqueeze(1)
                pol = mc.train_policy
                mu32 = pol.mu(obs, la)
                mu_base = mu32.detach().double()

                def grad_mu(lossfn):
                    x = mu_base.clone().requires_grad_(True)
                    lossfn(x).backward()
                    return x.grad.detach()
                lossG = lambda c: (lambda x: -torch.mean(torch.log(torch.sum(x * pv * trf_graph(x, pw, c), dim=1))))  # noqa: E731
                lossO = lambda t: (lambda x: -torch.mean(torch.log(torch.sum(x * pv * t, dim=1))))  # noqa: E731
                gGc, gG0 = grad_mu(lossG(FEE)), grad_mu(lossG(0.0))
                gOc, gO0 = grad_mu(lossO(trf_c)), grad_mu(lossO(trf_0))
                rel = lambda g1, g0: float((g1 - g0).norm() / g0.norm())  # noqa: E731

                def rel_param(g1, g0):  # parameter gradient = J^T g_mu (linear in g_mu)
                    def pg(v):
                        pol.zero_grad(); mu32.backward(v.float(), retain_graph=True)
                        return torch.cat([p.grad.detach().double().flatten() for p in pol.parameters() if p.grad is not None])
                    d, b = pg(g1 - g0), pg(g0)
                    return float(d.norm() / b.norm())
                trf_check = float((trf_graph(mu_base, pw, FEE) - trf_c).abs().max())
                r = dict(arch=a, market=m, seed=s, n_batch=len(bc), same_actions_c_vs_0=bool(same),
                         G_rel_grad_mu_f64=rel(gGc, gG0), O_rel_grad_mu_f64=rel(gOc, gO0),
                         G_rel_grad_param=rel_param(gGc, gG0), O_rel_grad_param=rel_param(gOc, gO0),
                         trf_graph_vs_env_maxabs=trf_check,
                         env_trf_mu_min=float(trf_c.min()), env_trf_mu_mean=float(trf_c.mean()))
                rows.append(r)
                print(json.dumps(r), flush=True)
    gmin = min(min(r['G_rel_grad_mu_f64'], r['G_rel_grad_param']) for r in rows)
    res = dict(threshold=GATE_THRESHOLD, rule='G passes iff for all 12 (arch,market,seed) both the float64 relative difference of '
               'the loss gradient w.r.t. the policy output mu (c=0.0025 vs 0) and the corresponding parameter-gradient relative '
               'difference exceed 1e-6', G_min=gmin, O_max=max(max(r['O_rel_grad_mu_f64'], r['O_rel_grad_param']) for r in rows),
               G_pass=bool(gmin > GATE_THRESHOLD), data={k: v['info'] for k, v in D.items()}, rows=rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'gate.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print('GATE', 'PASS' if res['G_pass'] else 'FAIL', 'G_min', gmin, 'O_max', res['O_max'])


# ---------------------------------------------------------------- main run
def run_setting(D, a, m, s, cond, tag):
    MDIR.mkdir(parents=True, exist_ok=True)
    final, ck = MDIR / f'{tag}.pt', MDIR / f'{tag}_ckpt.pt'
    t0 = time.time()
    seed_all(s); _START[0] = 'cash'
    model = new_model(D, m, a, cond)
    if not final.exists():
        ep0 = 0
        if ck.exists():
            c = torch.load(ck, weights_only=False)
            model.train_policy.load_state_dict(c['policy']); model.train_optimizer.load_state_dict(c['opt']); ep0 = c['ep']
            random.setstate(c['rng'][0]); np.random.set_state(c['rng'][1]); torch.set_rng_state(c['rng'][2])
            print(f'{tag}: resume from episode {ep0}', flush=True)
        for ep in range(ep0, EPISODES):
            with contextlib.redirect_stdout(io.StringIO()):
                model.train(1)
            torch.save({'policy': model.train_policy.state_dict(), 'opt': model.train_optimizer.state_dict(), 'ep': ep + 1,
                        'rng': (random.getstate(), np.random.get_state(), torch.get_rng_state())}, ck)
            print(f'{tag}: episode {ep + 1}/{EPISODES} ({time.time() - t0:.0f}s)', flush=True)
        torch.save(model.train_policy.state_dict(), final); ck.unlink()
    t_train = time.time() - t0
    cls, kw = ARCH[a]; pol = cls(**kw, device=device); pol.load_state_dict(torch.load(final))
    ev = new_model(D, m, a, cond)
    # alpha_eff (training span, online off): 20 points, cash vs equal-weight start, 60 days
    trd = sorted(D[m]['train']['date'].unique()); gaps = []
    for p in np.linspace(TW - 1 + W, len(trd) - H - 2, 20).astype(int):
        on = span(D, m, trd[p], trd[p + H], 0)
        _, xe, _ = run(ev, pol, on, FEE, 'ew', False); _, xc, _ = run(ev, pol, on, FEE, 'cash', False)
        k = min(len(xe), len(xc), H); gaps.append(np.abs(xe[:k] - xc[:k]))
    L = min(map(len, gaps)); g = np.mean([q[:L] for q in gaps], axis=0)
    a_eff = alpha_from_gap(g)
    years = {}
    for y, dy in D[m]['years'].items():
        v, x, env = run(ev, pol, dy, FEE, 'cash', False)
        vo, _, _ = run(ev, pol, dy, FEE, 'cash', True, seed=s)
        benv = make_env(dy, FEE, PortfolioOptimizationEnv); benv.reset(); term = False
        with contextlib.redirect_stdout(io.StringIO()):
            while not term:
                _, _, term, _ = benv.step([0] + [1 / D[m]['N']] * D[m]['N'])
        bench = float(np.log(benv._asset_memory['final'][-1] / benv._asset_memory['final'][0]))
        gr = float(np.log(v[-1] / v[0]))
        years[str(y)] = dict(turnover=turnover(env), log_growth=gr, bench_ew_log_growth=bench, excess=gr - bench,
                             mean_exposure=float(x.mean()), online_log_growth=float(np.log(vo[-1] / vo[0])))
    res = dict(tag=tag, cond=cond, arch=a, market=m, seed=s, fee=FEE, alpha_eff=a_eff, gap0=float(g[0]),
               turnover=float(np.mean([r['turnover'] for r in years.values()])), years=years,
               train_seconds=round(t_train), total_seconds=round(time.time() - t0))
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f'{tag}.json.tmp'; tmp.write_text(json.dumps(res, indent=1)); tmp.rename(OUT / f'{tag}.json')
    final.unlink()  # delete checkpoint after evaluation
    print(f'DONE {tag}: alpha_eff={a_eff:.4f} turnover={res["turnover"]:.4f} ({res["total_seconds"]}s)', flush=True)


def cmd_run(args):
    torch.set_num_threads(args.threads)
    ENV_CWD[0] = str(WORK / 'envout' / f'w{args.worker}')
    D = load_data()
    for i, (a, m, s, c) in enumerate(CONFIGS):
        if i % args.nworkers != args.worker:
            continue
        tag = tag_of(a, m, s, c)
        if (OUT / f'{tag}.json').exists():
            continue
        run_setting(D, a, m, s, c, tag)
    print('worker finished', flush=True)


def cmd_launch(args):
    LOGS.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    for w in range(args.nworkers):
        log = open(LOGS / f'worker{w}.log', 'a')
        p = subprocess.Popen(['nohup', sys.executable, str(pathlib.Path(__file__).resolve()), 'run', '--worker', str(w),
                              '--nworkers', str(args.nworkers), '--threads', str(args.threads)],
                             cwd=str(REPO), stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        print(f'worker {w}: pid {p.pid}, log {LOGS / f"worker{w}.log"}')


def cmd_status(args):
    done = [tag_of(*c) for c in CONFIGS if (OUT / f'{tag_of(*c)}.json').exists()]
    print(f'{len(done)}/{len(CONFIGS)} finished'); print('\n'.join(done))


# ---------------------------------------------------------------- judge (prereg section 3)
def cmd_judge(args):
    R = {}
    for c in CONFIGS:
        p = OUT / f'{tag_of(*c)}.json'
        if not p.exists():
            raise SystemExit(f'not finished: {p.name} (judge needs all {len(CONFIGS)} settings)')
        R[c] = json.loads(p.read_text())
    pairs = []
    for a in ARCH:
        for m in MARKETS:
            for s in SEEDS:
                o, g = R[(a, m, s, 'O')], R[(a, m, s, 'G')]
                pairs.append(dict(arch=a, market=m, seed=s, alpha_O=o['alpha_eff'], alpha_G=g['alpha_eff'],
                                  turnover_O=o['turnover'], turnover_G=g['turnover'],
                                  hg1=g['alpha_eff'] < o['alpha_eff'] - 0.05, alpha_G_lt_05=g['alpha_eff'] < 0.5,
                                  hg2=g['turnover'] < 0.9 * o['turnover'],
                                  **{f'{k}_{y}_{cnd}': R[(a, m, s, cnd)]['years'][y][k] for cnd in CONDS
                                     for y in ('2020', '2021', '2022') for k in ('log_growth', 'excess', 'online_log_growth')}))
    P = pd.DataFrame(pairs)
    verdict = lambda k, yes, no, mixed: yes if k >= 9 else (no if k <= 3 else mixed)  # noqa: E731
    k1, k2, k05 = int(P['hg1'].sum()), int(P['hg2'].sum()), int(P['alpha_G_lt_05'].sum())
    res = {'H-G1': dict(count=k1, of=len(P), verdict=verdict(k1, '비용 기울기를 연결하면 관성이 커진다', '커지지 않았다', '엇갈렸다'),
                        alpha_G_lt_0_5=k05),
           'H-G2': dict(count=k2, of=len(P), verdict=verdict(k2, '회전율이 줄었다', '줄지 않았다', '엇갈렸다'))}
    P.to_csv(OUT / 'pairs.csv', index=False)
    (OUT / 'judge.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(P[['arch', 'market', 'seed', 'alpha_O', 'alpha_G', 'hg1', 'turnover_O', 'turnover_G', 'hg2']].round(4).to_string())
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['gate', 'run', 'launch', 'status', 'judge'])
    ap.add_argument('--worker', type=int, default=0)
    ap.add_argument('--nworkers', type=int, default=1)
    ap.add_argument('--threads', type=int, default=1)
    args = ap.parse_args()
    {'gate': cmd_gate, 'run': cmd_run, 'launch': cmd_launch, 'status': cmd_status, 'judge': cmd_judge}[args.cmd](args)
