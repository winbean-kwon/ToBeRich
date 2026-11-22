# -*- coding: utf-8 -*-
# 탐색적 F7x Ensemble 난류 문턱 반사실 실행. 사전 등록 notes/funnel_f7x_ensemble_turb_prereg.md 그대로.
# 서버 노트북 WSL, F7 Ensemble과 같은 환경(~/f4work/ensemble/p37). 원 clone(@f02a762)은 바꾸지 않고,
# 실행마다 새 사본의 model/models.py에서 난류 문턱 두 곳만 바꾼다
# (C: 상수 140 — 기간별 덮어쓰기 제거, T: 저자 ed22d27 규칙, O: 문턱 무한대, R: 코드 그대로 + 문턱 기록만 = P 재실행 점검).
# 그 밖의 코드·설정·래퍼는 F7 Ensemble(replication/funnel_f7_ensemble_local.py)과 같다.
# 사용: python3 funnel_f7x_ensemble_turb_run.py            (본 실행)
#       python3 funnel_f7x_ensemble_turb_run.py --patchtest <models.py 경로>  (패치만 시험, 실행 없음)
import hashlib, json, os, pathlib, shutil, signal, subprocess, sys, time

ORIG_SHA = '026987d83b620da66cabf7b7625154438eaabac766b9d1455d56da623dfeb540'  # f02a762 model/models.py

OLD_A = "    # based on the analysis of the in-sample data\n    turbulence_threshold = 140\n"
OLD_B = ("        # TODO: use a dynamic model, like moving-average or linear regression to tune the turbulence index\n"
         "        # 2018-2019\n"
         "        if (i >= 692) & (i < 1090):\n"
         "            turbulence_threshold = 100\n"
         "            # 2020\n"
         "        if i >= 1090:\n"
         "            turbulence_threshold = 90\n")

LOG = ("        import json as _j, os as _o\n"
       "        with open(_o.environ['ENS_THR'], 'a') as _f:\n"
       "            _f.write(_j.dumps({'iter': int(i), 'thr': float(turbulence_threshold), 'hist_mean': {HM}}) + '\\n')\n")

# T: 저자 출판 후 커밋 ed22d27(2020-09-27 22:15 -0400) model/models.py의 문턱 코드 그대로(주석 생략, 식 동일).
NEW_A = {
    'C': OLD_A,
    'R': OLD_A,
    'T': ("    # based on the analysis of the in-sample data\n"
          "    #turbulence_threshold = 140\n"
          "    insample_turbulence = df[(df.datadate<20151000) & (df.datadate>=20090000)]\n"
          "    insample_turbulence = insample_turbulence.drop_duplicates(subset=['datadate'])\n"
          "    insample_turbulence_threshold = np.quantile(insample_turbulence.turbulence.values, .90)\n"),
    'O': ("    # based on the analysis of the in-sample data\n"
          "    turbulence_threshold = float('inf')  # F7x 조건 O: 난류 규칙 끔\n"),
}
NEW_B = {
    'C': LOG.replace('{HM}', 'None'),
    'R': OLD_B + LOG.replace('{HM}', 'None'),
    'T': ("        # Turbulence lookback window is one quarter\n"
          "        historical_turbulence = df[(df.datadate<unique_trade_date[i - rebalance_window - validation_window]) & (df.datadate>=(unique_trade_date[i - rebalance_window - validation_window-63]))]\n"
          "        historical_turbulence = historical_turbulence.drop_duplicates(subset=['datadate'])\n"
          "        historical_turbulence_mean = np.mean(historical_turbulence.turbulence.values)\n"
          "        if historical_turbulence_mean > insample_turbulence_threshold:\n"
          "            turbulence_threshold = insample_turbulence_threshold\n"
          "        else:\n"
          "            turbulence_threshold = np.quantile(insample_turbulence.turbulence.values, 0.99)\n"
          + LOG.replace('{HM}', 'float(historical_turbulence_mean)')),
    'O': LOG.replace('{HM}', 'None'),
}


def patch(src, cond):
    assert src.count(OLD_A) == 1 and src.count(OLD_B) == 1, '패치 위치가 f02a762와 다름'
    return src.replace(OLD_A, NEW_A[cond]).replace(OLD_B, NEW_B[cond])


if sys.argv[1:2] == ['--patchtest']:
    import py_compile, tempfile
    src = open(sys.argv[2]).read()
    assert hashlib.sha256(src.encode()).hexdigest() == ORIG_SHA, '원본 해시 불일치'
    for c in ('C', 'T', 'O', 'R'):
        p = pathlib.Path(tempfile.mkdtemp()) / 'models.py'
        p.write_text(patch(src, c))
        py_compile.compile(str(p), doraise=True)
        print(c, 'patch ok', hashlib.sha256(p.read_bytes()).hexdigest())
    sys.exit(0)

HOME = pathlib.Path.home()
WORK = HOME / 'f4work' / 'ensemble'
REPO = WORK / 'repo'
PY37 = str(WORK / 'p37' / 'bin' / 'python')
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'ensemble_turb'
OUT.mkdir(parents=True, exist_ok=True)

ORDER = [f'{c}{k}' for k in range(1, 6) for c in 'CTO'] + ['R1', 'R2']  # 교대 순서(중단 시 조건별 n을 맞춤), P 재실행 점검은 마지막
CAP = 6 * 3600
MAX_ATTEMPTS = 3
START_DEADLINE = 1795705200    # 2026-11-27 00:00 KST: 첫 실행을 못 시작하면 '미시험(일정)'
STOP_AT = 1795878000           # 2026-11-29 00:00 KST: 이후 새 실행을 시작하지 않는다
ITERS = list(range(126, 1198, 63))

# out/env_ok는 2026-11-22 확인 시 없음(F7 이후 삭제 경위 미상). 다시 만들지 않고 관문 기록·파이썬만 확인, pip freeze를 기록한다.
for f in (WORK / 'out' / 'gate_ok.txt', pathlib.Path(PY37)):
    if not f.exists():
        raise SystemExit(f'환경 없음: {f}')
if hashlib.sha256((REPO / 'model' / 'models.py').read_bytes()).hexdigest() != ORIG_SHA:
    raise SystemExit('원 clone model/models.py 해시가 f02a762와 다름')
FRONTIER_PAT = 'funnel_f7x_frontier_run.py|f7_run.sh|f7_all.sh|f7_second.sh|frontier_launch'
MEM_MIN_KB = 1500 * 1024


def busy():
    """FRONTIER가 돌거나 사용 가능 메모리가 1.5GB 미만이면 이유를, 아니면 None."""
    if subprocess.run(['pgrep', '-f', FRONTIER_PAT], capture_output=True).returncode == 0:
        return 'frontier_running'
    for l in open('/proc/meminfo'):
        if l.startswith('MemAvailable:') and int(l.split()[1]) < MEM_MIN_KB:
            return 'low_memory'
    return None


def wait_free():
    """실행 전마다 호출. 바쁘면 10분마다 다시 본다. 대기 기록은 wait.jsonl."""
    while True:
        why = busy()
        if why is None:
            return True
        with open(OUT / 'wait.jsonl', 'a') as f:
            f.write(json.dumps({'t': time.time(), 'why': why}) + '\n')
        time.sleep(600)


if '--busytest' in sys.argv:
    print('busy():', busy()); sys.exit(0)

# F7 Ensemble 래퍼 그대로(시간·거래 모델 이름 기록)
RUN_PY = (pathlib.Path(__file__).resolve().parent / 'funnel_f7_ensemble_local.py').read_text()
RUN_PY = RUN_PY.split("RUN_PY = r'''", 1)[1].split("'''", 1)[0]
(OUT / 'run_ensemble_turb.py').write_text(RUN_PY)
fr = subprocess.run([PY37, '-m', 'pip', 'freeze'], capture_output=True, text=True).stdout
(OUT / 'pip_freeze.txt').write_text(fr)


def load(path):
    out = []
    if path.exists():
        for l in open(path, errors='ignore'):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def run_one(name):
    cond = name[0]
    rd = OUT / name
    rd.mkdir(exist_ok=True)
    if (rd / 'done.json').exists():
        return json.loads((rd / 'done.json').read_text())
    starts = load(rd / 'starts.jsonl')
    if len(starts) >= MAX_ATTEMPTS:
        r = {'run': name, 'status': 'failed_max_attempts', 'attempts': len(starts)}
        (rd / 'done.json').write_text(json.dumps(r, indent=1)); return r
    att = len(starts) + 1
    with open(rd / 'starts.jsonl', 'a') as f:
        f.write(json.dumps({'attempt': att, 't': time.time()}) + '\n')
    w = WORK / f'run_turb_{name}'
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(str(REPO), str(w), ignore=shutil.ignore_patterns('.git', 'trained_models', 'results'))
    mp = w / 'model' / 'models.py'
    mp.write_text(patch(mp.read_text(), cond))
    (rd / 'patched_sha.txt').write_text(hashlib.sha256(mp.read_bytes()).hexdigest() + '\n')
    times, errp, cho = rd / f'times.attempt{att}.jsonl', rd / f'error.attempt{att}.log', rd / f'chosen.attempt{att}.jsonl'
    thr = rd / f'thresholds.attempt{att}.jsonl'
    env = dict(os.environ, ENS_TIMES=str(times), ENS_ERR=str(errp), ENS_CHOSEN=str(cho), ENS_THR=str(thr))
    t0 = time.time(); killed = False
    with open(rd / f'stdout.attempt{att}.log', 'w') as fo, open(rd / f'stderr.attempt{att}.log', 'w') as fe:
        p = subprocess.Popen([PY37, str(OUT / 'run_ensemble_turb.py')], cwd=str(w), stdout=fo, stderr=fe,
                             env=env, start_new_session=True)
        while p.poll() is None:
            time.sleep(20)
            if time.time() - t0 > CAP:
                os.killpg(p.pid, signal.SIGKILL); killed = True; p.wait(); break
    rc, sec = p.returncode, time.time() - t0
    evs = [e['ev'] for e in load(times)]
    av = [w / 'results' / f'account_value_trade_ensemble_{i}.csv' for i in ITERS]
    have = [f.exists() for f in av]
    ok = (rc == 0 and not killed and 'main_end' in evs and all(have) and len(load(thr)) == len(ITERS))
    with open(rd / 'attempts.jsonl', 'a') as f:
        f.write(json.dumps({'attempt': att, 'rc': rc, 'killed_at_cap': killed, 'seconds': sec, 'ok': ok,
                            'n_account_files': sum(have), 'n_thr': len(load(thr)), 'events_tail': evs[-4:]}) + '\n')
    if ok:
        dst = rd / 'account_value'
        dst.mkdir(exist_ok=True)
        for f in av:
            shutil.copy(f, dst / f.name)
        shutil.copy(thr, rd / 'thresholds.jsonl')
        r = {'run': name, 'status': 'ok', 'attempt': att, 'seconds': sec}
    elif killed:
        r = {'run': name, 'status': 'killed_at_cap', 'attempt': att, 'seconds': sec}
    else:
        r = {'run': name, 'status': 'error', 'attempt': att, 'rc': rc}
    shutil.rmtree(w, ignore_errors=True)
    if r['status'] != 'error':
        (rd / 'done.json').write_text(json.dumps(r, indent=1))
    return r


started = any((OUT / n / 'starts.jsonl').exists() for n in ORDER)
if not started and time.time() >= START_DEADLINE:
    (OUT / 'not_started.json').write_text(json.dumps({'status': '미시험(일정)', 't': time.time()}))
    print('시작 마감(11-27 00:00 KST) 경과: 시작하지 않습니다.'); sys.exit(0)

for name in ORDER:
    while True:
        if not (OUT / name / 'done.json').exists():
            wait_free()
            if not started and time.time() >= START_DEADLINE:
                (OUT / 'not_started.json').write_text(json.dumps({'status': '미시험(일정)', 't': time.time()}))
                print('시작 마감(11-27 00:00 KST) 경과: 시작하지 않습니다.'); sys.exit(0)
            if time.time() >= STOP_AT:
                print('11-29 마감: 새 실행을 시작하지 않습니다.'); sys.exit(0)
            started = True
        r = run_one(name)
        print(json.dumps({k: r[k] for k in ('run', 'status', 'attempt') if k in r}, ensure_ascii=False), flush=True)
        if r.get('status') != 'error':
            break
(OUT / 'all_done').write_text(str(time.time()))
print('끝. 판정은 replication/funnel_f7x_ensemble_turb_judge.py')
