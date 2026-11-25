# -*- coding: utf-8 -*-
"""Pre-registered judge for exploratory F7x WaveCorr (notes/funnel_f7x_wavecorr_prereg.md).

Metrics follow the code's own compute_performance_measures (wavecorr_agent.py @20ff832):
  annual_return = APV[-1] ** (252 / len(APV)) - 1
  annual_vol    = std(diff(log APV)) * sqrt(252)          (numpy std, ddof 0)
  SR            = annual_return / annual_vol
  MDD           = min_i APV[i] / max(APV[0:i]) - 1, i >= 1
computed on the saved APV_.csv (columns: date, policy APV, EW APV), test period = rows after trainSetLen.
Only seeds with RUNS_DIR/seed<s>/done.json are read. status 'ok' -> metrics from APV_.csv; status 'early_stop' (code's
zero-turnover return) -> counted in the R2 denominator as not above the bar, excluded from the R1 mean.
Usage: python3 funnel_f7x_wavecorr_judge.py RESULTS_DIR RUNS_DIR OUT_JSON   |   --selftest
"""
import csv
import json
import math
import os
import sys

SEEDS = [1112, 1113, 1114, 1115, 1116]
REP_SR, CMP_SR = 1.73, 1.14            # Table 2 Can-data: WaveCorr, strongest benchmark (CS-PPN)
REP_AR, CMP_AR = 0.27, 0.21
HALF_SR, HALF_AR = 0.5 * (REP_SR - CMP_SR), 0.5 * (REP_AR - CMP_AR)


def read_apv(path):
    rows = [r for r in csv.reader(open(path)) if r]
    return [r[0] for r in rows], [float(r[1]) for r in rows], [float(r[2]) for r in rows]


def metrics(v):
    n = len(v)
    ar = v[-1] ** (252 / n) - 1
    lr = [math.log(v[i + 1]) - math.log(v[i]) for i in range(n - 1)]
    m = sum(lr) / len(lr)
    vol = math.sqrt(sum((x - m) ** 2 for x in lr) / len(lr)) * math.sqrt(252)
    peak, mdd = v[0], 0.0
    for i in range(1, n):
        peak = max(peak, v[i - 1])
        mdd = min(mdd, v[i] / peak - 1)
    return {'AR': ar, 'vol': vol, 'SR': ar / vol, 'MDD': mdd, 'n': n}


def judge(results_dir, runs_dir):
    res = {'reported': {'SR': REP_SR, 'AR': REP_AR}, 'comparator': {'SR': CMP_SR, 'AR': CMP_AR},
           'band_SR': [REP_SR - HALF_SR, REP_SR + HALF_SR], 'band_AR': [REP_AR - HALF_AR, REP_AR + HALF_AR],
           'per_seed': {}, 'EW': None}
    ew, dates0 = None, None
    early = []
    for s in SEEDS:
        dj = os.path.join(runs_dir, f'seed{s}', 'done.json')
        if not os.path.exists(dj):
            continue
        st = json.load(open(dj)).get('status')
        if st == 'early_stop':
            early.append(s)
            continue
        if st != 'ok':
            continue
        p = os.path.join(results_dir, f'can_waveCorr_50stocks_seed{s}_permutation1', 'APV_.csv')
        d, v, e = read_apv(p)
        if dates0 is None:
            dates0, ew = d, e
        elif d != dates0:
            res['per_seed'][s] = 'date mismatch'
            continue
        res['per_seed'][s] = metrics(v)
        res['EW_identical_across_seeds'] = res.get('EW_identical_across_seeds', True) and e == ew
    ok = {s: m for s, m in res['per_seed'].items() if isinstance(m, dict)}
    res['early_stop_seeds'] = early
    res['n_done'] = len(ok) + len(early)
    if res['n_done'] < 4 or not ok:
        res['R1'] = res['R2'] = res['verdict'] = '판정 불가(완료 시드 4개 미만)'
        return res
    res['EW'] = metrics(ew)
    mean_sr = sum(m['SR'] for m in ok.values()) / len(ok)
    mean_ar = sum(m['AR'] for m in ok.values()) / len(ok)
    res['mean_SR'], res['mean_AR'] = mean_sr, mean_ar
    lo, hi = res['band_SR']
    r1 = lo <= mean_sr <= hi
    res['R1'] = '통과' if r1 else ('미통과(위쪽)' if mean_sr > hi else '미통과')
    lo, hi = res['band_AR']
    res['R1_aux_AR'] = '통과' if lo <= mean_ar <= hi else '미통과'
    bar = max(CMP_SR, res['EW']['SR'])
    res['R2_bar'] = bar
    k = sum(m['SR'] > bar for m in ok.values())
    res['R2_seeds_above'] = f'{k}/{len(ok) + len(early)}'
    r2 = k >= 4
    res['R2'] = '통과' if r2 else '미통과'
    res['verdict'] = '재현' if (r1 and r2) else ('부분 재현' if (r1 or r2) else '미재현')
    res['runs_in_band_SR'] = sum(res['band_SR'][0] <= m['SR'] <= res['band_SR'][1] for m in ok.values())
    return res


def selftest():
    import random
    import tempfile
    random.seed(0)
    d = tempfile.mkdtemp()
    n = 1454
    ew = [1.0]
    for _ in range(n - 1):
        ew.append(ew[-1] * (1 + 0.0002 + 0.009 * random.gauss(0, 1)))
    for i, s in enumerate(SEEDS):
        v = [1.0]
        drift = 0.0011 if i < 4 else 0.0
        for _ in range(n - 1):
            v.append(v[-1] * (1 + drift + 0.010 * random.gauss(0, 1)))
        p = os.path.join(d, f'can_waveCorr_50stocks_seed{s}_permutation1')
        os.makedirs(p)
        with open(os.path.join(p, 'APV_.csv'), 'w') as f:
            for j in range(n):
                f.write(f'2014-01-{j},{v[j]},{ew[j]}\n')
        os.makedirs(os.path.join(d, 'runs', f'seed{s}'))
        json.dump({'status': 'ok'}, open(os.path.join(d, 'runs', f'seed{s}', 'done.json'), 'w'))
    r = judge(d, os.path.join(d, 'runs'))
    print('selftest', r['R1'], r['R2'], r['R2_seeds_above'], round(r['mean_SR'], 3), round(r['EW']['SR'], 3), r['verdict'])
    assert r['n_done'] == 5 and r['EW_identical_across_seeds']
    flat = metrics([1.0, 1.1, 1.0, 1.1])
    assert abs(flat['MDD'] + 1 / 11) < 1e-12
    json.dump({'status': 'early_stop'}, open(os.path.join(d, 'runs', 'seed1113', 'done.json'), 'w'))
    r2 = judge(d, os.path.join(d, 'runs'))
    assert r2['early_stop_seeds'] == [1113] and r2['R2_seeds_above'].endswith('/5') and r2['n_done'] == 5
    os.remove(os.path.join(d, 'runs', 'seed1116', 'done.json'))
    os.remove(os.path.join(d, 'runs', 'seed1115', 'done.json'))
    assert judge(d, os.path.join(d, 'runs'))['R1'].startswith('판정 불가')
    print('selftest ok')


if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        selftest()
        sys.exit(0)
    r = judge(sys.argv[1], sys.argv[2])
    json.dump(r, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: r.get(k) for k in ('n_done', 'R1', 'R1_aux_AR', 'R2', 'R2_seeds_above', 'verdict')},
                     ensure_ascii=False))
