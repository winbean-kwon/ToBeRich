# -*- coding: utf-8 -*-
# 탐색적 F7 Margin Trader 판정. 사전 등록 notes/funnel_f7x_margintrader_prereg.md 4장 그대로. 표준 라이브러리만.
# 입력: 실행 기록 폴더(<조건>_s<시드>_done.json), 조건 P(주 판정) 또는 H(병기). 각 시드의 result_dir/perf_stats_trade.csv, perf_stats_dji.csv(pyfolio perf_stats, 열 Value)만 읽는다.
# 사용: python3 funnel_f7x_margintrader_judge.py <OUT 폴더> <P|H> [출력 json]
#       python3 funnel_f7x_margintrader_judge.py --selftest
import csv, json, math, pathlib, statistics, sys, tempfile

REPORTED = {'sharpe': 0.793, 'ann': 0.185}
FINRL_A2C = {'sharpe': 0.684, 'ann': 0.115}
DJI = {'sharpe': 0.790, 'ann': 0.129}
FINRL_DDPG_SR = 0.956
TOL = (REPORTED['sharpe'] - FINRL_A2C['sharpe']) / 2          # 0.0545
R1_LO, R1_HI = REPORTED['sharpe'] - TOL, REPORTED['sharpe'] + TOL
R2_BAR = max(DJI['sharpe'], FINRL_A2C['sharpe'])                # 0.790
ANN_TOL = (REPORTED['ann'] - FINRL_A2C['ann']) / 2               # 0.035
KEYS = {'Annual return': 'ann', 'Cumulative returns': 'cum', 'Annual volatility': 'vol',
        'Sharpe ratio': 'sharpe', 'Calmar ratio': 'calmar', 'Max drawdown': 'mdd'}


def read_perf(p):
    out = {}
    with open(p) as f:
        for row in csv.reader(f):
            if len(row) >= 2 and row[0] in KEYS:
                out[KEYS[row[0]]] = float(row[1])
    return out


def judge(outdir, cond):
    outdir = pathlib.Path(outdir)
    runs, dji = {}, None
    for s in range(5):
        d = outdir / f'{cond}_s{s}_done.json'
        if not d.exists():
            continue
        info = json.loads(d.read_text())
        if info.get('status') not in ('완료', '완료(후속 오류)'):
            continue
        rd = pathlib.Path(info['result_dir'])
        runs[s] = read_perf(rd / 'perf_stats_trade.csv')
        if s == 0 and (rd / 'perf_stats_dji.csv').exists():
            dji = read_perf(rd / 'perf_stats_dji.csv')
    n = len(runs)
    srs = [r['sharpe'] for r in runs.values()]
    res = {'cond': cond, 'n_complete': n, 'per_seed': runs, 'tolerance': {'R1': [R1_LO, R1_HI], 'R2_bar': R2_BAR}}
    if n >= 3:
        m = sum(srs) / n
        res['R1'] = {'mean_sharpe': m, 'sd_sharpe': statistics.stdev(srs), 'pass': R1_LO <= m <= R1_HI,
                     'direction': 'in' if R1_LO <= m <= R1_HI else ('below' if m < R1_LO else 'above')}
    else:
        res['R1'] = {'pass': None, 'note': '판정 불가(완료 3개 미만)'}
    if n == 5:
        k = sum(1 for x in srs if x > R2_BAR)
        res['R2'] = {'n_above': k, 'need': math.ceil(0.7 * 5), 'pass': k >= math.ceil(0.7 * 5)}
    else:
        res['R2'] = {'pass': None, 'note': '판정 불가(완료 5개 미만)'}
    p1, p2 = res['R1']['pass'], res['R2']['pass']
    if p1 is None or p2 is None:
        g = '판정 불가'
    else:
        g = {2: '재현', 1: '부분 재현', 0: '미재현'}[int(p1) + int(p2)]
    res['grade'] = '탐색적 ' + g
    # 보조(판정 아님)
    aux = {}
    if n:
        anns = [r['ann'] for r in runs.values()]
        ma = sum(anns) / n
        aux['ann_mean'] = ma
        aux['ann_in_T3_width'] = REPORTED['ann'] - ANN_TOL <= ma <= REPORTED['ann'] + ANN_TOL
        aux['n_in_R1_width'] = sum(1 for x in srs if R1_LO <= x <= R1_HI)
        aux['alt_width_DJI'] = abs(REPORTED['sharpe'] - DJI['sharpe']) / 2
        aux['alt_width_FinRL_DDPG'] = abs(REPORTED['sharpe'] - FINRL_DDPG_SR) / 2
        aux['mean_in_alt_DJI'] = abs(sum(srs) / n - REPORTED['sharpe']) <= aux['alt_width_DJI']
        aux['mean_in_alt_DDPG'] = abs(sum(srs) / n - REPORTED['sharpe']) <= aux['alt_width_FinRL_DDPG']
    if dji:
        rel = {k: (dji[k] - DJI[k]) / DJI[k] for k in ('sharpe', 'ann') if k in dji}
        aux['dji_check'] = {'ours': dji, 'rel_diff': rel, 'flag': any(abs(v) > 0.2 for v in rel.values())}
    res['aux'] = aux
    return res


def selftest():
    def mk(td, s, sr, ann, status='완료'):
        rd = td / f's{s}'; rd.mkdir()
        rows = [['', 'Value'], ['Annual return', ann], ['Cumulative returns', 0.6], ['Annual volatility', 0.25],
                ['Sharpe ratio', sr], ['Calmar ratio', 0.7], ['Max drawdown', -0.26]]
        for name in ('perf_stats_trade.csv', 'perf_stats_dji.csv'):
            with open(rd / name, 'w', newline='') as f:
                csv.writer(f).writerows(rows if name.endswith('trade.csv') else
                                        [['', 'Value'], ['Annual return', 0.13], ['Sharpe ratio', 0.79]])
        (td / f'P_s{s}_done.json').write_text(json.dumps({'status': status, 'result_dir': str(rd)}))
    with tempfile.TemporaryDirectory() as t:
        td = pathlib.Path(t)
        for s, sr in enumerate([0.80, 0.82, 0.79, 0.85, 0.81]):
            mk(td, s, sr, 0.18)
        r = judge(td, 'P'); assert r['grade'] == '탐색적 재현', r
    with tempfile.TemporaryDirectory() as t:
        td = pathlib.Path(t)
        for s, sr in enumerate([0.5, 0.6, 0.55, 0.95, 0.7]):
            mk(td, s, sr, 0.10)
        r = judge(td, 'P'); assert r['R1']['direction'] == 'below' and r['R2']['n_above'] == 1 and r['grade'] == '탐색적 미재현', r
    with tempfile.TemporaryDirectory() as t:
        td = pathlib.Path(t)
        for s, sr in enumerate([0.80, 0.82, 0.79, 0.85]):
            mk(td, s, sr, 0.18)
        mk(td, 4, 0.9, 0.2, status='실패(시도 3회)')
        r = judge(td, 'P'); assert r['R1']['pass'] is True and r['R2']['pass'] is None and r['grade'] == '탐색적 판정 불가', r
    with tempfile.TemporaryDirectory() as t:
        td = pathlib.Path(t)
        for s, sr in enumerate([0.70, 0.75, 0.80, 0.78, 0.76]):   # 평균 0.758 폭 안, 0.790 초과 1개 → 부분 재현
            mk(td, s, sr, 0.18)
        r = judge(td, 'P'); assert r['R1']['pass'] and not r['R2']['pass'] and r['grade'] == '탐색적 부분 재현', r
    with tempfile.TemporaryDirectory() as t:
        td = pathlib.Path(t)
        for s, sr in enumerate([0.80, 0.82, 0.79, 0.85, 0.81]):
            mk(td, s, sr, 0.18, status='완료(후속 오류)' if s == 2 else '완료')
        r = judge(td, 'P'); assert r['n_complete'] == 5 and r['grade'] == '탐색적 재현', r
        assert judge(td, 'H')['grade'] == '탐색적 판정 불가'
    assert abs(TOL - 0.0545) < 1e-9 and abs(R2_BAR - 0.790) < 1e-12
    print('selftest ok')


if __name__ == '__main__':
    if sys.argv[1:] == ['--selftest']:
        selftest()
    else:
        r = judge(sys.argv[1], sys.argv[2])
        s = json.dumps(r, ensure_ascii=False, indent=1)
        if len(sys.argv) > 3:
            pathlib.Path(sys.argv[3]).write_text(s)
        print(s)
