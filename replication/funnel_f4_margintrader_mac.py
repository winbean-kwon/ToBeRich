# -*- coding: utf-8 -*-
# Margin Trader(ICAIF 2023) F4 맥 로컬 실행. notes/funnel_f4_margintrader.md 2절 그대로.
# 저자 스크립트 trading_margin_a2c.py를 기본 인자 그대로 1회 실행(A2C 50,000스텝, seed 0, 검증·거래 구간 평가).
# 성과(표준출력·results/ 아래 CSV·그림)는 열지 않는다. 판정은 종료 코드·시간·표지 파일 존재로만 한다.
# 사용: ~/f4mac/py310/bin/python replication/funnel_f4_margintrader_mac.py
import glob, hashlib, json, os, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
REPO = HOME / 'f4mac' / 'mt'                    # JingyiGu/Margin-Trader clone
HEAD = '7b7fa9e'
PY = HOME / 'f4mac' / 'py310' / 'bin' / 'python'
SHIM_DIR = pathlib.Path(__file__).resolve().parent  # replication/ (funnel_f4_yf_shim.py)
OUT = HOME / 'f4mac' / 'out' / 'margintrader'
CAP = 3 * 3600
MAX_ATT = 3
OUT.mkdir(parents=True, exist_ok=True)

SHA = {'trading_margin_a2c.py': 'a28e3bb4e1173f7076705a613844ba83f23de3db7a79674b637868e80e0f0017',
       'env/marginEnv.py': '8fcff5146ded428d0c12c13f36eb79c71922ef245c91986e34c49fe45100f58a',
       'env/agent.py': '5009aeebef176d8659b60d5b857c059530c189126889dbad02138fa845b704da'}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    if (OUT / 'done.json').exists():
        print('이미 끝남', (OUT / 'done.json').read_text()); return
    atts = sorted(OUT.glob('attempt*.json'))
    if len(atts) >= MAX_ATT:
        (OUT / 'done.json').write_text(json.dumps({'status': 'F4 실패(시도 3회)'}, ensure_ascii=False)); return
    att = len(atts) + 1
    run = HOME / 'f4mac' / f'mt_run{att}'
    subprocess.run(['rm', '-rf', str(run)]); run.mkdir(parents=True)
    subprocess.run(f'git -C {REPO} archive {HEAD} | tar -x -C {run}', shell=True, check=True)
    for f, h in SHA.items():
        assert sha(run / f) == h, f
    (OUT / f'attempt{att}.json').write_text(json.dumps({'attempt': att, 'start': time.time()}))
    code = ("import sys; sys.path.insert(0, %r); import funnel_f4_yf_shim; import runpy; "
            "sys.argv=['trading_margin_a2c.py']; runpy.run_path('trading_margin_a2c.py', run_name='__main__')") % str(SHIM_DIR)
    t0 = time.time()
    with open(run / 'stdout.log', 'w') as fo, open(run / 'stderr.log', 'w') as fe:
        p = subprocess.Popen([str(PY), '-c', code], cwd=str(run), stdout=fo, stderr=fe,
                             env=dict(os.environ, MPLBACKEND='Agg', PYTHONNOUSERSITE='1'))
        try:
            rc = p.wait(timeout=CAP); capped = False
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(); rc = None; capped = True
    sec = time.time() - t0
    marker = bool(glob.glob(str(run / 'results' / '*' / 'a2c' / 'perf_stats_trade.csv')))   # 존재만 확인
    res = {'attempt': att, 'rc': rc, 'capped': capped, 'seconds': round(sec, 1), 'marker_exists': marker}
    data = run / 'datasets' / 'data.csv'
    if data.exists():
        import csv
        tics = set(); n = 0
        with open(data) as f:
            r = csv.DictReader(f)
            for row in r:
                n += 1; tics.add(row['tic'])
        res['data'] = {'sha256': sha(data), 'rows': n, 'n_tic': len(tics), 'tics': sorted(tics)}
    if capped:
        res['status'] = '상한 내 미완'
    elif rc == 0 and marker:
        res['status'] = 'F4 통과(저자 스크립트 기본 인자 1회)'
    else:
        res['status'] = 'F4 실패(시도)'
        res['stderr_tail'] = (run / 'stderr.log').read_text(errors='ignore').splitlines()[-40:]
    (OUT / f'attempt{att}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    if res['status'] != 'F4 실패(시도)':
        (OUT / 'done.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != 'stderr_tail'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
