# -*- coding: utf-8 -*-
# HARLF(Y25-02) F4 맥 로컬 실행. notes/funnel_f4_harlf.md 2절 그대로.
# 논문 각주 2 Colab 노트북(Drive 1FPX9_8z0X39Pg3tf1bSvoByEWbbQ_juF)의 코드 셀을 Colab "모두 실행"처럼 순서대로 한 이름공간에서 실행한다.
# '!'로 시작하는 셸 줄(pip 설치 3줄)만 빼고 실행한다(설치는 env에서 미리 함). 예외가 나면 그 셀에서 멈춘다.
# 성과(표준출력·결과 CSV·그림)는 열지 않는다. 판정은 종료 코드·시간·표지 파일 존재로만 한다.
# 사용: python3 replication/funnel_f4_harlf_mac.py
import hashlib, json, os, pathlib, subprocess, time

HOME = pathlib.Path.home()
NB = HOME / 'f4mac' / 'harlf' / 'nb2.ipynb'
NB_SHA = '2552debf194b3e1169ec38f65205851a440186d57fa72f0eee37349ac994d423'
PY = HOME / 'f4mac' / 'py311' / 'bin' / 'python'
OUT = HOME / 'f4mac' / 'out' / 'harlf'
CAP = 3 * 3600
MAX_ATT = 3
OUT.mkdir(parents=True, exist_ok=True)

DRIVER = r'''
import json, sys, time, traceback
cells = json.load(open(sys.argv[1]))
ev = open(sys.argv[2], 'a')
g = {'__name__': '__main__'}
for i, src in cells:
    ev.write(json.dumps({'ev': 'cell_start', 'cell': i, 't': time.time()}) + '\n'); ev.flush()
    try:
        exec(compile(src, f'<cell {i}>', 'exec'), g)
    except BaseException:
        tb = traceback.format_exc().splitlines()
        ev.write(json.dumps({'ev': 'cell_error', 'cell': i, 't': time.time(), 'tb_tail': tb[-12:]}) + '\n'); ev.flush()
        sys.exit(3)
    ev.write(json.dumps({'ev': 'cell_end', 'cell': i, 't': time.time()}) + '\n'); ev.flush()
ev.write(json.dumps({'ev': 'all_done', 't': time.time()}) + '\n')
'''


def main():
    if (OUT / 'done.json').exists():
        print('이미 끝남', (OUT / 'done.json').read_text()); return
    assert hashlib.sha256(NB.read_bytes()).hexdigest() == NB_SHA
    atts = sorted(OUT.glob('attempt*.json'))
    if len(atts) >= MAX_ATT:
        (OUT / 'done.json').write_text(json.dumps({'status': 'F4 실패(시도 3회)'}, ensure_ascii=False)); return
    att = len(atts) + 1
    run = HOME / 'f4mac' / 'harlf' / f'run{att}'          # 노트북 첫 셀이 작업 폴더를 비우므로 빈 폴더에서 실행
    meta = HOME / 'f4mac' / 'harlf' / f'meta{att}'
    subprocess.run(['rm', '-rf', str(run), str(meta)]); run.mkdir(parents=True); meta.mkdir(parents=True)
    nb = json.loads(NB.read_text())
    cells, dropped = [], []
    for i, c in enumerate(nb['cells']):
        if c['cell_type'] != 'code':
            continue
        lines = ''.join(c['source']).splitlines()
        keep = [l for l in lines if not l.lstrip().startswith('!')]
        dropped += [(i, l.strip()) for l in lines if l.lstrip().startswith('!')]
        cells.append((i, '\n'.join(keep)))
    (meta / 'cells.json').write_text(json.dumps(cells))
    (meta / 'driver.py').write_text(DRIVER)
    (OUT / f'attempt{att}.json').write_text(json.dumps({'attempt': att, 'start': time.time(), 'dropped': dropped}, ensure_ascii=False))
    t0 = time.time()
    with open(meta / 'stdout.log', 'w') as fo, open(meta / 'stderr.log', 'w') as fe:
        p = subprocess.Popen([str(PY), str(meta / 'driver.py'), str(meta / 'cells.json'), str(meta / 'events.jsonl')],
                             cwd=str(run), stdout=fo, stderr=fe, env=dict(os.environ, MPLBACKEND='Agg', PYTHONNOUSERSITE='1'))
        try:
            rc = p.wait(timeout=CAP); capped = False
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); rc = None; capped = True
    sec = time.time() - t0
    ab = run / 'ALL_BACKTEST'
    marker = {'roi': (ab / 'ROI.csv').exists(), 'pv': (ab / 'portfolio_value.csv').exists(),
              'super': any('super' in str(q).lower() for q in ab.rglob('*.csv')) if ab.exists() else False}   # 존재만 확인
    evs = [json.loads(l) for l in open(meta / 'events.jsonl')] if (meta / 'events.jsonl').exists() else []
    res = {'attempt': att, 'rc': rc, 'capped': capped, 'seconds': round(sec, 1), 'marker': marker,
           'cells_done': sum(e['ev'] == 'cell_end' for e in evs), 'cells_total': len(cells),
           'all_done': any(e['ev'] == 'all_done' for e in evs)}
    err = [e for e in evs if e['ev'] == 'cell_error']
    if capped:
        res['status'] = '상한 내 미완'
    elif rc == 0 and res['all_done'] and all(marker.values()):
        res['status'] = 'F4 통과(노트북 2 전체 1회, 감성 시뮬레이션)'
    else:
        res['status'] = 'F4 실패(시도)'
        res['error'] = err[-1] if err else (meta / 'stderr.log').read_text(errors='ignore').splitlines()[-40:]
    (OUT / f'attempt{att}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    if res['status'] != 'F4 실패(시도)':
        (OUT / 'done.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != 'error'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
