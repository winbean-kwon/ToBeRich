# -*- coding: utf-8 -*-
# Ensemble F7 판정. 사전 등록 notes/funnel_f7_ensemble_prereg.md 4장 그대로. 표준 라이브러리만 쓴다.
# 집계는 저자 backtesting.ipynb(get_account_value → [0:1097] → pyfolio)와 같고, 지표 식은 empyrical 정의다.
# 사용: python3 funnel_f7_ensemble_judge.py <OUT 폴더> <^DJI.csv 경로>
#       python3 funnel_f7_ensemble_judge.py --selftest
import csv, json, math, pathlib, sys

ITERS = list(range(126, 1198, 63))
ROWS = 1097
REPORTED = {'cum': 0.704, 'ann': 0.130, 'vol': 0.097, 'sharpe': 1.30, 'mdd': -0.097}
BASE_SHARPE = {'PPO': 1.10, 'A2C': 1.12, 'DDPG': 0.87, 'Min-Variance': 0.45, 'DJIA': 0.47}
DJIA_REPORTED = {'cum': 0.386, 'sharpe': 0.47}
TOL = (1.30 - 0.47) / 2  # v3 규칙: 보고값과 최고 외부 기준선(DJIA 0.47) 차이의 절반 = 0.415
R1_LO, R1_HI = 1.30 - TOL, 1.30 + TOL
R2_BAR = max(BASE_SHARPE.values())  # 1.12


def metrics(values):
    """values: 계좌 가치 열(행 순서 그대로). empyrical 식: 첫 수익률(NaN)은 빼고 평균·표준편차(ddof=1),
    연율화는 len(수익률 시리즈, NaN 포함)/252년."""
    r = [values[k] / values[k - 1] - 1 for k in range(1, len(values))]
    n_series = len(values)  # pct_change 시리즈 길이(첫 NaN 포함) = pyfolio에 넘긴 행 수
    m = sum(r) / len(r)
    sd = math.sqrt(sum((x - m) ** 2 for x in r) / (len(r) - 1))
    cum = 1.0
    peak, mdd = 1.0, 0.0
    for x in r:
        cum *= 1 + x
        peak = max(peak, cum)
        mdd = min(mdd, cum / peak - 1)
    return {'cum': cum - 1, 'ann': cum ** (252 / n_series) - 1, 'vol': sd * math.sqrt(252),
            'sharpe': m / sd * math.sqrt(252), 'mdd': mdd, 'n_rows': len(values)}


def read_run(rd):
    vals, per_file = [], []
    for i in ITERS:
        f = rd / 'account_value' / f'account_value_trade_ensemble_{i}.csv'
        with open(f) as fh:
            rows = list(csv.DictReader(fh))
        per_file.append(len(rows))
        vals += [float(x['0']) for x in rows]
    return vals, per_file


def judge(out, dji_path):
    out = pathlib.Path(out)
    runs = {}
    for k in range(1, 6):
        rd = out / f'E{k}'
        dj = rd / 'done.json'
        st = json.loads(dj.read_text()).get('status') if dj.exists() else 'missing'
        if st != 'ok':
            runs[f'E{k}'] = {'status': st}
            continue
        vals, per_file = read_run(rd)
        runs[f'E{k}'] = {'status': 'ok', 'rows_total': len(vals), 'rows_per_file': per_file,
                         'main': metrics(vals[:ROWS]), 'aux_all_rows': metrics(vals)}
    ok = [v for v in runs.values() if v['status'] == 'ok']
    n = len(ok)
    res = {'n_completed': n, 'runs': runs}
    if n >= 3:
        mean_sr = sum(v['main']['sharpe'] for v in ok) / n
        res['R1'] = {'mean_sharpe': mean_sr, 'band': [R1_LO, R1_HI], 'pass': R1_LO <= mean_sr <= R1_HI,
                     'direction': 'within' if R1_LO <= mean_sr <= R1_HI else ('below' if mean_sr < R1_LO else 'above')}
    else:
        res['R1'] = {'pass': None, 'note': '완료 실행 3개 미만: 판정 불가'}
    if n == 5:
        cnt = sum(v['main']['sharpe'] > R2_BAR for v in ok)
        need = math.ceil(0.7 * n)
        res['R2'] = {'bar': R2_BAR, 'count': cnt, 'need': need, 'pass': cnt >= need}
    else:
        res['R2'] = {'pass': None, 'note': '완료 실행 5개 미만: 판정 불가'}
    if res['R1']['pass'] is None or res['R2']['pass'] is None:
        res['grade'] = '판정 불가'
    else:
        p = res['R1']['pass'] + res['R2']['pass']
        res['grade'] = {2: '재현', 1: '부분 재현', 0: '미재현'}[p]
    # 보조: 지표 평균, R1 폭 안의 실행 수, DJIA 데이터 점검(판정 아님)
    if ok:
        res['aux_mean'] = {key: sum(v['main'][key] for v in ok) / n for key in ('cum', 'ann', 'vol', 'sharpe', 'mdd')}
        res['aux_in_band'] = sum(R1_LO <= v['main']['sharpe'] <= R1_HI for v in ok)
    if dji_path:
        with open(dji_path) as fh:
            d = [r for r in csv.DictReader(fh) if '2016-01-01' <= r['Date'] <= '2020-06-30']
        dm = metrics([float(r['Adj Close']) for r in d][:ROWS])
        res['aux_djia'] = {'ours': dm, 'reported': DJIA_REPORTED,
                           'flag_rel_diff_gt_20pct': abs(dm['cum'] - 0.386) / 0.386 > 0.2 or abs(dm['sharpe'] - 0.47) / 0.47 > 0.2}
    return res


def selftest():
    import random, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp())
    rng = random.Random(0)
    for k in range(1, 6):
        rd = tmp / f'E{k}'
        (rd / 'account_value').mkdir(parents=True)
        (rd / 'done.json').write_text(json.dumps({'status': 'ok'}))
        v = 1e6
        for i in ITERS:
            with open(rd / 'account_value' / f'account_value_trade_ensemble_{i}.csv', 'w') as fh:
                fh.write(',0\n')
                for j in range(63):
                    v *= 1 + rng.gauss(0.0005, 0.006)
                    fh.write(f'{j},{v}\n')
    # 알려진 수열로 지표 식 확인
    m = metrics([100, 110, 99, 108.9])
    assert abs(m['cum'] - 0.089) < 1e-9 and abs(m['mdd'] - (-0.1)) < 1e-9, m
    res = judge(tmp, None)
    assert res['n_completed'] == 5 and res['runs']['E1']['rows_total'] == 18 * 63
    assert res['grade'] in ('재현', '부분 재현', '미재현')
    (tmp / 'E5' / 'done.json').write_text(json.dumps({'status': 'killed_at_cap'}))
    assert judge(tmp, None)['grade'] == '판정 불가'
    print('selftest ok (합성 데이터)')


if __name__ == '__main__':
    if sys.argv[1:] == ['--selftest']:
        selftest()
    else:
        r = judge(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        pathlib.Path(sys.argv[1], 'judge_result.json').write_text(json.dumps(r, ensure_ascii=False, indent=1))
