# -*- coding: utf-8 -*-
# 탐색적 F7x Ensemble 난류 문턱 반사실 판정. 사전 등록 notes/funnel_f7x_ensemble_turb_prereg.md 4장 그대로.
# 재현 등급을 매기지 않는다(코드를 바꾼 반사실이므로). 대비 범주와 기술 수치만 낸다.
# 표준 라이브러리만 쓴다. 지표 식·집계는 F7 Ensemble 판정(funnel_f7_ensemble_judge.py)을 그대로 불러 쓴다.
# 사용: python3 funnel_f7x_ensemble_turb_judge.py <P 폴더(ensemble_f7)> <T·O 폴더(ensemble_turb)>
#       python3 funnel_f7x_ensemble_turb_judge.py --selftest
import json, math, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from funnel_f7_ensemble_judge import metrics, read_run, ROWS, R1_LO, R1_HI, R2_BAR  # noqa: E402

CONDS = {'P': ['E1', 'E2', 'E3', 'E4', 'E5'], 'C': ['C1', 'C2', 'C3', 'C4', 'C5'], 'T': ['T1', 'T2', 'T3', 'T4', 'T5'],
         'O': ['O1', 'O2', 'O3', 'O4', 'O5'], 'R': ['R1', 'R2']}
PRIMARY = 'C'  # 주 대비 C − P, 보조 T − P·O − P, R은 점검(대비 없음)


def t_cdf(t, df):
    """스튜던트 t 누적분포(수치 적분, 심프슨 2,000구간)."""
    c = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)
    f = lambda x: c * (1 + x * x / df) ** (-(df + 1) / 2)
    a, b, n = 0.0, abs(t), 2000
    h = (b - a) / n
    s = f(a) + f(b) + sum((4 if k % 2 else 2) * f(a + k * h) for k in range(1, n))
    half = s * h / 3
    return 0.5 + half if t >= 0 else 0.5 - half


def t_ppf(p, df):
    lo, hi = 0.0, 100.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def welch(x, y):
    """평균 차이 x̄ − ȳ, Welch 95% 구간."""
    nx, ny = len(x), len(y)
    mx, my = sum(x) / nx, sum(y) / ny
    vx = sum((v - mx) ** 2 for v in x) / (nx - 1)
    vy = sum((v - my) ** 2 for v in y) / (ny - 1)
    se = math.sqrt(vx / nx + vy / ny)
    df = (vx / nx + vy / ny) ** 2 / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1))
    q = t_ppf(0.975, df)
    d = mx - my
    return {'diff': d, 'ci95': [d - q * se, d + q * se], 'se': se, 'df': df}


def zero_days(vals):
    v = vals[:ROWS]
    return sum(1 for k in range(1, len(v)) if v[k] == v[k - 1])


def load_cond(base, names):
    runs = {}
    for nm in names:
        rd = pathlib.Path(base) / nm
        dj = rd / 'done.json'
        st = json.loads(dj.read_text()).get('status') if dj.exists() else 'missing'
        if st != 'ok':
            runs[nm] = {'status': st}
            continue
        vals, per_file = read_run(rd)
        rec = {'status': 'ok', 'main': metrics(vals[:ROWS]), 'zero_return_days_1097': zero_days(vals)}
        thr = rd / 'thresholds.jsonl'
        if thr.exists():
            rec['thresholds'] = [json.loads(l) for l in open(thr) if l.strip()]
        runs[nm] = rec
    return runs


def describe_vs_reported(sr):
    """기술만(재현 등급 아님): 평균 Sharpe가 F7 R1 폭 안인지, 1.12 초과 실행 수."""
    if not sr:
        return {}
    m = sum(sr) / len(sr)
    return {'mean_sharpe': m, 'mean_in_F7_R1_band': R1_LO <= m <= R1_HI, 'n_above_1.12': sum(s > R2_BAR for s in sr), 'n': len(sr)}


def judge(p_dir, to_dir):
    res = {'runs': {}}
    sr = {}
    for c, names in CONDS.items():
        runs = load_cond(p_dir if c == 'P' else to_dir, names)
        res['runs'][c] = runs
        sr[c] = [r['main']['sharpe'] for r in runs.values() if r['status'] == 'ok']
    res['n'] = {c: len(v) for c, v in sr.items()}
    res['contrasts'] = {}
    for c in ('C', 'T', 'O'):
        if len(sr[c]) >= 3 and len(sr['P']) >= 3:
            w = welch(sr[c], sr['P'])
            lo, hi = w['ci95']
            cat = '차이 있음(높음)' if lo > 0 else ('차이 있음(낮음)' if hi < 0 else '구분 안 됨')
            res['contrasts'][f'{c}-P'] = dict(w, category=cat)
        else:
            res['contrasts'][f'{c}-P'] = {'category': '판정 불가(완료 3회 미만)'}
        res[f'describe_{c}'] = describe_vs_reported(sr[c])
    # R(P 재실행 점검): 대비 없음. 값과 P 범위 안 여부만
    res['check_R'] = {'sharpe': sr['R'], 'P_range': [min(sr['P']), max(sr['P'])] if sr['P'] else None,
                      'within_P_range': [min(sr['P']) <= v <= max(sr['P']) for v in sr['R']] if sr['P'] else None}
    # 보조(판정 아님)
    res['aux'] = {}
    for c in CONDS:
        ok = [r for r in res['runs'][c].values() if r['status'] == 'ok']
        if ok:
            res['aux'][c] = {k: sum(r['main'][k] for r in ok) / len(ok) for k in ('cum', 'ann', 'vol', 'sharpe', 'mdd')}
            res['aux'][c]['zero_return_days_mean'] = sum(r['zero_return_days_1097'] for r in ok) / len(ok)
            th = [tuple(round(x['thr'], 6) for x in r['thresholds']) for r in ok if 'thresholds' in r]
            if th:
                res['aux'][c]['thresholds_identical_across_runs'] = len(set(th)) == 1
                res['aux'][c]['thresholds_run1'] = list(th[0])
    return res


def selftest():
    import random, tempfile
    tmp = pathlib.Path(tempfile.mkdtemp())
    rng = random.Random(1)
    for c, names in CONDS.items():
        for nm in names:
            rd = (tmp / 'P' / nm) if c == 'P' else (tmp / 'TO' / nm)
            (rd / 'account_value').mkdir(parents=True)
            (rd / 'done.json').write_text(json.dumps({'status': 'ok'}))
            v, mu = 1e6, {'P': 0.0004, 'C': 0.0004, 'T': 0.0004, 'O': 0.0012, 'R': 0.0004}[c]
            for i in range(126, 1198, 63):
                with open(rd / 'account_value' / f'account_value_trade_ensemble_{i}.csv', 'w') as fh:
                    fh.write(',0\n')
                    for j in range(63):
                        if j % 5:
                            v *= 1 + rng.gauss(mu, 0.006)
                        fh.write(f'{j},{v}\n')
            if c != 'P':
                with open(rd / 'thresholds.jsonl', 'w') as fh:
                    for i in range(126, 1198, 63):
                        fh.write(json.dumps({'iter': i, 'thr': 96.08, 'hist_mean': None}) + '\n')
    assert abs(t_ppf(0.975, 4) - 2.776) < 1e-3 and abs(t_ppf(0.975, 1e6) - 1.960) < 1e-3
    w = welch([1, 2, 3], [1, 2, 3])
    assert abs(w['diff']) < 1e-12 and w['ci95'][0] < 0 < w['ci95'][1]
    assert zero_days([1, 1, 2, 2, 2]) == 3
    r = judge(tmp / 'P', tmp / 'TO')
    assert r['n'] == {'P': 5, 'C': 5, 'T': 5, 'O': 5, 'R': 2}
    assert r['contrasts']['O-P']['category'] == '차이 있음(높음)', r['contrasts']['O-P']
    assert r['aux']['T']['thresholds_identical_across_runs'] is True
    (tmp / 'TO' / 'T5' / 'done.json').write_text(json.dumps({'status': 'killed_at_cap'}))
    (tmp / 'TO' / 'T4' / 'done.json').write_text(json.dumps({'status': 'error'}))
    (tmp / 'TO' / 'T3' / 'done.json').write_text(json.dumps({'status': 'error'}))
    r = judge(tmp / 'P', tmp / 'TO')
    assert r['contrasts']['T-P']['category'].startswith('판정 불가') and r['describe_T']['n'] == 2
    assert len(r['check_R']['within_P_range']) == 2
    print('selftest ok (합성 데이터)')


if __name__ == '__main__':
    if sys.argv[1:] == ['--selftest']:
        selftest()
    else:
        r = judge(sys.argv[1], sys.argv[2])
        print(json.dumps(r, ensure_ascii=False, indent=1))
        pathlib.Path(sys.argv[2], 'judge_result.json').write_text(json.dumps(r, ensure_ascii=False, indent=1))
