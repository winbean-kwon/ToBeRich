"""FinRL cost-gradient experiment, extension (pre-registered: notes/finrl_costgrad_ext_prereg.md, 33f5819).

Reuses replication/finrl_costgrad.py (base, unmodified) for data, env, condition G, alpha_eff, turnover.

Conditions (data / architectures / markets / seeds / training settings = base):
  O1  original FinRL PolicyGradient, fee 0.01.
  G1  base condition G (in-graph env TRF cost factor), fee 0.01.
  P   placebo, fee 0.0025: original loss + lambda * mean_batch(sum_i mu_i^2) (sum over all n+1 outputs,
      cash included). lambda is calibrated per setting at init on the first training batch (bisection,
      float64 loss gradients w.r.t. mu mapped to parameters by J^T as in the base gate) so that the relative
      parameter-gradient change ||g(lambda) - g(0)|| / ||g(0)|| equals that setting's G_rel_grad_param in
      replication/finrl_costgrad/gate.json. The penalty is applied in every _gradient_ascent (training and
      online test updates), mirroring how G changes the loss.
  O (0.25%) and G (0.25%) are taken from the base results (not rerun).

Gate (prereg 1): G1 relative gradient difference c=0.01 vs 0 (float64) > 1e-6 in all 12 (checked, like the base
implementation, on both the mu-gradient and the parameter-gradient); P calibration error <= 10% in all 12.

Judge (prereg 2): H-G1', H-G2' on 12 (O1, G1) pairs; H-P counts P settings whose test mean exposure (mean over
2020/2021/2022 of the yearly mean exposure, online off, cash start) is < 0.5, against base O 5/12 and G 1/12.

Commands (repo root, PYTHONPATH=.t3env/pylib python3 replication/finrl_costgrad_ext.py ...):
  gate | run --worker i --nworkers N | launch --nworkers N | status | judge
Outputs: replication/finrl_costgrad_ext/ (per-setting JSON, gate.json, judge.json, pairs.csv).
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import pathlib
import random
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import finrl_costgrad as cg  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

from finrl_po.algorithms import PolicyGradient  # noqa: E402
from finrl_po.env_portfolio_optimization import PortfolioOptimizationEnv  # noqa: E402
from finrl_po.models import MODELS  # noqa: E402

OUT = cg.REPO / 'replication' / 'finrl_costgrad_ext'
BASE_OUT = cg.OUT
FEE_HI, FEE_P = 0.01, 0.0025
CAL_TOL = 0.10
FEE_OF = {'O1': FEE_HI, 'G1': FEE_HI, 'P': FEE_P}
CONDS = ['O1', 'G1', 'P']
CONFIGS = [(a, m, s, c) for s in cg.SEEDS for a in cg.ARCH for m in cg.MARKETS for c in CONDS]
tag_of = cg.tag_of


# ---------------------------------------------------------------- condition P (placebo)
def placebo_penalty(mu):
    """mean over the batch of sum_i mu_i^2 (all n+1 outputs)."""
    return torch.mean(torch.sum(mu ** 2, dim=1))


class PolicyGradientPlacebo(PolicyGradient):
    """Identical to PolicyGradient except the loss adds placebo_lambda * mean(sum mu^2)."""
    placebo_lambda = 0.0

    def _gradient_ascent(self, test=False):
        obs, last_actions, price_variations, trf_mu = (
            next(iter(self.test_dataloader)) if test else next(iter(self.train_dataloader))
        )
        obs = obs.to(self.device)
        last_actions = last_actions.to(self.device)
        price_variations = price_variations.to(self.device)
        trf_mu = trf_mu.unsqueeze(1).to(self.device)
        mu = self.test_policy.mu(obs, last_actions) if test else self.train_policy.mu(obs, last_actions)
        policy_loss = -torch.mean(torch.log(torch.sum(mu * price_variations * trf_mu, dim=1)))
        policy_loss = policy_loss + self.placebo_lambda * placebo_penalty(mu)  # [P]
        if test:
            self.test_policy.zero_grad()
            policy_loss.backward()
            self.test_optimizer.step()
        else:
            self.train_policy.zero_grad()
            policy_loss.backward()
            self.train_optimizer.step()


MODELS['pg_placebo'] = PolicyGradientPlacebo
cg.MODEL_NAME.update({'O1': 'pg', 'G1': 'pg_costgrad', 'P': 'pg_placebo'})


def new_model(D, m, a, cond, lam=0.0):
    model = cg.new_model(D, m, a, cond, FEE_OF[cond])
    if cond == 'P':
        model.placebo_lambda = float(lam)
    return model


# ---------------------------------------------------------------- gate
def batch_tensors(b):
    obs = torch.from_numpy(np.stack([e[0] for e in b])); la = torch.from_numpy(np.stack([e[1] for e in b]))
    pv = torch.from_numpy(np.stack([e[2] for e in b])).double()
    pw = torch.from_numpy(np.stack([e[4] for e in b])).double()
    trf = torch.tensor([e[3] for e in b], dtype=torch.float64).unsqueeze(1)
    return obs, la, pv, pw, trf


def grad_tools(pol, obs, la):
    mu32 = pol.mu(obs, la)
    mu_base = mu32.detach().double()

    def grad_mu(lossfn):
        x = mu_base.clone().requires_grad_(True)
        lossfn(x).backward()
        return x.grad.detach()

    def pgrad(v):  # parameter gradient = J^T v
        pol.zero_grad(); mu32.backward(v.float(), retain_graph=True)
        return torch.cat([p.grad.detach().double().flatten() for p in pol.parameters() if p.grad is not None])
    return mu_base, grad_mu, pgrad


rel = lambda g1, g0: float((g1 - g0).norm() / g0.norm())  # noqa: E731


def cmd_gate(args):
    torch.set_num_threads(2)
    D = cg.load_data()
    base = json.loads((BASE_OUT / 'gate.json').read_text())
    target = {(r['arch'], r['market'], r['seed']): r['G_rel_grad_param'] for r in base['rows']}
    rows = []
    for a in cg.ARCH:
        for m in cg.MARKETS:
            for s in cg.SEEDS:
                # ---- G1: c = 0.01 vs 0 (same procedure as the base gate)
                cg.seed_all(s); cg._START[0] = 'cash'
                mc = cg.new_model(D, m, a, 'G1', FEE_HI); bc = cg.collect_first_batch(mc)
                cg.seed_all(s)
                m0 = cg.new_model(D, m, a, 'G1', 0.0); b0 = cg.collect_first_batch(m0)
                obs, la, pv, pw, trf_c = batch_tensors(bc)
                trf_0 = batch_tensors(b0)[4]
                mu_base, grad_mu, pgrad = grad_tools(mc.train_policy, obs, la)
                lossG = lambda c: (lambda x: -torch.mean(torch.log(torch.sum(x * pv * cg.trf_graph(x, pw, c), dim=1))))  # noqa: E731
                lossO = lambda t: (lambda x: -torch.mean(torch.log(torch.sum(x * pv * t, dim=1))))  # noqa: E731
                gGc, gG0 = grad_mu(lossG(FEE_HI)), grad_mu(lossG(0.0))
                gOc, gO0 = grad_mu(lossO(trf_c)), grad_mu(lossO(trf_0))
                r = dict(arch=a, market=m, seed=s, n_batch=len(bc),
                         G1_rel_grad_mu_f64=rel(gGc, gG0), G1_rel_grad_param=rel(pgrad(gGc), pgrad(gG0)),
                         O1_rel_grad_mu_f64=rel(gOc, gO0), O1_rel_grad_param=rel(pgrad(gOc), pgrad(gO0)),
                         trf_graph_vs_env_maxabs_1pct=float((cg.trf_graph(mu_base, pw, FEE_HI) - trf_c).abs().max()),
                         env_trf_mu_mean_1pct=float(trf_c.mean()), env_trf_mu_min_1pct=float(trf_c.min()))
                # ---- P: lambda calibration at fee 0.0025 on the first training batch
                cg.seed_all(s); cg._START[0] = 'cash'
                mp = new_model(D, m, a, 'P', 0.0); bp = cg.collect_first_batch(mp)
                obs, la, pv, pw, trf_p = batch_tensors(bp)
                mu_base, grad_mu, pgrad = grad_tools(mp.train_policy, obs, la)
                g_orig = grad_mu(lossO(trf_p))
                p0 = pgrad(g_orig)
                lossP = lambda lam: (lambda x: lossO(trf_p)(x) + lam * placebo_penalty(x))  # noqa: E731
                relP = lambda lam: float((pgrad(grad_mu(lossP(lam))) - p0).norm() / p0.norm())  # noqa: E731
                tgt = target[(a, m, s)]
                lo, hi = 0.0, 1e-3
                while relP(hi) < tgt and hi < 1e12:
                    hi *= 2
                for _ in range(80):
                    mid = (lo + hi) / 2
                    lo, hi = (mid, hi) if relP(mid) < tgt else (lo, mid)
                lam = (lo + hi) / 2
                achieved = relP(lam)
                r.update(P_target_G_rel_grad_param=tgt, P_lambda=lam, P_achieved_rel_grad_param=achieved,
                         P_cal_rel_error=abs(achieved - tgt) / tgt, P_rel_grad_mu_f64=rel(grad_mu(lossP(lam)), g_orig),
                         P_same_first_batch_as_base_G=bool(len(bp) == len(bc)))
                rows.append(r)
                print(json.dumps(r), flush=True)
    g1min = min(min(r['G1_rel_grad_mu_f64'], r['G1_rel_grad_param']) for r in rows)
    pmax = max(r['P_cal_rel_error'] for r in rows)
    res = dict(threshold=cg.GATE_THRESHOLD, cal_tol=CAL_TOL,
               rule='G1 passes iff for all 12 both the float64 mu-gradient and the parameter-gradient relative difference '
                    '(c=0.01 vs 0) exceed 1e-6; P passes iff the lambda calibration relative error <= 10% in all 12',
               G1_min=g1min, O1_max=max(max(r['O1_rel_grad_mu_f64'], r['O1_rel_grad_param']) for r in rows),
               G1_pass=bool(g1min > cg.GATE_THRESHOLD), P_cal_err_max=pmax, P_pass=bool(pmax <= CAL_TOL),
               P_lambda_min=min(r['P_lambda'] for r in rows), P_lambda_max=max(r['P_lambda'] for r in rows),
               rows=rows)
    res['pass'] = bool(res['G1_pass'] and res['P_pass'])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'gate.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print('GATE', 'PASS' if res['pass'] else 'FAIL', 'G1_min', g1min, 'O1_max', res['O1_max'], 'P_cal_err_max', pmax,
          'lambda', res['P_lambda_min'], res['P_lambda_max'])


def load_gate():
    p = OUT / 'gate.json'
    if not p.exists():
        raise SystemExit('run gate first')
    g = json.loads(p.read_text())
    if not g['pass']:
        raise SystemExit('gate failed: not running')
    return {(r['arch'], r['market'], r['seed']): r['P_lambda'] for r in g['rows']}


# ---------------------------------------------------------------- main run (= base run_setting with fee/lambda)
def run_setting(D, a, m, s, cond, tag, lam):
    fee = FEE_OF[cond]
    cg.MDIR.mkdir(parents=True, exist_ok=True)
    final, ck = cg.MDIR / f'{tag}.pt', cg.MDIR / f'{tag}_ckpt.pt'
    t0 = time.time()
    cg.seed_all(s); cg._START[0] = 'cash'
    model = new_model(D, m, a, cond, lam)
    if not final.exists():
        ep0 = 0
        if ck.exists():
            c = torch.load(ck, weights_only=False)
            model.train_policy.load_state_dict(c['policy']); model.train_optimizer.load_state_dict(c['opt']); ep0 = c['ep']
            random.setstate(c['rng'][0]); np.random.set_state(c['rng'][1]); torch.set_rng_state(c['rng'][2])
            print(f'{tag}: resume from episode {ep0}', flush=True)
        for ep in range(ep0, cg.EPISODES):
            with contextlib.redirect_stdout(io.StringIO()):
                model.train(1)
            torch.save({'policy': model.train_policy.state_dict(), 'opt': model.train_optimizer.state_dict(), 'ep': ep + 1,
                        'rng': (random.getstate(), np.random.get_state(), torch.get_rng_state())}, ck)
            print(f'{tag}: episode {ep + 1}/{cg.EPISODES} ({time.time() - t0:.0f}s)', flush=True)
        torch.save(model.train_policy.state_dict(), final); ck.unlink()
    t_train = time.time() - t0
    cls, kw = cg.ARCH[a]; pol = cls(**kw, device=cg.device); pol.load_state_dict(torch.load(final))
    ev = new_model(D, m, a, cond, lam)
    trd = sorted(D[m]['train']['date'].unique()); gaps = []
    for p in np.linspace(cg.TW - 1 + cg.W, len(trd) - cg.H - 2, 20).astype(int):
        on = cg.span(D, m, trd[p], trd[p + cg.H], 0)
        _, xe, _ = cg.run(ev, pol, on, fee, 'ew', False); _, xc, _ = cg.run(ev, pol, on, fee, 'cash', False)
        k = min(len(xe), len(xc), cg.H); gaps.append(np.abs(xe[:k] - xc[:k]))
    L = min(map(len, gaps)); g = np.mean([q[:L] for q in gaps], axis=0)
    a_eff = cg.alpha_from_gap(g)
    years = {}
    for y, dy in D[m]['years'].items():
        v, x, env = cg.run(ev, pol, dy, fee, 'cash', False)
        vo, _, _ = cg.run(ev, pol, dy, fee, 'cash', True, seed=s)
        benv = cg.make_env(dy, fee, PortfolioOptimizationEnv); benv.reset(); term = False
        with contextlib.redirect_stdout(io.StringIO()):
            while not term:
                _, _, term, _ = benv.step([0] + [1 / D[m]['N']] * D[m]['N'])
        bench = float(np.log(benv._asset_memory['final'][-1] / benv._asset_memory['final'][0]))
        gr = float(np.log(v[-1] / v[0]))
        years[str(y)] = dict(turnover=cg.turnover(env), log_growth=gr, bench_ew_log_growth=bench, excess=gr - bench,
                             mean_exposure=float(x.mean()), online_log_growth=float(np.log(vo[-1] / vo[0])))
    res = dict(tag=tag, cond=cond, arch=a, market=m, seed=s, fee=fee, placebo_lambda=lam if cond == 'P' else None,
               alpha_eff=a_eff, gap0=float(g[0]),
               turnover=float(np.mean([r['turnover'] for r in years.values()])),
               mean_exposure=float(np.mean([r['mean_exposure'] for r in years.values()])), years=years,
               train_seconds=round(t_train), total_seconds=round(time.time() - t0))
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f'{tag}.json.tmp'; tmp.write_text(json.dumps(res, indent=1)); tmp.rename(OUT / f'{tag}.json')
    final.unlink()  # delete checkpoint after evaluation
    print(f'DONE {tag}: alpha_eff={a_eff:.4f} turnover={res["turnover"]:.4f} exposure={res["mean_exposure"]:.3f} '
          f'({res["total_seconds"]}s)', flush=True)


def cmd_run(args):
    torch.set_num_threads(args.threads)
    lams = load_gate()
    cg.ENV_CWD[0] = str(cg.WORK / 'envout' / f'ext_w{args.worker}')
    D = cg.load_data()
    for i, (a, m, s, c) in enumerate(CONFIGS):
        if i % args.nworkers != args.worker:
            continue
        tag = tag_of(a, m, s, c)
        if (OUT / f'{tag}.json').exists():
            continue
        run_setting(D, a, m, s, c, tag, lams[(a, m, s)] if c == 'P' else 0.0)
    print('worker finished', flush=True)


def cmd_launch(args):
    load_gate()
    cg.LOGS.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    for w in range(args.nworkers):
        lp = cg.LOGS / f'ext_worker{w}.log'
        log = open(lp, 'a')
        p = subprocess.Popen(['nohup', sys.executable, str(pathlib.Path(__file__).resolve()), 'run', '--worker', str(w),
                              '--nworkers', str(args.nworkers), '--threads', str(args.threads)],
                             cwd=str(cg.REPO), stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        print(f'worker {w}: pid {p.pid}, log {lp}')


def cmd_status(args):
    done = [tag_of(*c) for c in CONFIGS if (OUT / f'{tag_of(*c)}.json').exists()]
    print(f'{len(done)}/{len(CONFIGS)} finished'); print('\n'.join(done))


# ---------------------------------------------------------------- judge (prereg 2)
def exposure(r):
    return float(np.mean([v['mean_exposure'] for v in r['years'].values()]))


def excess3(r):
    return float(sum(v['excess'] for v in r['years'].values()))


def cmd_judge(args):
    R = {}
    for c in CONFIGS:
        p = OUT / f'{tag_of(*c)}.json'
        if not p.exists():
            raise SystemExit(f'not finished: {p.name} (judge needs all {len(CONFIGS)} settings)')
        R[c] = json.loads(p.read_text())
    for a in cg.ARCH:
        for m in cg.MARKETS:
            for s in cg.SEEDS:
                for c in ('O', 'G'):
                    R[(a, m, s, c)] = json.loads((BASE_OUT / f'{tag_of(a, m, s, c)}.json').read_text())
    rows = []
    for a in cg.ARCH:
        for m in cg.MARKETS:
            for s in cg.SEEDS:
                o, g, pl = R[(a, m, s, 'O1')], R[(a, m, s, 'G1')], R[(a, m, s, 'P')]
                rows.append(dict(arch=a, market=m, seed=s, alpha_O1=o['alpha_eff'], alpha_G1=g['alpha_eff'],
                                 turnover_O1=o['turnover'], turnover_G1=g['turnover'],
                                 hg1p=g['alpha_eff'] < o['alpha_eff'] - 0.05, alpha_G1_lt_05=g['alpha_eff'] < 0.5,
                                 hg2p=g['turnover'] < 0.9 * o['turnover'], lambda_P=pl['placebo_lambda'],
                                 **{f'exposure_{c}': exposure(R[(a, m, s, c)]) for c in ('O', 'G', 'O1', 'G1', 'P')},
                                 **{f'excess3_{c}': excess3(R[(a, m, s, c)]) for c in ('O', 'G', 'O1', 'G1', 'P')},
                                 turnover_P=pl['turnover'], alpha_P=pl['alpha_eff']))
    P = pd.DataFrame(rows)
    verdict = lambda k, yes, no, mixed: yes if k >= 9 else (no if k <= 3 else mixed)  # noqa: E731
    k1, k2, k05 = int(P['hg1p'].sum()), int(P['hg2p'].sum()), int(P['alpha_G1_lt_05'].sum())
    nlow = {c: int((P[f'exposure_{c}'] < 0.5).sum()) for c in ('O', 'G', 'O1', 'G1', 'P')}
    kp = nlow['P']
    vp = ('위약도 같은 변화를 낸다 — 퇴화 감소는 비용 항에 특정되지 않는다' if kp <= 1 else
          '위약은 그 변화를 내지 않는다 — 비용 항 특정과 모순되지 않는다' if kp >= 4 else '엇갈렸다')
    desc = {}
    for c in ('O', 'G', 'O1', 'G1', 'P'):
        tv = [R[(a, m, s, c)]['turnover'] for a in cg.ARCH for m in cg.MARKETS for s in cg.SEEDS]
        al = [R[(a, m, s, c)]['alpha_eff'] for a in cg.ARCH for m in cg.MARKETS for s in cg.SEEDS]
        desc[c] = dict(turnover_median=float(np.median(tv)), turnover_mean=float(np.mean(tv)),
                       exposure_mean=float(P[f'exposure_{c}'].mean()), exposure_lt_05=nlow[c],
                       excess3_median=float(P[f'excess3_{c}'].median()), excess3_mean=float(P[f'excess3_{c}'].mean()),
                       alpha_min=float(min(al)), alpha_max=float(max(al)))
    res = {"H-G1'": dict(count=k1, of=len(P), verdict=verdict(k1, '1%에서는 관성이 커진다', '커지지 않았다', '엇갈렸다'),
                         alpha_G1_lt_0_5=k05),
           "H-G2'": dict(count=k2, of=len(P), verdict=verdict(k2, '줄었다', '줄지 않았다', '엇갈렸다')),
           'H-P': dict(count_P_exposure_lt_0_5=kp, of=len(P), base_O=nlow['O'], base_G=nlow['G'], verdict=vp,
                       exposure_definition='mean over 2020/2021/2022 of the yearly mean test exposure (online off, cash start)'),
           'descriptive': desc}
    P.to_csv(OUT / 'pairs.csv', index=False)
    (OUT / 'judge.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(P[['arch', 'market', 'seed', 'alpha_O1', 'alpha_G1', 'hg1p', 'turnover_O1', 'turnover_G1', 'hg2p',
             'exposure_O', 'exposure_G', 'exposure_P']].round(4).to_string())
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['gate', 'run', 'launch', 'status', 'judge'])
    ap.add_argument('--worker', type=int, default=0)
    ap.add_argument('--nworkers', type=int, default=1)
    ap.add_argument('--threads', type=int, default=1)
    args = ap.parse_args()
    {'gate': cmd_gate, 'run': cmd_run, 'launch': cmd_launch, 'status': cmd_status, 'judge': cmd_judge}[args.cmd](args)
