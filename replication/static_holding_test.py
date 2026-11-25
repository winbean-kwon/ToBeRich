# -*- coding: utf-8 -*-
"""Exploratory static-holding (buy-and-hold) test on share-based environments (notes/static_holding_test_prereg.md).

E (Ensemble strategy F7 runs E1-E5, old FinRL env, adjcp prices, 18 trading cycles of 63 days):
   per cycle, find the smallest d in 1..5 such that rows d..end of the cycle's account-value curve equal
   cash + sum_i n_i * adjcp_{i,t} with real n_i >= 0 (this env holds fractional shares; least squares,
   max |residual| <= 1e-9 * max value). Row r <-> cycle date index r (63 rows, 63 dates).
   Control (must pass, else no ensemble result is used): the F4 run's last_state_ensemble_62.csv (cash, 30 prices,
   30 holdings at the end of trading cycle 126) must match our adjcp prices on that date (max abs diff <= 1e-6) and
   cash + holdings . prices must equal the last row of that run's account_value_trade_ensemble_126.csv (rel 1e-9).
M (Margin Trader F7x runs P_s0-P_s4): holdings from trade_state.csv (*_h columns); share of days whose holdings
   equal the previous day's, and the last day on which holdings change.
Usage (server, any python with numpy+pandas): python static_holding_test.py OUT_JSON
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HOME = os.path.expanduser('~')
ENS_RUNS = f'{HOME}/ToBeRich/data/funnel/ensemble_f7'
ENS_DATA = f'{HOME}/f4work/ensemble/run/data/dow_30_2009_2020.csv'
MT_RUNS = f'{HOME}/f4work/mt/runs'
TOL = 1e-9
REB = VAL = 63


def ens_prices():
    d = pd.read_csv(ENS_DATA, index_col=0)
    d['adjcp'] = d['prccd'] / d['ajexdi']
    px = d.pivot_table(index='datadate', columns='tic', values='adjcp').sort_index()
    utd = d[(d.datadate > 20151001) & (d.datadate <= 20200707)].datadate.unique()
    return px, utd


def fit_cycle(v, P):
    """smallest d in 1..5 with exact static holdings n >= 0 on rows d.. (v[r] vs P[r]); returns (d, best_resid)."""
    best = np.inf
    for d in range(1, 6):
        y, X = v[d:], P[d:]
        A = np.column_stack([np.ones(len(X)), X])
        coef = np.linalg.lstsq(A, y, rcond=None)[0]
        n, c = coef[1:], float(coef[0])
        res = float(np.max(np.abs(y - c - X @ n)) / np.max(np.abs(y)))
        best = min(best, res)
        if (n >= -1e-6).all() and res <= TOL and c >= -1e-6 * np.max(np.abs(y)):
            return d, res, int((n > 1e-6).sum())
    return None, best, None


def ens_run(run, px, utd, offset=0):
    out = []
    for i in range(REB + VAL, len(utd), REB):
        f = f'{run}/account_value/account_value_trade_ensemble_{i}.csv'
        if not os.path.exists(f):
            out.append({'iter': i, 'missing': True})
            continue
        v = pd.read_csv(f, index_col=0).iloc[:, 0].values.astype(float)
        dates = utd[i - REB:i]
        P = px.loc[dates].values
        rows = [r for r in range(len(v)) if 0 <= r - offset < len(dates)]
        vv = v[rows]
        PP = P[[r - offset for r in rows]]
        d, res, nheld = fit_cycle(vv, PP)
        out.append({'iter': i, 'd': d, 'best_resid': res, 'n_assets_held': nheld})
    return out


def main(out_json):
    res = {}
    px, utd = ens_prices()
    assert px.shape[1] == 30 or px.shape[1] >= 29
    runs = sorted(glob.glob(f'{ENS_RUNS}/E[1-5]'))
    st = pd.read_csv(f'{HOME}/f4work/ensemble/run/results/last_state_ensemble_62.csv')['last_state'].values
    pr, h = st[1:31], st[31:61]
    pd_ = float(np.max(np.abs(pr - px.loc[utd[125]].values)))
    av = pd.read_csv(f'{HOME}/f4work/ensemble/run/results/account_value_trade_ensemble_126.csv', index_col=0).iloc[:, 0].values
    vd = float(abs(st[0] + pr @ h - av[-1]) / av[-1])
    ctrl = pd_ <= 1e-6 and vd <= 1e-9
    res['ensemble_control'] = {'max_price_diff': pd_, 'value_rel_diff': vd, 'rows': int(len(av)), 'pass': ctrl}
    offset = 0
    res['ensemble_alignment'] = {'offset': offset}
    res['ensemble'] = {}
    for run in (runs if ctrl else []):
        cyc = ens_run(run, px, utd, offset)
        ok = [c for c in cyc if not c.get('missing')]
        bh = sum(c['d'] is not None for c in ok)
        share = bh / len(ok) if ok else None
        cls = None if share is None else ('매수 후 보유형' if share >= 0.9 else ('부분 정적' if share >= 0.5 else '정적 아님'))
        res['ensemble'][os.path.basename(run)] = {'cycles': len(ok), 'bh_cycles': bh, 'share': share, 'class': cls,
                                                  'cash_only_cycles': sum(c['n_assets_held'] == 0 for c in ok),
                                                  'cycle_detail': cyc}
    res['margintrader'] = {}
    for s in range(5):
        fs = glob.glob(f'{MT_RUNS}/P_s{s}/results/*/a2c/trade_state.csv')
        if not fs:
            continue
        st = pd.read_csv(fs[0])
        H = st[[c for c in st.columns if c.endswith('_h')]].values
        same = np.all(H[1:] == H[:-1], axis=1)
        changed = np.where(~same)[0] + 1
        last = int(changed.max()) if len(changed) else 0
        share = float(same.mean())
        cls = '매수 후 보유형' if last <= 5 else ('부분 정적' if share >= 0.5 else '정적 아님')
        res['margintrader'][f'P_s{s}'] = {'days': int(len(H)), 'share_days_unchanged': share,
                                          'last_change_day': last, 'n_change_days': int(len(changed)), 'class': cls,
                                          'n_positions_end': int((H[-1] != 0).sum())}
    for fam in ('ensemble', 'margintrader'):
        c = [v['class'] for v in res[fam].values()]
        if len(c) < 4:
            res[f'{fam}_target_class'] = '판정 불가'
            continue
        res[f'{fam}_target_class'] = ('매수 후 보유형' if sum(x == '매수 후 보유형' for x in c) >= 4 else
                                      ('부분 정적' if sum(x in ('매수 후 보유형', '부분 정적') for x in c) >= 4 else '정적 아님'))
    json.dump(res, open(out_json, 'w'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({'control': res['ensemble_control'],
                      'ensemble': {k: {kk: v[kk] for kk in ('cycles', 'bh_cycles', 'share', 'class', 'cash_only_cycles')}
                                   for k, v in res['ensemble'].items()},
                      'margintrader': {k: {kk: v[kk] for kk in ('share_days_unchanged', 'last_change_day', 'class')}
                                       for k, v in res['margintrader'].items()},
                      'targets': {f: res[f'{f}_target_class'] for f in ('ensemble', 'margintrader')}},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
