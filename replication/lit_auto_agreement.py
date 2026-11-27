# 문헌 조사 자동 재코딩 일치(사전 등록 notes/lit_auto_coder_prereg.md 지표 그대로).
import csv, json, collections
orig = {r['id']: r for r in csv.DictReader(open('notes/lit/lit_survey_merged.csv', encoding='utf-8-sig'))}
auto = {r['id']: r for r in csv.DictReader(open('notes/lit/lit_auto_coding.csv', encoding='utf-8-sig'))}
def tf(x): return str(x).strip().lower() in ('true', 't', 'y', 'yes', '1')
def init_cat(s):
    s = s.lower()
    for k in ('cash', 'equal', 'random'):
        if s.startswith(k): return k
    if s.startswith('policy') or 'carried' in s: return 'carried_over'
    return 'unspecified'
def kappa(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n; pe = pa * pb + (1 - pa) * (1 - pb)
    return po, (None if pe == 1 else (po - pe) / (1 - pe))
ids = list(auto); res = {'n': len(ids)}
for item, oc in (('stateful', 'stateful'), ('init_in_paper', 'init_in_paper'), ('eval_warmup', 'eval_warmup')):
    a = [tf(auto[i][item]) for i in ids]; o = [tf(orig[i][oc]) for i in ids]
    po, k = kappa(o, a)
    res[item] = {'agreement': round(po, 3), 'kappa': None if k is None else round(k, 3),
                 'orig_true': sum(o), 'auto_true': sum(a),
                 'disagree': [{'id': i, 'orig': o[j], 'auto': a[j]} for j, i in enumerate(ids) if o[j] != a[j]]}
oi = [init_cat(orig[i]['test_initial_holding']) for i in ids]; ai = [init_cat(auto[i]['test_initial_holding']) for i in ids]
res['test_initial_holding'] = {'agreement': round(sum(x == y for x, y in zip(oi, ai)) / len(ids), 3),
                               'crosstab_orig_auto': {f'{x}|{y}': v for (x, y), v in collections.Counter(zip(oi, ai)).items()},
                               'disagree': [{'id': i, 'orig': orig[i]['test_initial_holding'], 'auto': auto[i]['test_initial_holding']} for i, x, y in zip(ids, oi, ai) if x != y]}
res['init_sensitivity_auto_true'] = sum(tf(auto[i]['init_sensitivity']) for i in ids)
json.dump(res, open('replication/lit_auto_agreement.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
