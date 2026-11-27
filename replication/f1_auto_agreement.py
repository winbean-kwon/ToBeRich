# F1 자동 독립 재검색과 사용자 판정의 일치(사전 등록 notes/f1_second_coder_prereg.md 지표 그대로).
import csv, json, math, collections
a = {r['id']: r['판정'].strip() for r in csv.DictReader(open('notes/lit/f1/f1_auto_coder_sheet.csv', encoding='utf-8-sig'))}
u = {r['id']: r['판정'].strip() for r in csv.DictReader(open('notes/lit/f1/f1_recheck_sheet.csv', encoding='utf-8-sig'))}
ids = list(a)
bu = [u[i] == '찾음' for i in ids]; ba = [a[i] == '찾음' for i in ids]
n = len(ids); po = sum(x == y for x, y in zip(bu, ba)) / n
pu, pa = sum(bu) / n, sum(ba) / n
pe = pu * pa + (1 - pu) * (1 - pa)
kappa = (po - pe) / (1 - pe) if pe < 1 else float('nan')
# 근사 표준오차(Cohen 1960)
se = math.sqrt(po * (1 - po) / (n * (1 - pe) ** 2)) if pe < 1 else float('nan')
cross = collections.Counter((u[i], a[i]) for i in ids)
dis = [{'id': i, 'user': u[i], 'auto': a[i]} for i in ids if u[i] != a[i]]
res = {'n': n, 'binary_agreement': round(po, 3), 'kappa': round(kappa, 3),
       'kappa_ci95': [round(kappa - 1.96 * se, 3), round(kappa + 1.96 * se, 3)],
       'crosstab_user_auto': {f'{k[0]}|{k[1]}': v for k, v in cross.items()}, 'disagreements_6cat': dis}
json.dump(res, open('replication/f1_auto_agreement.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
