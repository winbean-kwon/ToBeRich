# -*- coding: utf-8 -*-
# 전체 재생성·대조: 저장소에 커밋된 판정 JSON·표·통계 입력을 원 산출물에서 다시 만들고 커밋본과 비교한다.
# 새 계산·새 기준 없음. 각 단계는 기존 판정 명령을 그대로 부른다(대장 D절과 같은 명령).
#   python3 replication/regenerate_all.py            # 맥 단계 실행 → replication/regen/manifest_mac.json
#   python3 replication/regenerate_all.py server     # 서버 단계(ssh tb) 실행 → replication/regen/manifest_server.json
# 끝나면 이 스크립트가 덮어쓴 추적 파일은 HEAD 내용으로 되돌린다(비교 결과는 manifest에 남는다).
# 통계 v2 main.json은 봉인 중이라 다시 만들지 않는다(입력 CSV만 대조).
import sys, os, json, time, hashlib, subprocess, pathlib, shutil, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTD = ROOT / 'replication' / 'regen'
PY = sys.executable


def sh256(b):
    return hashlib.sha256(b).hexdigest()


def head_bytes(rel):
    r = subprocess.run(['git', 'show', f'HEAD:{rel}'], cwd=ROOT, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def jdiff(a, b, path=''):
    # a: 커밋본, b: 재생성본. 반환: (추가 키 경로, 그 밖 차이 경로)
    added, other = [], []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in b:
            if k not in a:
                added.append(f'{path}/{k}')
        for k in a:
            if k not in b:
                other.append(f'{path}/{k} (없어짐)')
            else:
                x, y = jdiff(a[k], b[k], f'{path}/{k}'); added += x; other += y
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x0, y0) in enumerate(zip(a, b)):
            x, y = jdiff(x0, y0, f'{path}[{i}]'); added += x; other += y
    elif a != b:
        if isinstance(a, float) and isinstance(b, float) and abs(a - b) <= 1e-12 * max(1, abs(a)):
            return added, other
        other.append(path)
    return added, other


def compare(committed, new, rel):
    row = {'path': rel, 'sha256_committed': sh256(committed) if committed is not None else None,
           'sha256_regenerated': sh256(new) if new is not None else None}
    if committed is None or new is None:
        row['status'] = '비교 불가(파일 없음)'; return row
    if committed == new:
        row['status'] = '바이트 동일'; return row
    if rel.endswith('.json'):
        try:
            a, b = json.loads(committed), json.loads(new)
        except Exception:
            row['status'] = '다름(JSON 해석 실패)'; return row
        added, other = jdiff(a, b)
        if not other:
            row['status'] = '내용 동일' if not added else '내용 동일 + 기록용 키 추가'
            row['added_keys'] = added[:20]
        else:
            row['status'] = '다름'; row['diff_paths'] = other[:30]; row['added_keys'] = added[:20]
        return row
    row['status'] = '다름'
    return row


def run(cmd, env=None):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env={**os.environ, **(env or {})}, shell=isinstance(cmd, str))
    return r.returncode, round(time.time() - t0, 1), (r.stderr or '')[-1500:]


# (단계 이름, 명령, 환경, [(재생성 파일, 대조할 커밋 파일)])
MAC_STEPS = [
    ('FinRL O1 판정', [PY, 'replication/finrl_t3_run.py', 'judge'], None,
     [('replication/finrl_t3/o1/judge_W0.json', None)]),
    ('FinRL O2 판정', [PY, 'replication/finrl_t3_run.py', 'judge2'], None,
     [('replication/finrl_t3/o2/judge_o2.json', None)]),
    ('FinRL O6 판정', [PY, 'replication/finrl_t3_run.py', 'judge6'], None,
     [('replication/finrl_t3/o6/judge_o6.json', None)]),
    ('DeepAries O1 판정', [PY, 'replication/deeparies_run.py', 'judge1'], None,
     [('replication/deeparies/runs/judge_o1.json', 'replication/deeparies/judge_o1.json')]),
    ('DeepAries E 판정(e1·e10)', [PY, 'replication/deeparies_run.py', 'judge_e'], {'DA_RUNS': str(ROOT / 'replication/deeparies/e10')},
     [('replication/deeparies/e10/judge_e.json', None), ('replication/deeparies/e10/judge_e1.json', None),
      ('replication/deeparies/e10/judge_e10.json', None)]),
    ('AlphaMix+ O1 판정', [PY, 'replication/alphamix_t2/judge1_without_daily_check.py', 'judge1', 'replication/alphamix_t2'], None,
     [('replication/alphamix_t2/judge_o1.json', None)]),
    ('MARS O1 판정', [PY, 'replication/mars_t4.py', 'judge'], {'MARS_WORK': '.marswork', 'MARS_OUT': 'data/mars_t4'},
     [('data/mars_t4/judge_o1.json', None)]),
    ('깔때기 표', [PY, 'replication/funnel_table.py'], None, [('notes/lit/f1/funnel_table.csv', None)]),
    ('재현 종합표', [PY, 'replication/reproduction_synthesis.py'], None, [('replication/reproduction_synthesis.csv', None)]),
    ('통계 v2 입력(F·D·D′)', [PY, 'replication/stat_power/prep.py', 'fd'], None,
     [(f'replication/stat_power/inputs/{n}.csv', None) for n in ('F_W0', 'F_W1', 'F_W2', 'D', 'Dp')]),
]


def mac():
    rows, touched = [], set()
    for name, cmd, env, files in MAC_STEPS:
        before = {f: (ROOT / f).read_bytes() if (ROOT / f).exists() else None for f, _ in files}
        rc, sec, err = run(cmd, env)
        step = {'step': name, 'cmd': ' '.join(str(c) for c in cmd).replace(str(ROOT) + '/', ''), 'env': env and
                {k: v.replace(str(ROOT) + '/', '') for k, v in env.items()}, 'rc': rc, 'seconds': sec, 'files': []}
        if rc != 0:
            step['stderr_tail'] = err
        for f, ref in files:
            new = (ROOT / f).read_bytes() if (ROOT / f).exists() else None
            committed = head_bytes(ref or f)
            row = compare(committed, new, ref or f)
            if ref:
                row['regenerated_at'] = f
            if new is not None and before[f] is not None and new == before[f] and rc != 0:
                row['status'] += ' (실행 실패, 기존 파일 그대로)'
            step['files'].append(row)
            if head_bytes(f) is not None:
                touched.add(f)
        rows.append(step)
        print(f"{name}: rc={rc} {sec}s", [r['status'] for r in step['files']], flush=True)
    for f in sorted(touched):   # 추적 파일 원상 복구
        subprocess.run(['git', 'checkout', 'HEAD', '--', f], cwd=ROOT)
    return rows


SERVER_SCRIPT = r'''
set -e
T=$(mktemp -d ~/regen_XXXX)
R=~/ToBeRich
cd $R && git pull -q --ff-only origin audit-fix-1004
PY=~/f4work/statpow/bin/python
# Ensemble F7: 원 폴더를 덮어쓰지 않게 E1..E5를 링크한 임시 폴더에서 판정
mkdir -p $T/ens && for k in 1 2 3 4 5; do ln -s $R/data/funnel/ensemble_f7/E$k $T/ens/E$k; done
python3 $R/replication/funnel_f7_ensemble_judge.py $T/ens ~/f4work/ensemble/run/data/^DJI.csv > /dev/null
# RAT F7: 결과 파일을 뺀 모든 항목을 링크
mkdir -p $T/rat && for f in $R/data/funnel/rat_f7_gtx1650/*; do b=$(basename $f); [ "$b" = f7_result.json ] || ln -s $f $T/rat/$b; done
$PY $R/replication/funnel_f7_rat_judge.py $T/rat > /dev/null
# 통계 v2 E 입력
mkdir -p $T/sp && cp $R/replication/stat_power/prep.py $T/sp/ && cd $T/sp && $PY prep.py e $R/data/funnel/ensemble_f7 ~/f4work/ensemble/run > /dev/null
echo "@@ENS"; cat $T/ens/judge_result.json
echo "@@RAT"; cat $T/rat/f7_result.json
echo "@@E"; cat $T/sp/inputs/E.csv
rm -rf $T
'''


def server():
    t0 = time.time()
    # 바이트 그대로 받는다(CSV의 \r\n 줄바꿈이 텍스트 모드에서 바뀌지 않게)
    r = subprocess.run(['ssh', 'tb', 'wsl -e bash -s'], input=SERVER_SCRIPT.encode(), capture_output=True)
    out = r.stdout
    parts = {}
    for tag in ('ENS', 'RAT', 'E'):
        mk = f'@@{tag}\n'.encode(); i = out.find(mk)
        nxt = [out.find(f'@@{t}\n'.encode(), i + 1) for t in ('ENS', 'RAT', 'E')]
        j = min([x for x in nxt if x > i] or [len(out)])
        parts[tag] = out[i + len(mk):j] if i >= 0 else None
    rows = [{'step': 'Ensemble F7 판정(서버)', 'files': [compare(head_bytes('replication/funnel_f7/ensemble_judge_result.json'), parts['ENS'], 'replication/funnel_f7/ensemble_judge_result.json')]},
            {'step': 'RAT F7 판정(서버, GTX 1650 결과)', 'files': [compare(head_bytes('replication/funnel_f7/rat_f7_result.json'), parts['RAT'], 'replication/funnel_f7/rat_f7_result.json')]},
            {'step': '통계 v2 입력 E(서버)', 'files': [compare(head_bytes('replication/stat_power/inputs/E.csv'), parts['E'], 'replication/stat_power/inputs/E.csv')]}]
    for s in rows:
        print(s['step'], [f['status'] for f in s['files']])
    return rows, {'rc': r.returncode, 'seconds': round(time.time() - t0, 1), 'stderr_tail': r.stderr.decode(errors='replace')[-1500:]}


if __name__ == '__main__':
    OUTD.mkdir(exist_ok=True)
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if sys.argv[1:] == ['server']:
        rows, meta = server()
        (OUTD / 'manifest_server.json').write_text(json.dumps({'git_head': head, 'date': time.strftime('%Y-%m-%d %H:%M'), **meta, 'steps': rows}, ensure_ascii=False, indent=1))
    else:
        rows = mac()
        (OUTD / 'manifest_mac.json').write_text(json.dumps({'git_head': head, 'date': time.strftime('%Y-%m-%d %H:%M'), 'python': sys.version.split()[0], 'steps': rows}, ensure_ascii=False, indent=1))
