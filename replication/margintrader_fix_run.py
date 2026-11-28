# -*- coding: utf-8 -*-
# Margin Trader 정정 재실행(notes/margintrader_fix_prereg.md). funnel_f7x_margintrader_run.py와 같고 shim v2·출력 폴더(out_fix·runs_fix)만 다르다.
# 순서: 데이터 받기 1회(H, 시드 0; data.csv만 보존, 나머지 산출물은 열지 않고 지움) → P 시드 0~4 → H 시드 0~4.
# P = 7aa392c(+ os.makedir→os.makedirs 한 줄, ea8fc36과 동일), H = 7b7fa9e. 시드 k≠0은 `seed = 0` 한 줄만 바꾼다.
# 성과(stdout·results/·tensorboard)는 열지 않는다. 기록은 rc·시간·표지 존재·데이터 해시뿐.
# 사용: python3 margintrader_fix_run.py   (환경 변수 MT_ROOT, MT_PY로 경로 변경 가능)
import csv, difflib, glob, hashlib, json, os, pathlib, shutil, subprocess, time

HOME = pathlib.Path.home()
ROOT = pathlib.Path(os.environ.get('MT_ROOT', HOME / 'f4work' / 'mt'))
REPO = ROOT / 'repo'                       # git clone https://github.com/JingyiGu/Margin-Trader
PY = pathlib.Path(os.environ.get('MT_PY', ROOT / 'py310' / 'bin' / 'python'))
SHIM_DIR = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'out_fix'
RUNS = ROOT / 'runs_fix'
CAP = 3600
MAX_ATT = 3
SEEDS = [0, 1, 2, 3, 4]
COMMIT = {'P': '7aa392c', 'H': '7b7fa9e'}
SHA = {  # 수정 뒤 해시. trading_margin_a2c.py는 두 조건이 같아야 한다.
    'P': {'trading_margin_a2c.py': 'a28e3bb4e1173f7076705a613844ba83f23de3db7a79674b637868e80e0f0017',
          'env/marginEnv.py': 'f5ffa5d2b50a387f1b07c667353106fcf1ce1afe77c309435a163c84ae7e628e',
          'env/agent.py': '5009aeebef176d8659b60d5b857c059530c189126889dbad02138fa845b704da'},
    'H': {'trading_margin_a2c.py': 'a28e3bb4e1173f7076705a613844ba83f23de3db7a79674b637868e80e0f0017',
          'env/marginEnv.py': '8fcff5146ded428d0c12c13f36eb79c71922ef245c91986e34c49fe45100f58a',
          'env/agent.py': '5009aeebef176d8659b60d5b857c059530c189126889dbad02138fa845b704da'},
}
DATA = OUT / 'data.csv'
OUT.mkdir(parents=True, exist_ok=True); RUNS.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def replace_line(p, old, new):
    a = p.read_text().splitlines(keepends=True)
    assert sum(1 for l in a if l.rstrip('\n') == old) == 1, (p, old)
    b = [new + '\n' if l.rstrip('\n') == old else l for l in a]
    p.write_text(''.join(b))
    d = [l for l in difflib.unified_diff(a, b, n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
    assert d == ['-' + old + '\n', '+' + new + '\n'], d
    return d


def prepare(cond, seed, name):
    run = RUNS / name
    if run.exists():
        shutil.rmtree(run)
    run.mkdir(parents=True)
    subprocess.run(f'git -C {REPO} archive {COMMIT[cond]} | tar -x -C {run}', shell=True, check=True)
    diffs = []
    s = run / 'trading_margin_a2c.py'
    if cond == 'P':
        diffs += replace_line(s, "os.makedir('./datasets', exist_ok=True)", "os.makedirs('./datasets', exist_ok=True)")
    for f, h in SHA[cond].items():
        assert sha(run / f) == h, (cond, f)
    if seed != 0:
        diffs += replace_line(s, 'seed = 0', f'seed = {seed}')
    if name != 'fetch':
        (run / 'datasets').mkdir(exist_ok=True)
        shutil.copy2(DATA, run / 'datasets' / 'data.csv')
    return run, diffs


def data_info(p):
    tics, n = set(), 0
    with open(p) as f:
        for row in csv.DictReader(f):
            n += 1; tics.add(row['tic'])
    return {'sha256': sha(p), 'rows': n, 'n_tic': len(tics), 'tics': sorted(tics)}


def execute(cond, seed, name):
    done = OUT / f'{name}_done.json'
    if done.exists():
        return json.loads(done.read_text())
    for att in range(1, MAX_ATT + 1):
        rec = OUT / f'{name}_att{att}.json'
        if rec.exists():
            continue                      # 끊긴 시도도 1회로 센다
        run, diffs = prepare(cond, seed, name)
        info = {'name': name, 'cond': cond, 'commit': COMMIT[cond], 'seed': seed, 'attempt': att,
                'diff': diffs, 'start': time.strftime('%Y-%m-%d %H:%M:%S')}
        rec.write_text(json.dumps(info, ensure_ascii=False))
        code = ("import sys; sys.path.insert(0, %r); import funnel_f4_yf_shim_v2; import runpy; "
                "sys.argv=['trading_margin_a2c.py']; runpy.run_path('trading_margin_a2c.py', run_name='__main__')") % str(SHIM_DIR)
        t0 = time.time()
        with open(run / 'stdout.log', 'w') as fo, open(run / 'stderr.log', 'w') as fe:
            p = subprocess.Popen([str(PY), '-c', code], cwd=str(run), stdout=fo, stderr=fe,
                                 env=dict(os.environ, MPLBACKEND='Agg', PYTHONNOUSERSITE='1'))
            try:
                rc = p.wait(timeout=CAP); capped = False
            except subprocess.TimeoutExpired:
                p.kill(); p.wait(); rc = None; capped = True
        marker = glob.glob(str(run / 'results' / '*' / 'a2c' / 'perf_stats_trade.csv'))
        info.update({'rc': rc, 'capped': capped, 'seconds': round(time.time() - t0, 1), 'marker_exists': bool(marker)})
        d = run / 'datasets' / 'data.csv'
        if d.exists():
            info['data'] = data_info(d)
        if len(marker) == 1 and not capped:
            info['status'] = '완료' if rc == 0 else '완료(후속 오류)'
            info['result_dir'] = str(pathlib.Path(marker[0]).parent)
            if rc != 0:
                info['stderr_tail'] = (run / 'stderr.log').read_text(errors='ignore').splitlines()[-40:]
        elif capped:
            info['status'] = '상한 초과, 미완'
        else:
            info['status'] = '실패(시도)'
            info['stderr_tail'] = (run / 'stderr.log').read_text(errors='ignore').splitlines()[-40:]
        rec.write_text(json.dumps(info, ensure_ascii=False, indent=1))
        if info['status'] != '실패(시도)':
            done.write_text(json.dumps(info, ensure_ascii=False, indent=1))
            return info
    info = {'name': name, 'status': '실패(시도 3회)'}
    done.write_text(json.dumps(info, ensure_ascii=False))
    return info


def brief(r):
    return json.dumps({k: r.get(k) for k in ('name', 'status', 'rc', 'seconds')}, ensure_ascii=False)


def main():
    if not DATA.exists():
        r = execute('H', 0, 'fetch')
        print(brief(r), flush=True)
        src = RUNS / 'fetch' / 'datasets' / 'data.csv'
        if not src.exists():
            print('데이터 받기 실패 → 중단'); return
        shutil.copy2(src, DATA)
        (OUT / 'data_info.json').write_text(json.dumps(data_info(DATA), ensure_ascii=False, indent=1))
        for sub in ('results', 'trained_models', 'tensorboard_log', 'stdout.log'):   # 열지 않고 지움
            p = RUNS / 'fetch' / sub
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    for cond in ('P', 'H'):
        for s in SEEDS:
            print(brief(execute(cond, s, f'{cond}_s{s}')), flush=True)
    (OUT / 'all_done.json').write_text(json.dumps({'end': time.strftime('%Y-%m-%d %H:%M:%S')}))
    print('전부 끝', flush=True)


if __name__ == '__main__':
    main()
