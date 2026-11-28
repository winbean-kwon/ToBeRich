"""FinRL cost-gradient experiment, learning rates 0.001 and 0.03 (pre-registered: notes/finrl_costgrad_lr_prereg.md, 687b043).

Reuses replication/finrl_costgrad.py (base), replication/finrl_costgrad_ext.py (extension) and the read-only data
handling of replication/finrl_costgrad_long.py, all unmodified. Only cg.LR changes (read by cg.new_model at call time).

Conditions (= extension O1 / G1 at fee 0.01 and 40 episodes, learning rate per run):
  O1_lr<x>  original FinRL PolicyGradient, fee 0.01, 40 episodes, lr x.
  G1_lr<x>  base condition G (in-graph env TRF cost factor), fee 0.01, 40 episodes, lr x.
  x in {0.001, 0.03} -> tags O1_lr0p001_*, G1_lr0p001_*, O1_lr0p03_*, G1_lr0p03_* (no collision with earlier runs;
  checkpoints WORK/models/<tag>_ckpt.pt are therefore distinct too).
Settings: market BR10 x {EIIE, EI3} x seeds {0, 1, 2} x 2 learning rates -> 24 runs, 6 (O1, G1) pairs per lr.

Data: WORK/data/raw_BR10.csv, the same file as the 120-episode run (md5 must equal LONG_MD5). Read only: the script
refuses to start if it is missing (no download, no rewrite) and checks md5 + mtime before/after loading.

Gate (prereg; per learning rate): G1 initial relative gradient difference c=0.01 vs 0 (float64) > 1e-6 in all 6
(same computation as the extension / long gates: mu-gradient and parameter-gradient).

Divergence (prereg): a run whose trained parameters or evaluation outputs (alpha_eff, turnover, exposure) are not
finite is recorded as '발산' (JSON with diverged=true) and its pair is excluded; the count thresholds stay as written
(>=5 / <=1 of the 6 pairs), they are not rescaled to the remaining pairs.

Judge (prereg; per learning rate, 6 pairs):
  H-G1R: #pairs alpha_eff(G1) < alpha_eff(O1) - 0.05; >=5 '이 학습률에서는 관성이 커진다', <=1 '커지지 않았다', else '엇갈렸다'.
  H-G2R: #pairs turnover(G1) < 0.9 * turnover(O1);    >=5 '줄었다', <=1 '줄지 않았다', else '엇갈렸다'.
  Auxiliary (descriptive, not verdicts): turnover comparison restricted to pairs with exposure >= 0.9 in both
  conditions; exposure; 3-year excess over equal weight; comparison with the lr 0.01 extension O1/G1 BR10 pairs.

Commands (repo root, PYTHONPATH=.t3env/pylib python3 replication/finrl_costgrad_lr.py ...):
  gate --lr 0.001 | gate --lr 0.03 | run --worker i --nworkers N | launch --nworkers N | status | judge
Outputs: replication/finrl_costgrad_lr/ (per-run JSON, gate_lr*.json, judge.json, pairs.csv).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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

OUT = cg.REPO / 'replication' / 'finrl_costgrad_lr'
EXT_OUT = ext.OUT
FEE = 0.01
EPISODES = 40
MARKET = 'BR10'
LRS = [0.001, 0.03]
LR_BASE = 0.01
LONG_MD5 = 'e595fc39b7f398104dbb212c5b0bfa3f'   # data_md5 recorded in replication/finrl_costgrad_long/*.json
RAW = cg.DATA_DIR / f'raw_{MARKET}.csv'
tag_of = cg.tag_of


def lr_tag(lr):
    return f'lr{lr:g}'.replace('.', 'p')


def cond_of(base, lr):
    return f'{base}_{lr_tag(lr)}'


LR_OF, BASE_OF = {}, {}
for _lr in LRS:
    for _b in ('O1', 'G1'):
        _c = cond_of(_b, _lr)
        LR_OF[_c], BASE_OF[_c] = _lr, _b
        cg.MODEL_NAME[_c] = cg.MODEL_NAME[_b]   # O1 -> 'pg', G1 -> 'pg_costgrad'
        ext.FEE_OF[_c] = FEE
CONFIGS = [(a, MARKET, s, cond_of(b, lr)) for lr in LRS for s in cg.SEEDS for a in cg.ARCH for b in ('O1', 'G1')]


def data_md5():
    return hashlib.md5(RAW.read_bytes()).hexdigest()


def load_br10():
    """Read-only load of the existing cleaned BR10 cache (cg.load_data restricted to BR10)."""
    if not RAW.exists():
        raise SystemExit(f'missing {RAW}: refusing to download or rewrite')
    before = (RAW.stat().st_mtime_ns, data_md5())
    if before[1] != LONG_MD5:
        raise SystemExit(f'data md5 {before[1]} != long-run md5 {LONG_MD5}')
    saved = cg.MARKETS
    cg.MARKETS = {MARKET: saved[MARKET]}
    try:
        D = cg.load_data()
    finally:
        cg.MARKETS = saved
    if (RAW.stat().st_mtime_ns, data_md5()) != before:
        raise SystemExit('data cache changed during load')
    return D, before[1]


def gate_path(lr):
    return OUT / f'gate_{lr_tag(lr)}.json'


# ---------------------------------------------------------------- gate (per learning rate)
def cmd_gate(args):
    lr = args.lr
    if lr not in LRS:
        raise SystemExit(f'lr must be one of {LRS}')
    torch.set_num_threads(args.threads)
    cg.LR = lr
    D, md5 = load_br10()
    c = cond_of('G1', lr)
    rows = []
    for a in cg.ARCH:
        for s in cg.SEEDS:
            cg.seed_all(s); cg._START[0] = 'cash'
            mc = cg.new_model(D, MARKET, a, c, FEE); bc = cg.collect_first_batch(mc)
            assert mc.train_optimizer.param_groups[0]['lr'] == lr
            cg.seed_all(s)
            m0 = cg.new_model(D, MARKET, a, c, 0.0); b0 = cg.collect_first_batch(m0)
            obs, la, pv, pw, trf_c = ext.batch_tensors(bc)
            trf_0 = ext.batch_tensors(b0)[4]
            mu_base, grad_mu, pgrad = ext.grad_tools(mc.train_policy, obs, la)
            lossG = lambda cc: (lambda x: -torch.mean(torch.log(torch.sum(x * pv * cg.trf_graph(x, pw, cc), dim=1))))  # noqa: E731
            lossO = lambda t: (lambda x: -torch.mean(torch.log(torch.sum(x * pv * t, dim=1))))  # noqa: E731
            gGc, gG0 = grad_mu(lossG(FEE)), grad_mu(lossG(0.0))
            gOc, gO0 = grad_mu(lossO(trf_c)), grad_mu(lossO(trf_0))
            r = dict(arch=a, market=MARKET, seed=s, lr=lr, n_batch=len(bc),
                     G1_rel_grad_mu_f64=ext.rel(gGc, gG0), G1_rel_grad_param=ext.rel(pgrad(gGc), pgrad(gG0)),
                     O1_rel_grad_mu_f64=ext.rel(gOc, gO0), O1_rel_grad_param=ext.rel(pgrad(gOc), pgrad(gO0)),
                     trf_graph_vs_env_maxabs_1pct=float((cg.trf_graph(mu_base, pw, FEE) - trf_c).abs().max()))
            rows.append(r)
            print(json.dumps(r), flush=True)
    gmin = min(min(r['G1_rel_grad_mu_f64'], r['G1_rel_grad_param']) for r in rows)
    res = dict(lr=lr, threshold=cg.GATE_THRESHOLD, data_md5=md5,
               rule='passes iff for all 6 both the float64 mu-gradient and the parameter-gradient relative difference '
                    '(c=0.01 vs 0) of G1 exceed 1e-6',
               G1_min=gmin, O1_max=max(max(r['O1_rel_grad_mu_f64'], r['O1_rel_grad_param']) for r in rows),
               rows=rows)
    res['pass'] = bool(gmin > cg.GATE_THRESHOLD)
    OUT.mkdir(parents=True, exist_ok=True)
    gate_path(lr).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print('GATE lr', lr, 'PASS' if res['pass'] else 'FAIL', 'G1_min', gmin, 'O1_max', res['O1_max'])


def check_gate(lr):
    p = gate_path(lr)
    if not p.exists():
        raise SystemExit(f'run gate --lr {lr} first')
    if not json.loads(p.read_text())['pass']:
        raise SystemExit(f'gate lr {lr} failed: not running')


# ---------------------------------------------------------------- divergence detection
class Diverged(Exception):
    pass


def _finite_state(path):
    sd = torch.load(path, weights_only=False)
    sd = sd['policy'] if isinstance(sd, dict) and 'policy' in sd else sd
    return all(bool(torch.isfinite(v).all()) for v in sd.values() if torch.is_tensor(v) and v.is_floating_point())


_CUR = {}
_orig_new_model = ext.new_model


def _checked_new_model(D, m, a, cond, lam=0.0):
    """Wraps ext.new_model (looked up as a module global by ext.run_setting): verifies the learning rate and,
    once the trained policy exists (the evaluation model is built after it is saved), that its parameters are finite."""
    model = _orig_new_model(D, m, a, cond, lam)
    assert model.train_optimizer.param_groups[0]['lr'] == LR_OF[cond], 'learning rate not applied'
    final = cg.MDIR / f'{_CUR["tag"]}.pt'
    if final.exists() and not _finite_state(final):
        raise Diverged('non-finite trained parameters')
    return model


ext.new_model = _checked_new_model


def write_json(p, r):
    tmp = p.with_suffix('.json.tmp'); tmp.write_text(json.dumps(r, indent=1)); tmp.rename(p)


def record_divergence(a, s, c, tag, reason, md5):
    r = dict(tag=tag, cond=c, base_cond=BASE_OF[c], arch=a, market=MARKET, seed=s, fee=FEE, lr=LR_OF[c],
             episodes=EPISODES, data_md5=md5, diverged=True, reason=reason)
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / f'{tag}.json', r)
    for q in (cg.MDIR / f'{tag}.pt', cg.MDIR / f'{tag}_ckpt.pt'):
        if q.exists():
            q.unlink()
    print(f'DIVERGED {tag}: {reason}', flush=True)


# ---------------------------------------------------------------- run (= extension run_setting, lr per run)
def cmd_run(args):
    torch.set_num_threads(args.threads)
    for lr in LRS:
        check_gate(lr)
    cg.EPISODES = EPISODES               # read at call time by ext.run_setting
    ext.OUT = OUT                        # ext.run_setting writes to its module-level OUT
    cg.ENV_CWD[0] = str(cg.WORK / 'envout' / f'lr_w{args.worker}')
    D, md5 = load_br10()
    for i, (a, m, s, c) in enumerate(CONFIGS):
        if i % args.nworkers != args.worker:
            continue
        tag = tag_of(a, m, s, c)
        if (OUT / f'{tag}.json').exists():
            continue
        cg.LR = LR_OF[c]                 # read at call time by cg.new_model
        _CUR['tag'] = tag
        try:
            ext.run_setting(D, a, m, s, c, tag, 0.0)   # resumes from WORK/models/<tag>_ckpt.pt if present
        except Diverged as e:
            record_divergence(a, s, c, tag, str(e), md5); continue
        except Exception as e:
            ck = cg.MDIR / f'{tag}_ckpt.pt'
            if ck.exists() and not _finite_state(ck):
                record_divergence(a, s, c, tag, f'non-finite parameters during training ({type(e).__name__}: {e})', md5)
                continue
            raise
        p = OUT / f'{tag}.json'
        r = json.loads(p.read_text())
        r.update(episodes=EPISODES, lr=LR_OF[c], base_cond=BASE_OF[c], data_md5=md5, diverged=False)
        vals = [r['alpha_eff'], r['gap0'], r['turnover'], r['mean_exposure']] + [v for y in r['years'].values() for v in y.values()]
        if not all(math.isfinite(v) for v in vals):
            r.update(diverged=True, reason='non-finite evaluation output')
            print(f'DIVERGED {tag}: non-finite evaluation output', flush=True)
        write_json(p, r)
    print('worker finished', flush=True)


def cmd_launch(args):
    for lr in LRS:
        check_gate(lr)
    load_br10()  # verify the cache once before starting workers
    cg.LOGS.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(OMP_NUM_THREADS=str(args.threads), MKL_NUM_THREADS=str(args.threads))
    for w in range(args.nworkers):
        lp = cg.LOGS / f'lr_worker{w}.log'
        log = open(lp, 'a')
        p = subprocess.Popen(['nohup', sys.executable, str(pathlib.Path(__file__).resolve()), 'run', '--worker', str(w),
                              '--nworkers', str(args.nworkers), '--threads', str(args.threads)],
                             cwd=str(cg.REPO), stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        print(f'worker {w}: pid {p.pid}, log {lp}')


def cmd_status(args):
    done = [tag_of(*c) for c in CONFIGS if (OUT / f'{tag_of(*c)}.json').exists()]
    print(f'{len(done)}/{len(CONFIGS)} finished'); print('\n'.join(done))


# ---------------------------------------------------------------- judge (prereg)
def verdict(k, yes, no):
    return yes if k >= 5 else (no if k <= 1 else '엇갈렸다')


def cmd_judge(args):
    R = {}
    for c in CONFIGS:
        p = OUT / f'{tag_of(*c)}.json'
        if not p.exists():
            raise SystemExit(f'not finished: {p.name} (judge needs all {len(CONFIGS)} runs)')
        R[c] = json.loads(p.read_text())
        assert R[c]['episodes'] == EPISODES and R[c]['fee'] == FEE and R[c]['lr'] == LR_OF[c[3]]
        assert R[c]['data_md5'] == LONG_MD5
    E = {(a, s, b): json.loads((EXT_OUT / f'{tag_of(a, MARKET, s, b)}.json').read_text())
         for a in cg.ARCH for s in cg.SEEDS for b in ('O1', 'G1')}
    rows = []
    for lr in LRS:
        for a in cg.ARCH:
            for s in cg.SEEDS:
                o, g = R[(a, MARKET, s, cond_of('O1', lr))], R[(a, MARKET, s, cond_of('G1', lr))]
                eo, eg = E[(a, s, 'O1')], E[(a, s, 'G1')]
                row = dict(lr=lr, arch=a, market=MARKET, seed=s, diverged_O1=o['diverged'], diverged_G1=g['diverged'],
                           alpha_O1_lr01=eo['alpha_eff'], alpha_G1_lr01=eg['alpha_eff'],
                           turnover_O1_lr01=eo['turnover'], turnover_G1_lr01=eg['turnover'],
                           exposure_O1_lr01=ext.exposure(eo), exposure_G1_lr01=ext.exposure(eg))
                valid = not (o['diverged'] or g['diverged'])
                row['valid'] = valid
                if valid:
                    row.update(alpha_O1=o['alpha_eff'], alpha_G1=g['alpha_eff'],
                               turnover_O1=o['turnover'], turnover_G1=g['turnover'],
                               hg1r=g['alpha_eff'] < o['alpha_eff'] - 0.05,
                               hg2r=g['turnover'] < 0.9 * o['turnover'],
                               exposure_O1=ext.exposure(o), exposure_G1=ext.exposure(g),
                               excess3_O1=ext.excess3(o), excess3_G1=ext.excess3(g))
                rows.append(row)
    P = pd.DataFrame(rows)
    res = {'note': 'diverged pairs are excluded; thresholds stay >=5 / <=1 of 6 (not rescaled)'}
    for lr in LRS:
        Q = P[P['lr'] == lr]
        V = Q[Q['valid']]
        k1, k2 = int(V['hg1r'].sum()) if len(V) else 0, int(V['hg2r'].sum()) if len(V) else 0
        hi = V[(V['exposure_O1'] >= 0.9) & (V['exposure_G1'] >= 0.9)] if len(V) else V
        aux_hi = dict(n_pairs=int(len(hi)),
                      count_turnover_G1_lt_0_9_O1=int((hi['turnover_G1'] < 0.9 * hi['turnover_O1']).sum()) if len(hi) else 0,
                      ratio_G1_over_O1=[float(x) for x in (hi['turnover_G1'] / hi['turnover_O1'])] if len(hi) else [],
                      pairs=[f"{r.arch}_s{r.seed}" for r in hi.itertuples()],
                      note='descriptive only (not a verdict): pairs with exposure >= 0.9 in both conditions')
        desc = {}
        for c in ('O1', 'G1'):
            if len(V):
                desc[c] = dict(alpha_median=float(V[f'alpha_{c}'].median()), alpha_min=float(V[f'alpha_{c}'].min()),
                               alpha_max=float(V[f'alpha_{c}'].max()),
                               turnover_median=float(V[f'turnover_{c}'].median()),
                               turnover_mean=float(V[f'turnover_{c}'].mean()),
                               exposure_mean=float(V[f'exposure_{c}'].mean()),
                               exposure_lt_05=int((V[f'exposure_{c}'] < 0.5).sum()),
                               excess3_median=float(V[f'excess3_{c}'].median()),
                               excess3_mean=float(V[f'excess3_{c}'].mean()))
        # lr 0.01 extension, same 6 pairs, same rules (descriptive)
        k1_01 = int((Q['alpha_G1_lr01'] < Q['alpha_O1_lr01'] - 0.05).sum())
        k2_01 = int((Q['turnover_G1_lr01'] < 0.9 * Q['turnover_O1_lr01']).sum())
        cmp01 = dict(hg1_count_lr0_01=k1_01, hg2_count_lr0_01=k2_01, of=len(Q),
                     alpha_median_lr0_01={c: float(Q[f'alpha_{c}_lr01'].median()) for c in ('O1', 'G1')},
                     turnover_median_lr0_01={c: float(Q[f'turnover_{c}_lr01'].median()) for c in ('O1', 'G1')},
                     exposure_mean_lr0_01={c: float(Q[f'exposure_{c}_lr01'].mean()) for c in ('O1', 'G1')},
                     note='same rules applied to the extension O1/G1 BR10 runs (lr 0.01, 40 episodes); descriptive')
        res[lr_tag(lr)] = {
            'lr': lr, 'n_pairs': len(Q), 'n_valid': int(len(V)),
            'diverged_runs': [f"{b}_{r.arch}_s{r.seed}" for r in Q.itertuples() for b in ('O1', 'G1')
                              if getattr(r, f'diverged_{b}')],
            'H-G1R': dict(count=k1, of=len(Q), verdict=verdict(k1, '이 학습률에서는 관성이 커진다', '커지지 않았다')),
            'H-G2R': dict(count=k2, of=len(Q), verdict=verdict(k2, '줄었다', '줄지 않았다')),
            'aux_turnover_exposure_ge_0_9': aux_hi, 'descriptive': desc, 'comparison_lr0_01_same_pairs': cmp01}
    OUT.mkdir(parents=True, exist_ok=True)
    P.to_csv(OUT / 'pairs.csv', index=False)
    (OUT / 'judge.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
    cols = [c for c in ['lr', 'arch', 'seed', 'valid', 'alpha_O1', 'alpha_G1', 'hg1r', 'turnover_O1', 'turnover_G1', 'hg2r',
                        'exposure_O1', 'exposure_G1', 'alpha_O1_lr01', 'alpha_G1_lr01'] if c in P.columns]
    print(P[cols].round(4).to_string())
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['gate', 'run', 'launch', 'status', 'judge'])
    ap.add_argument('--lr', type=float, default=None)
    ap.add_argument('--worker', type=int, default=0)
    ap.add_argument('--nworkers', type=int, default=1)
    ap.add_argument('--threads', type=int, default=1)
    args = ap.parse_args()
    {'gate': cmd_gate, 'run': cmd_run, 'launch': cmd_launch, 'status': cmd_status, 'judge': cmd_judge}[args.cmd](args)
