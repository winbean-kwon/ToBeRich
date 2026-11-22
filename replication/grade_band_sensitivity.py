# -*- coding: utf-8 -*-
"""허용 폭 규칙별 보조 등급표(탐색적). 규칙은 notes/grade_band_sensitivity_spec.md에 계산 전 고정.
주 판정은 바꾸지 않는다. 행을 합산한 재현율을 만들지 않는다.

실행: python3 replication/grade_band_sensitivity.py → replication/grade_band_sensitivity.csv, .json
      python3 replication/grade_band_sensitivity.py --selftest
"""
import csv, json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYN = ROOT / 'replication' / 'reproduction_synthesis.csv'
REL = 0.10                       # B2
RAT_SD, RAT_N = 14.25, 5         # B4: RAT ±14.25를 SD로 간주
ALPHA_SIGMA = {'S2021': 1.8, 'S2020': 1.7, 'S2019': 1.42}  # B4: AlphaMix+ 보고 σ, n = 5
TWO_METRIC = ('DeepAries', 'MARS')  # 등록 R1이 두 지표를 본 대상


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


def registered_r1_r2():
    """행 이름 → (등록 R1, 등록 R2). R2만 규칙 계산에 쓰고, R1은 B0 열에 쓴다."""
    o1 = load('replication/deeparies/judge_o1.json')
    e = load('replication/deeparies/e10/judge_e.json')
    a = load('replication/alphamix_t2/judge_o1.json')
    f = load('replication/finrl_t3/o1/judge_W0.json')
    m = load('data/mars_t4/judge_o1.json')
    en = load('replication/funnel_f7/ensemble_judge_result.json')
    ra = load('replication/funnel_f7/rat_f7_result.json')
    out = {
        'DeepAries O1(맥)': (o1['R1']['통과'], o1['R2']['통과']),
        'DeepAries e1(Colab, 탐색적)': (e['R1']['e1']['통과'], e['R2']['e1']['통과']),
        'DeepAries E(10 epoch, Colab)': (e['R1']['e10']['통과'], e['R2']['e10']['통과']),
        'MARS L(논문 시점 코드)': (m['L']['R1'], m['L']['R2']),
        'MARS N(저자 수정본)': (m['N']['R1'], m['N']['R2']),
        'MARS C(번들 체크포인트)': (m['C']['R1'], None),
        'Ensemble F7(깔때기, 서버 CPU)': (en['R1']['pass'], en['R2']['pass']),
        'RAT F7 P(깔때기, GTX 1650)': (ra['R1_A(주)'] == 'pass', ra['R2'] == 'pass'),
    }
    for st in ('S2021', 'S2020', 'S2019'):
        s = a['stages'][st]
        out[f'AlphaMix+ {st}'] = (s['R1'], s['R2'])
    for al in f['알고리즘']:
        out[f"FinRL {al['algo'].upper()}"] = (al['R1'], al['R2'])
    return out, {'R1': a['R1'], 'R2': a['R2'], 'grade': a['grade']}


def fnum(x):
    return None if x in ('', None) else float(x)


def bands(r):
    """행 → {규칙: 폭 또는 None}."""
    name, rep = r['대상'], float(r['보고값'])
    sd, n = fnum(r['시드 SD']), int(r['시드 수'])
    single = r['우리 집계 방식'] == '선택 시드'
    b = {'B0': float(r['허용 폭'])}
    adv = fnum(r['논문 우위'])
    b['B1'] = None if adv is None else abs(adv) / 2
    b['B2'] = REL * abs(rep)
    if sd is None:
        b['B3'] = None
    else:
        b['B3'] = 2 * sd if single else 2 * sd / math.sqrt(n)
    if name.startswith('AlphaMix+'):
        b['B4'] = 2 * ALPHA_SIGMA[name.split()[-1]] / math.sqrt(5)
    elif name.startswith('RAT'):
        b['B4'] = 2 * RAT_SD / math.sqrt(RAT_N)
    else:
        b['B4'] = None
    return b


def grade(r1, r2):
    if r1 is None:
        return '—'
    if r2 is None:
        return 'R1 통과' if r1 else 'R1 실패'
    return {2: '재현', 1: '부분 재현', 0: '미재현'}[int(r1) + int(r2)]


def build(rows, reg, alpha_reg):
    table = []
    for r in rows:
        name = r['대상']
        diff = abs(float(r['우리 값']) - float(r['보고값']))
        b = bands(r)
        r1_reg, r2 = reg[name]
        rec = {'대상': name, '지표': r['지표'], '|우리−보고|': round(diff, 3), 'R2(등록)': r2,
               '주 지표만': name.startswith(TWO_METRIC)}
        for k, w in b.items():
            if k == 'B0':
                r1 = r1_reg           # 등록 판정 그대로(두 지표 행 포함)
            else:
                r1 = None if w is None else diff <= w + 1e-12
            rec[f'{k} 폭'] = None if w is None else round(w, 3)
            rec[f'{k} R1'] = r1
            rec[f'{k} 등급'] = grade(r1, r2)
        table.append(rec)
    # AlphaMix+ 방법 단위(3단계 중 ≥2)
    st = [t for t in table if t['대상'].startswith('AlphaMix+')]
    meth = {'대상': 'AlphaMix+ (방법 단위)', '지표': 'TR', 'R2(등록)': alpha_reg['R2'], '주 지표만': False}
    for k in ('B0', 'B1', 'B2', 'B3', 'B4'):
        vals = [t[f'{k} R1'] for t in st]
        r1 = None if any(v is None for v in vals) else sum(vals) >= 2
        if k == 'B0':
            r1 = alpha_reg['R1']
        meth[f'{k} R1'] = r1
        meth[f'{k} 등급'] = grade(r1, alpha_reg['R2'])
    table.append(meth)
    return table


def summarize(table):
    graded = [t for t in table if not (t['대상'].startswith('AlphaMix+ S'))]  # 단계 행은 등급 단위가 아님
    s = {}
    for k in ('B1', 'B2', 'B3', 'B4'):
        changed = [t['대상'] for t in graded if t[f'{k} 등급'] != '—' and t[f'{k} 등급'] != t['B0 등급']]
        na = [t['대상'] for t in graded if t[f'{k} 등급'] == '—']
        s[k] = {'계산 가능 행': len(graded) - len(na), 'B0과 등급 다른 행 수': len(changed), '다른 행': changed, '계산 불가': na}
    return s


def selftest():
    r = {'대상': 'X', '지표': 'm', '보고값': '10', '허용 폭': '1', '우리 값': '9.5', '논문 우위': '3',
         '시드 SD': '1', '시드 수': '4', '우리 집계 방식': '시드 평균'}
    b = bands(r)
    assert b['B1'] == 1.5 and abs(b['B2'] - 1.0) < 1e-12 and b['B3'] == 1.0 and b['B4'] is None
    r['우리 집계 방식'] = '선택 시드'
    assert bands(r)['B3'] == 2.0
    assert grade(True, False) == '부분 재현' and grade(None, True) == '—' and grade(False, None) == 'R1 실패'
    print('selftest ok')


if __name__ == '__main__':
    if sys.argv[1:] == ['--selftest']:
        selftest(); sys.exit(0)
    rows = list(csv.DictReader(open(SYN, encoding='utf-8')))
    reg, alpha_reg = registered_r1_r2()
    missing = [r['대상'] for r in rows if r['대상'] not in reg]
    assert not missing, missing
    table = build(rows, reg, alpha_reg)
    summ = summarize(table)
    out = ROOT / 'replication' / 'grade_band_sensitivity'
    keys = list(table[0].keys())
    with open(out.with_suffix('.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        for t in table:
            w.writerow({k: t.get(k, '') for k in keys})
    out.with_suffix('.json').write_text(json.dumps({'table': table, 'summary': summ}, ensure_ascii=False, indent=1))
    print(json.dumps(summ, ensure_ascii=False, indent=1))
