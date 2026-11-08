# -*- coding: utf-8 -*-
# WaveCorr F4/F5 로컬 실행. notes/funnel_f4_wavecorr.md 사전 등록 그대로.
# wavecorr_run.py를 exec로 split해서 하이퍼파라미터 정의까지만 돌리고(허용 수정 1),
# epochs를 두 값(5, 25)으로 바꿔 runSingleExperiment를 2회만 호출해 1에폭당 시간을 추정한다(허용 수정 2).
import json, os, pathlib, resource, shutil, signal, subprocess, sys, time

HOME = pathlib.Path.home()
WORK = HOME / 'f4work' / 'wavecorr'
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'wavecorr'
WORK.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
START = time.time()
(OUT / 'log.txt').open('a').write(f'start {time.ctime()}\n')

REPO = WORK / 'repo'
HASHES = {
    'src/wavecorr_run.py': 'dbad7de02a87339dd2991ec2def926c81786920b6974b0c0896760f650436d3b',
    'src/wavecorr_agent.py': '1b9e83c18e339fdefc673e4409251a0e6886025e241bde2e52511cac34fc7193',
    'src/wavecorr_network.py': '69ee695e28c92c76861689e453f556045d75f1b1fe5e8d195d35742d67516559',
    'src/wavecorr_input.py': 'a5c3eaf90cf4281a1094d6c74283b743f412a1f2b6584a57ebf6e56e516252ae',
    'src/wavecorr_enum.py': '7df5a5ccee48c40293ac68547d63acf48258b351a1c0dd990485782a5285c2a5',
}

INSTALL_SH = r'''
set -e
mkdir -p "$W/out"
if [ -f "$W/out/env_ok" ]; then echo "환경이 이미 있음, 설치 건너뜀"; exit 0; fi
rm -rf "$W/p37"
step(){ n=$1; shift; echo "== $n"; if ! "$@" > "$W/out/install_$n.log" 2>&1; then echo "실패: $n"; tail -25 "$W/out/install_$n.log"; exit 1; fi; tail -1 "$W/out/install_$n.log"; }
cd "$W"
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
step py37 ./bin/micromamba create -y -p "$W/p37" -c conda-forge python=3.7 pip
P="$W/p37/bin/python -m pip --default-timeout=120 --retries 5"
step pydeps $P install -q pandas==0.24.2 numpy==1.18.5 Keras==2.3.1
step tf $P install -q tensorflow==1.14.0
[ -d "$W/repo" ] || git clone -q https://github.com/saeedmarzban/waveCorr.git "$W/repo"
cd "$W/repo" && git checkout -q 20ff832 && git log -1 --format='%h %ad' --date=short
touch "$W/out/env_ok"
'''

r = subprocess.run(['bash', '-c', INSTALL_SH], env=dict(os.environ, W=str(WORK)))
if r.returncode != 0:
    raise SystemExit(f'설치 실패: rc={r.returncode}')
print('설치 완료')

PY37 = str(WORK / 'p37' / 'bin' / 'python')

# ---- 관문: 버전·import·해시 ----
bad = []
for rel, h in HASHES.items():
    fp = REPO / rel
    import hashlib
    actual = hashlib.sha256(fp.read_bytes()).hexdigest()
    if actual != h:
        bad.append((rel, actual, h))
if bad:
    for rel, actual, h in bad:
        print(f'해시 불일치: {rel} actual={actual} expected={h}')
    raise SystemExit('해시 확인 실패, 측정하지 않는다')
print('해시 확인 통과')

GATE_PY = r'''
import sys, numpy, pandas, tensorflow, keras, py_compile
print('python', sys.version.split()[0])
print('numpy', numpy.__version__, 'pandas', pandas.__version__, 'tensorflow', tensorflow.__version__, 'keras', keras.__version__)
assert sys.version_info[:2] == (3, 7)
assert numpy.__version__ == '1.18.5' and pandas.__version__ == '0.24.2' and tensorflow.__version__ == '1.14.0' and keras.__version__ == '2.3.1'
py_compile.compile('wavecorr_run.py', doraise=True)
py_compile.compile('wavecorr_agent.py', doraise=True)
py_compile.compile('wavecorr_network.py', doraise=True)
py_compile.compile('wavecorr_input.py', doraise=True)
py_compile.compile('wavecorr_enum.py', doraise=True)
print('compile ok')
open('GATE_OK_PATH', 'w').write('1')
'''.replace('GATE_OK_PATH', str(WORK / 'out' / 'gate_ok.txt'))
(WORK / 'out' / 'gate.py').write_text(GATE_PY)
rg = subprocess.run([PY37, str(WORK / 'out' / 'gate.py')], cwd=str(REPO / 'src'),
                     stdout=open(WORK / 'out' / 'install_versions.log', 'w'), stderr=subprocess.STDOUT)
print((WORK / 'out' / 'install_versions.log').read_text())
if not (WORK / 'out' / 'gate_ok.txt').exists():
    raise SystemExit('관문 실패(버전·import·compile 확인)')
print('관문 통과')

# ---- 실행 래퍍: wavecorr_run.py를 exec로 split, epochs만 오버라이드 ----
CALIB_PY = r'''# -*- coding: utf-8 -*-
import os, sys, time, json, traceback
sys.path.insert(0, os.getcwd())
TIM = os.environ['WC_TIMES']; ERR = os.environ['WC_ERR']; EPOCHS = int(os.environ['WC_EPOCHS']); TAG = os.environ['WC_TAG']

def mark(ev, **kw):
    d = {'ev': ev, 't': time.time(), 'pid': os.getpid()}; d.update(kw)
    with open(TIM, 'a') as f: f.write(json.dumps(d) + '\n')

def err():
    with open(ERR, 'a') as f: traceback.print_exc(file=f)

src = open('wavecorr_run.py', encoding='utf-8').read()
CUTLINE = "\n# load the data from the assigned data set\n"
assert src.count(CUTLINE) == 1, 'split marker'
head, rest = src.split(CUTLINE)

mark(TAG + '_start')
try:
    g = {'__name__': 'wavecorr_run_head', '__builtins__': __builtins__}
    exec(compile(head, 'wavecorr_run.py', 'exec'), g)
    g['epochs'] = EPOCHS
    g['train_mode'] = 0  # 파일 끝의 10회 자동 디스패치(if train_mode==1/2)를 막는다. 아래서 1회만 직접 부른다.
    tail = CUTLINE.lstrip('\n') + rest
    exec(compile(tail, 'wavecorr_run.py', 'exec'), g)
    g['runSingleExperiment'](g['seed'], 1)
except Exception:
    err(); mark(TAG + '_error'); raise
mark(TAG + '_end')
'''
(WORK / 'out' / 'calib.py').write_text(CALIB_PY)

CAP = 3 * 3600
E1, E2 = 5, 25


def run_calib(tag, epochs, times_path, err_path, deadline):
    env = dict(os.environ, WC_TIMES=times_path, WC_ERR=err_path, WC_EPOCHS=str(epochs), WC_TAG=tag)
    remaining = deadline - time.time()
    if remaining <= 0:
        return None, False
    t0 = time.time()
    with open(str(WORK / 'out' / f'{tag}_smoke.log'), 'w') as f, open(str(WORK / 'out' / f'{tag}_smoke_err.log'), 'w') as g:
        p = subprocess.Popen([PY37, str(WORK / 'out' / 'calib.py')], cwd=str(REPO / 'src'), stdout=f, stderr=g, env=env, start_new_session=True)
        killed = False
        while p.poll() is None:
            time.sleep(5)
            if time.time() > deadline:
                os.killpg(p.pid, signal.SIGKILL); killed = True; p.wait(); break
    return p.returncode, killed


def load_ev(path):
    out = []
    if os.path.exists(path):
        for l in open(path, errors='ignore'):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def run(name='S'):
    fj = OUT / f'f4_{name}.json'
    if fj.exists():
        rr = json.loads(fj.read_text())
        if rr.get('f4_pass') or rr.get('killed_at_cap'):
            print(f'{name}: 끝난 기록이 있어 건너뜁니다(사전 등록 2.4)'); return rr
    times, errp = str(WORK / 'out' / f'{name}_times.jsonl'), str(WORK / 'out' / f'{name}_error.log')
    dt = OUT / f'{name}_times.jsonl'
    for f in (times, errp):
        pathlib.Path(f).unlink(missing_ok=True)
    deadline = time.time() + CAP
    cpu0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    rc1, killed1 = run_calib('calib1', E1, times, errp, deadline)
    try:
        shutil.copy(times, dt)
    except OSError:
        pass
    rc2, killed2 = (None, False)
    if not killed1 and rc1 == 0:
        rc2, killed2 = run_calib('calib2', E2, times, errp, deadline)
    cpu1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    ev = load_ev(times)
    first = lambda e: next((x for x in ev if x['ev'] == e), None)
    c1s, c1e = first('calib1_start'), first('calib1_end')
    c2s, c2e = first('calib2_start'), first('calib2_end')
    d = lambda a, b: (b['t'] - a['t']) if (a and b) else None
    T1, T2 = d(c1s, c1e), d(c2s, c2e)
    killed = bool(killed1 or killed2)
    rc = 0 if (rc1 == 0 and rc2 == 0) else (rc1 if rc1 != 0 else rc2)
    f4_pass = bool(rc1 == 0 and rc2 == 0 and T1 is not None and T2 is not None)
    rr = {'run': name, 'rc': rc, 'killed_at_cap': killed, 'f4_pass': f4_pass, 'T1_epochs5': T1, 'T2_epochs25': T2,
          'cpu_seconds_per_wall_second': (cpu1.ru_utime + cpu1.ru_stime - cpu0.ru_utime - cpu0.ru_stime) / max(time.time() - (deadline - CAP), 1),
          'cpu_count': os.cpu_count()}
    if T1 is not None and T2 is not None:
        p_per_epoch = (T2 - T1) / (E2 - E1)
        startup = T1 - E1 * p_per_epoch
        rr['p_per_epoch'] = p_per_epoch
        rr['startup'] = startup
        rr['hours_converted'] = 10 * (startup + 3000 * p_per_epoch) / 3600
        rr['hours_lower_bound'] = None
    elif T1 is not None:
        rr['hours_converted'] = None
        rr['hours_lower_bound'] = 10 * (T1 / E1) * 3000 / 3600
    else:
        rr['hours_converted'] = None
        rr['hours_lower_bound'] = 10 * CAP / 3600 if killed1 else None
    se = str(WORK / 'out' / 'calib2_smoke_err.log')
    if os.path.exists(se):
        import re as _re
        keep = [l.rstrip()[:200] for l in open(se, errors='ignore')
                if _re.search(r'Traceback|Error|Killed|Segmentation|Aborted', l)
                and not _re.search(r'sharpe|portfolio|reward|return\b', l, _re.I)]
        rr['stderr_filtered_tail'] = keep[-15:]
    for n in [f'{name}_times.jsonl', f'{name}_error.log', 'calib1_smoke.log', 'calib1_smoke_err.log', 'calib2_smoke.log', 'calib2_smoke_err.log']:
        src = str(WORK / 'out' / n)
        if os.path.exists(src):
            shutil.copy(src, OUT / n)
    fj.write_text(json.dumps(rr, indent=1))
    print(json.dumps(rr, indent=1))
    if os.path.exists(errp):
        print('--- traceback(마지막 30줄) ---'); print(''.join(open(errp).readlines()[-30:]))
    return rr


rS = run('S')

# ---- 판정 (사전 등록 2.5) ----
A, A_lb = rS.get('hours_converted'), rS.get('hours_lower_bound')
if A is not None:
    f5 = '한도 초과' if A > 10 else '통과(멈추고 사용자 보고 후 F7 사전 등록)'
elif A_lb is not None and A_lb > 10:
    f5 = '한도 초과(하한 기준)'
else:
    f5 = 'F5 측정 실패'
f4 = '통과(2점 보정 기준, 3000에폭·10회 전체 미실행)' if rS.get('f4_pass') else ('상한 내 미완' if rS.get('killed_at_cap') else '실패')
f5 += ' [장치: 서버 노트북(CPU)]'
res = {'F4': f4, 'A_hours_10runs': A, 'A_lower_bound': A_lb, 'F5': f5, 'E1': 5, 'E2': 25}
print(json.dumps(res, indent=1, ensure_ascii=False))
(OUT / 'f5_result.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print('작업 시간(시간):', round((time.time() - START) / 3600, 2))
(OUT / 'log.txt').open('a').write(f'end {time.ctime()}\n')
