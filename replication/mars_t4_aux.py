# -*- coding: utf-8 -*-
# T4 MARS O1 보조 값(사전 등록 4.2, 판정 아님). judge_o1.json과 시드별 파일로 계산한다.
# 사용: python3 replication/mars_t4_aux.py  → data/mars_t4/aux_o1.json, 화면 요약
import csv, json, pathlib, statistics as st

OUT = pathlib.Path(__file__).resolve().parents[1] / 'data' / 'mars_t4'
P, T = {'CR': 29.50, 'SR': 2.84}, {'CR': 7.07, 'SR': 0.715}
J = json.loads((OUT / 'judge_o1.json').read_text())
ref = J['reference']
res = {}


def rank(vals, v):  # 오름차순 순위(1 = 가장 낮음)
    return sorted(vals).index(v) + 1


for c in ('L', 'N'):
    S = J[c]['seeds']
    R = res[c] = {'windows': {}, 'seeds': {}}
    for win in ('W240', 'W251', 'W240_cash'):
        rk = 'W251' if win == 'W251' else 'W240'
        cr = [S[s][win]['CR'] for s in S]
        sr = [S[s][win]['SR'] for s in S]
        mc, ms = st.median(cr), st.median(sr)
        w = {'median_CR': mc, 'median_SR': ms, 'R1': abs(mc - P['CR']) <= T['CR'] and abs(ms - P['SR']) <= T['SR'],
             'SR_gap': abs(ms - P['SR']), 'CR_gap': abs(mc - P['CR'])}
        for name, d in (('DJI_computed', ref['DJI'][rk]), ('EW_cost0', ref['EW_cost0'][rk])):
            w['beat_' + name] = sum(a > d['CR'] and b > d['SR'] for a, b in zip(cr, sr))
        if rk == 'W240':  # 사전 등록 표기값(15.36, 1.41) 기준도 병기
            w['beat_DJI_prereg_rounded'] = sum(a > 15.36 and b > 1.41 for a, b in zip(cr, sr))
        w['R2_computed'] = w['beat_DJI_computed'] >= 7
        R['windows'][win] = w
    for m in ('CR', 'AR', 'AVol', 'SR', 'MDD'):
        v = [S[s]['W240'][m] for s in S]
        R['W240_' + m] = {'median': st.median(v), 'min': min(v), 'max': max(v)}
    for m in ('CR', 'SR'):
        v = [S[s]['W240'][m] for s in S]
        R['seed42_rank_' + m] = rank(v, S['42']['W240'][m])
    for s in S:
        d = OUT / c / f'seed_{s}'
        done = json.loads((d / 'done.json').read_text())
        att = sum(1 for _ in open(d / 'attempts.jsonl')) if (d / 'attempts.jsonl').exists() else None
        if c == 'L':
            rows = list(csv.DictReader(open(d / 'training_validation_stats.csv')))
            best, sel = float('-inf'), None
            for r in rows:  # main.py 89행: composite가 엄격히 클 때만 best_models 갱신
                if float(r['validation_composite_score']) > best:
                    best, sel = float(r['validation_composite_score']), int(r['episode'])
        else:
            sel = json.loads((d / 'bmid_selected_checkpoint.json').read_text())['selected_episode']
        met = {r['metric']: float(r['value']) for r in csv.DictReader(open(d / 'test_results_metrics.csv'))}
        w = S[s]['W240']
        R['seeds'][s] = {'W240': {k: round(w[k], 3) for k in ('CR', 'AR', 'AVol', 'SR', 'MDD')},
                         'episodes_run': done['episodes_run'], 'selected_episode': sel, 'attempts': att,
                         'cpu_hours': round(done['cpu_seconds'] / 3600, 1), 'repo_metrics_csv': met}

(OUT / 'aux_o1.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
for c in res:
    print('==', c)
    for win, w in res[c]['windows'].items():
        print(win, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in w.items()})
    print({k: {a: round(b, 2) for a, b in v.items()} for k, v in res[c].items() if k.startswith('W240_')})
    print('seed42 rank CR/SR', res[c]['seed42_rank_CR'], res[c]['seed42_rank_SR'])
    for s, v in res[c]['seeds'].items():
        print(s, v['W240'], 'ep', v['episodes_run'], 'sel', v['selected_episode'], 'att', v['attempts'],
              'cpu', v['cpu_hours'], {k: round(x, 3) for k, x in v['repo_metrics_csv'].items()})
