"""FinRL cost-gradient experiment, 3x training (pre-registered: notes/finrl_costgrad_long_prereg.md, cc9dc14).

Reuses replication/finrl_costgrad.py (base) and replication/finrl_costgrad_ext.py (extension), both unmodified:
data, env, condition G (in-graph TRF cost factor), alpha_eff, turnover, run_setting and the gate gradient tools.

Conditions (everything = extension conditions O1 / G1 except the episode count):
  O1L  original FinRL PolicyGradient, fee 0.01, 120 episodes.
  G1L  base condition G (in-graph env TRF cost factor), fee 0.01, 120 episodes.
Settings: market BR10 x {EIIE, EI3} x seeds {0, 1, 2} -> 6 (O1L, G1L) pairs.

Data: WORK/data/raw_BR10.csv (cleaned copy). Workers only READ it: the script refuses to start if it is missing
(no download, no rewrite), loads only BR10, and records its md5 in every output.

Gate (prereg): G1L initial relative gradient difference c=0.01 vs 0 (float64) > 1e-6 in all 6 (same computation
as the extension gate: both the mu-gradient and the parameter-gradient).

Judge (prereg; 6 pairs):
  H-G1L: #pairs alpha_eff(G1L) < alpha_eff(O1L) - 0.05; >=5 '긴 학습에서는 관성이 커진다', <=1 '커지지 않았다', else '엇갈렸다'.
  H-G2L: #pairs turnover(G1L) < 0.9 * turnover(O1L); >=5 '줄었다', <=1 '줄지 않았다', else '엇갈렸다'.
  Auxiliary (descriptive): exposure, 3-year excess over equal weight, comparison with 40-episode O1/G1 BR10.

Commands (repo root, PYTHONPATH=.t3env/pylib python3 replication/finrl_costgrad_long.py ...):
  gate | run --worker i --nworkers N | launch --nworkers N | status | judge
Outputs: replication/finrl_costgrad_long/ (per-setting JSON, gate.json, judge.json, pairs.csv).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import finrl_costgrad as cg  # noqa: E402
import finrl_costgrad_ext as ext  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

OUT = cg.REPO / 'replication' / 'finrl_costgrad_long'
EXT_OUT = ext.OUT
FEE = 0.01
EPISODES_LONG = 120
MARKET = 'BR10'
CONDS = ['O1L', 'G1L']
CONFIGS = [(a, MARKET, s, c) for s in cg.SEEDS for a in cg.ARCH for c in CONDS]
tag_of = cg.tag_of
RAW = cg.DATA_DIR / f'raw_{MARKET}.csv'

# condition wiring (module-level registries of the unmodified base/extension code)
cg.MODEL_NAME.update({'O1L': 'pg', 'G1L': 'pg_costgrad'})
ext.FEE_OF.update({'O1L': FEE, 'G1L': FEE})


def data_md5():
    return hashlib.md5(RAW.read_bytes()).hexdigest()


def load_br10():
    """Read-only load of the existing cleaned BR10 cache (cg.load_data restricted to BR10)."""
    if not RAW.exists():
        raise SystemExit(f'missing {RAW}: refusing to download or rewrite')
    before = (RAW.stat().st_mtime_ns, data_md5())
    saved = cg.MARKETS
    cg.MARKETS = {MARKET: saved[MARKET]}
    try:
        D = cg.load_data()
    finally:
        cg.MARKETS = saved
    if (RAW.stat().st_mtime_ns, data_md5()) != before:
        raise SystemExit('data cache changed during load')
    return D, before[1]


# ---------------------------------------------------------------- gate
def cmd_gate(args):
    torch.set_num_threads(args.threads)
    D, md5 = load_br10()
    rows = []
    for a in cg.ARCH:
        for s in cg.SEEDS:
            cg.seed_all(s); cg._START[0] = 'cash'
            mc = cg.new_model(D, MARKET, a, 'G1L', FEE); bc = cg.collect_first_batch(mc)
            cg.seed_all(s)
            m0 = cg.new_model(D, MARKET, a, 'G1L', 0.0); b0 = cg.collect_first_batch(m0)
            obs, la, pv, pw, trf_c = ext.batch_tensors(bc)
            trf_0 = ext.batch_tensors(b0)[4]
            mu_base, grad_mu, pgrad = ext.grad_tools(mc.train_policy, obs, la)
            lossG = lambda c: (lambda x: -torch.mean(torch.log(torch.sum(x * pv * cg.trf_graph(x, pw, c), dim=1))))  # noqa: E731
            lossO = lambda t: (lambda x: -torch.mean(torch.log(torch.sum(x * pv * t, dim=1))))  # noqa: E731
            gGc, gG0 = grad_mu(lossG(FEE)), grad_mu(lossG(0.0))
            gOc, gO0 = grad_mu(lossO(trf_c)), grad_mu(lossO(trf_0))
            r = dict(arch=a, market=MARKET, seed=s, n_batch=len(bc),
                     G1L_rel_grad_mu_f64=ext.rel(gGc, gG0), G1L_rel_grad_param=ext.rel(pgrad(gGc), pgrad(gG0)),
                     O1L_rel_grad_mu_f64=ext.rel(gOc, gO0), O1L_rel_grad_param=ext.rel(pgrad(gOc), pgrad(gO0)),
                     trf_graph_vs_env_maxabs_1pct=float((cg.trf_graph(mu_base, pw, FEE) - trf_c).abs().max()))
            rows.append(r)
            print(json.dumps(r), flush=True)
    gmin = min(min(r['G1L_rel_grad_mu_f64'], r['G1L_rel_grad_param']) for r in rows)
    res = dict(threshold=cg.GATE_THRESHOLD, data_md5=md5,
               rule='passes iff for all 6 both the float64 mu-gradient and the parameter-gradient relative difference '
                    '(c=0.01 vs 0) of G1L exceed 1e-6',
               G1L_min=gmin, O1L_max=max(max(r['O1L_rel_grad_mu_f64'], r['O1L_rel_grad_param']) for r in rows),
               rows=rows)
    res['pass'] = bool(gmin > cg.GATE_THRESHOLD)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'gate.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print('GATE', 'PASS' if res['pass'] else 'FAIL', 'G1L_min', gmin, 'O1L_max', res['O1L_max'])


def check_gate():
    p = OUT / 'gate.json'
    if not p.exists():
        raise SystemExit('run gate first')
    if not json.loads(p.read_text())['pass']:
        raise SystemExit('gate failed: not running')


# ---------------------------------------------------------------- run (= extension run_setting, 120 episodes)
def cmd_run(args):
    torch.set_num_threads(args.threads)
    check_gate()
    cg.EPISODES = EPISODES_LONG          # read at call time by ext.run_setting
    ext.OUT = OUT                        # ext.run_setting writes to its module-level OUT
    cg.ENV_CWD[0] = str(cg.WORK / 'envout' / f'long_w{args.worker}')
    D, md5 = load_br10()
    for i, (a, m, s, c) in enumerate(CONFIGS):
        if i % args.nworkers != args.worker:
            continue
        tag = tag_of(a, m, s, c)
        if (OUT / f'{tag}.json').exists():
            continue
        ext.run_setting(D, a, m, s, c, tag, 0.0)   # resumes from WORK/models/<tag>_ckpt.pt if present
        p = OUT / f'{tag}.json'
        r = json.loads(p.read_text()); r.update(episodes=EPISODES_LONG, data_md5=md5)
        tmp = OUT / f'{tag}.json.tmp'; tmp.write_text(json.dumps(r, indent=1)); tmp.rename(p)
    print('worker finished', flush=True)


def cmd_launch(args):
    check_gate()
    load_br10()  # verify the cache once before starting workers
    cg.LOGS.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(OMP_NUM_THREADS=str(args.threads), MKL_NUM_THREADS=str(args.threads))
    for w in range(args.nworkers):
        lp = cg.LOGS / f'long_worker{w}.log'
        log = open(lp, 'a')
        p = subprocess.Popen(['nohup', sys.executable, str(pathlib.Path(__file__).resolve()), 'run', '--worker', str(w),
                              '--nworkers', str(args.nworkers), '--threads', str(args.threads)],
                             cwd=str(cg.REPO), stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        print(f'worker {w}: pid {p.pid}, log {lp}')


def cmd_status(args):
    done = [tag_of(*c) for c in CONFIGS if (OUT / f'{tag_of(*c)}.json').exists()]
    print(f'{len(done)}/{len(CONFIGS)} finished'); print('\n'.join(done))


# ---------------------------------------------------------------- judge (prereg)
def cmd_judge(args):
    R = {}
    for c in CONFIGS:
        p = OUT / f'{tag_of(*c)}.json'
        if not p.exists():
            raise SystemExit(f'not finished: {p.name} (judge needs all {len(CONFIGS)} settings)')
        R[c] = json.loads(p.read_text())
        assert R[c]['episodes'] == EPISODES_LONG and R[c]['fee'] == FEE
    for a in cg.ARCH:
        for s in cg.SEEDS:
            for c in ('O1', 'G1'):
                R[(a, MARKET, s, c)] = json.loads((EXT_OUT / f'{tag_of(a, MARKET, s, c)}.json').read_text())
    rows = []
    for a in cg.ARCH:
        for s in cg.SEEDS:
            o, g = R[(a, MARKET, s, 'O1L')], R[(a, MARKET, s, 'G1L')]
            rows.append(dict(arch=a, market=MARKET, seed=s,
                             alpha_O1L=o['alpha_eff'], alpha_G1L=g['alpha_eff'],
                             turnover_O1L=o['turnover'], turnover_G1L=g['turnover'],
                             hg1l=g['alpha_eff'] < o['alpha_eff'] - 0.05,
                             hg2l=g['turnover'] < 0.9 * o['turnover'],
                             **{f'alpha_{c}': R[(a, MARKET, s, c)]['alpha_eff'] for c in ('O1', 'G1')},
                             **{f'turnover_{c}': R[(a, MARKET, s, c)]['turnover'] for c in ('O1', 'G1')},
                             **{f'exposure_{c}': ext.exposure(R[(a, MARKET, s, c)]) for c in ('O1L', 'G1L', 'O1', 'G1')},
                             **{f'excess3_{c}': ext.excess3(R[(a, MARKET, s, c)]) for c in ('O1L', 'G1L', 'O1', 'G1')}))
    P = pd.DataFrame(rows)
    verdict = lambda k, yes, no: yes if k >= 5 else (no if k <= 1 else '엇갈렸다')  # noqa: E731
    k1, k2 = int(P['hg1l'].sum()), int(P['hg2l'].sum())
    k1_40 = int((P['alpha_G1'] < P['alpha_O1'] - 0.05).sum())
    k2_40 = int((P['turnover_G1'] < 0.9 * P['turnover_O1']).sum())
    desc = {}
    for c in ('O1L', 'G1L', 'O1', 'G1'):
        desc[c] = dict(alpha_median=float(P[f'alpha_{c}'].median()), alpha_min=float(P[f'alpha_{c}'].min()),
                       alpha_max=float(P[f'alpha_{c}'].max()),
                       turnover_median=float(P[f'turnover_{c}'].median()), turnover_mean=float(P[f'turnover_{c}'].mean()),
                       exposure_mean=float(P[f'exposure_{c}'].mean()),
                       exposure_lt_05=int((P[f'exposure_{c}'] < 0.5).sum()),
                       excess3_median=float(P[f'excess3_{c}'].median()), excess3_mean=float(P[f'excess3_{c}'].mean()))
    res = {'H-G1L': dict(count=k1, of=len(P), verdict=verdict(k1, '긴 학습에서는 관성이 커진다', '커지지 않았다')),
           'H-G2L': dict(count=k2, of=len(P), verdict=verdict(k2, '줄었다', '줄지 않았다')),
           'descriptive': desc,
           'comparison_40ep_same_pairs': dict(hg1_count_40ep=k1_40, hg2_count_40ep=k2_40, of=len(P),
                                              note='same rules applied to extension O1/G1 BR10 (40 episodes); descriptive')}
    P.to_csv(OUT / 'pairs.csv', index=False)
    (OUT / 'judge.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(P[['arch', 'seed', 'alpha_O1L', 'alpha_G1L', 'hg1l', 'turnover_O1L', 'turnover_G1L', 'hg2l',
             'alpha_O1', 'alpha_G1', 'turnover_O1', 'turnover_G1', 'exposure_O1L', 'exposure_G1L']].round(4).to_string())
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['gate', 'run', 'launch', 'status', 'judge'])
    ap.add_argument('--worker', type=int, default=0)
    ap.add_argument('--nworkers', type=int, default=1)
    ap.add_argument('--threads', type=int, default=1)
    args = ap.parse_args()
    {'gate': cmd_gate, 'run': cmd_run, 'launch': cmd_launch, 'status': cmd_status, 'judge': cmd_judge}[args.cmd](args)
