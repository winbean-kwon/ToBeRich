# -*- coding: utf-8 -*-
# RAT F4/F5 로컬 이식(GTX 1650, WSL2). 원본 replication/funnel_f4_rat.ipynb(노트북)과 동일한 절차·상수.
# 변경한 것은 notes/server_gtx1650_runbook.md 3절 규칙대로 경로와 장치 판정뿐이다:
#   /content -> ~/f4work, Drive OUT -> ~/ToBeRich/data/funnel/rat_gtx1650, HAS_T4 -> HAS_GPU('GTX 1650'),
#   GPU 연산 시험 실패 시 CPU로 재지 않고 멈춘다(notes/funnel_f4_rat.md 개정 기록 2).
# 설치 명령, 버전 고정, 해시 확인, 측정 함수, 환산식, 재개 로직, 판정 칸은 노트북과 같다.
import hashlib, json, os, pathlib, resource, shutil, signal, sqlite3, subprocess, sys, time, re as _re

HOME = pathlib.Path.home()
WORK = HOME / 'f4work'
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'rat_gtx1650'
WORK.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
os.environ['MPLBACKEND'] = 'agg'
START = time.time()
(OUT / 'log.txt').open('a').write(f'start {time.ctime()}\n')

GPU_NAME = subprocess.getoutput('nvidia-smi -L')
HAS_GPU = 'GTX 1650' in GPU_NAME
print(GPU_NAME)
print('GPU 있음' if HAS_GPU else 'GPU 없음: 이 노트북에서는 측정하지 않습니다(개정 기록 2)')
if not HAS_GPU:
    raise SystemExit('nvidia-smi -L에서 GTX 1650을 찾지 못했습니다. 측정을 멈춥니다.')

# ---- 설치 (노트북 cell-2 %%bash와 같음, 경로만 WORK) ----
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
step torch $P install -q https://download.pytorch.org/whl/cu92/torch-0.4.1.post2-cp37-cp37m-linux_x86_64.whl
step pydeps $P install -q --only-binary=:all: numpy==1.16.6 pandas==0.24.2
step gdown $P install -q gdown
[ -d "$W/RAT" ] || git clone -q https://github.com/Ivsxk/RAT.git "$W/RAT"
cd "$W/RAT" && git checkout -q d1cbe96 && git log -1 --format='%h %ad' --date=short
sha256sum main.py | tee "$W/out/main_sha.txt"
grep -q '^f7ff0b45bdfe8b411e7453ee1c65f15a1976205ed82c750436efeafdf84ecc94 ' "$W/out/main_sha.txt" || { echo "main.py 해시가 기록과 다름"; exit 1; }
touch "$W/out/env_ok"
'''

r = subprocess.run(['bash', '-c', INSTALL_SH], env=dict(os.environ, W=str(WORK)))
if r.returncode != 0:
    raise SystemExit(f'설치 실패: rc={r.returncode}')
print('설치 완료')

# ---- 관문 (노트북 cell-3, GPU 연산 시험) ----
GATE_PY = r'''
import sys, numpy, pandas, torch, py_compile
print('python', sys.version.split()[0]); print('numpy', numpy.__version__, 'pandas', pandas.__version__)
print('torch', torch.__version__, 'cuda', torch.version.cuda)
assert sys.version_info[:2] == (3, 7) and torch.__version__ == '0.4.1.post2' and pandas.__version__ == '0.24.2' and numpy.__version__ == '1.16.6'
assert hasattr(pandas, 'Panel')
py_compile.compile('main.py', doraise=True); print('main.py compile ok')
ok = False
try:
    if torch.cuda.is_available():
        x = torch.randn(128, 64).cuda().requires_grad_()
        y = torch.nn.functional.softmax(torch.matmul(x, x.t()), -1)
        y = torch.nn.functional.layer_norm(y, y.shape[-1:]).masked_fill(y > 1e9, 0).sum()
        y.backward(); torch.cuda.synchronize()
        ok = bool((x.grad.abs() < float('inf')).all().item())
        print('gpu', torch.cuda.get_device_name(0), 'test ok' if ok else 'test nan')
    else:
        print('gpu not available')
except Exception as e:
    print('gpu test failed:', repr(e)[:300])
open('GPU_OK_PATH', 'w').write('1' if ok else '0')
'''.replace('GPU_OK_PATH', str(WORK / 'out' / 'gpu_ok.txt'))
(WORK / 'out' / 'gate.py').write_text(GATE_PY)
rg = subprocess.run([str(WORK / 'p37' / 'bin' / 'python'), str(WORK / 'out' / 'gate.py')],
                     cwd=str(WORK / 'RAT'),
                     stdout=open(WORK / 'out' / 'install_versions.log', 'w'),
                     stderr=subprocess.STDOUT)
print((WORK / 'out' / 'install_versions.log').read_text())
GPU_OK = (WORK / 'out' / 'gpu_ok.txt').read_text().strip() == '1'
DEVICE = 'gpu' if GPU_OK else None
if DEVICE is None:
    raise SystemExit('GPU 연산 시험을 통과하지 못했습니다. 이 노트북에서는 측정하지 않습니다(개정 기록 2, CPU 재측정 없음).')
print('DEVICE =', DEVICE)

# ---- 데이터 (노트북 cell-5) ----
z = str(WORK / 'Data.db')
zd = OUT / 'Data.db'
if not os.path.exists(z):
    if zd.exists():
        shutil.copy(zd, z)
    else:
        subprocess.run([str(WORK / 'p37' / 'bin' / 'gdown'), '1KO4Pd6qgTdtU1remUyP0rrwA8PJBQyJm', '-O', z], check=True)
        shutil.copy(z, zd)
h = hashlib.sha256(open(z, 'rb').read()).hexdigest()
first = OUT / 'data_sha_first.txt'
if not first.exists():
    first.write_text(h)
assert first.read_text().strip() == h, '데이터 해시가 첫 기록과 다릅니다'
con = sqlite3.connect(z)
n, nc, d0, d1 = con.execute('SELECT COUNT(*), COUNT(DISTINCT coin), MIN(date), MAX(date) FROM History').fetchone()
con.close()
os.makedirs(str(WORK / 'RAT' / 'database'), exist_ok=True)
shutil.copy(z, str(WORK / 'RAT' / 'database' / 'Data.db'))
info = {'size': os.path.getsize(z), 'sha256': h, 'rows': n, 'coins': nc,
        'min_date_utc': time.strftime('%Y-%m-%d %H:%M', time.gmtime(d0)), 'max_date_utc': time.strftime('%Y-%m-%d %H:%M', time.gmtime(d1))}
print(json.dumps(info, indent=1))
(OUT / 'data_info.json').write_text(json.dumps(info, indent=1))
assert d0 <= 1451577600 and d1 >= 1514736000, 'DB 기간이 코드 설정(2016-01-01~2018-01-01, +0800)을 덮지 않습니다'

# ---- 실행 래퍼 (노트북 cell-6, main.py 수정 없음) ----
WRAP = r'''# -*- coding: utf-8 -*-
# 실행 래퍼(허용 수정 1~4: 장치 지정, 입력 자르기, 결과 기록, 실행 길이). main.py는 수정하지 않는다. Python 3.7용.
import os, sys, time, json, traceback
import numpy as np
TIM = os.environ['RAT_TIMES']; ERR = os.environ['RAT_ERR']; DEV = os.environ['RAT_DEVICE']
def mark(ev, **kw):
    d = {'ev': ev, 't': time.time(), 'pid': os.getpid()}; d.update(kw)
    with open(TIM, 'a') as f: f.write(json.dumps(d) + '\n')
def err():
    with open(ERR, 'a') as f: traceback.print_exc(file=f)

src = open('main.py').read()
CUTLINE = '\nstart = parse_time(FLAGS.start)\n'
assert src.count(CUTLINE) == 1, 'split marker'
head, rest = src.split(CUTLINE)
nl = head.count('\n') + 1
tail = '\n' * nl + CUTLINE.lstrip('\n') + rest   # 줄 번호 보존
g = {'__name__': '__main__', '__file__': os.path.abspath('main.py'), '__builtins__': __builtins__}
mark('main_start', tz=list(time.tzname), argv=sys.argv[1:])
try:
    exec(compile(head, 'main.py', 'exec'), g)
    import torch
    assert not getattr(torch.cuda, '_initialized', False), 'cuda initialized before device override'
    os.environ['CUDA_VISIBLE_DEVICES'] = '0' if DEV == 'gpu' else ''
    if DEV == 'cpu':
        torch.Tensor.cuda = lambda self, *a, **k: self
        torch.nn.Module.cuda = lambda self, *a, **k: self
    FLAGS = g['FLAGS']

    HM = g['HistoryManager']; _gp = HM.get_global_panel
    def cut_panel(self, start, end, period=300, features=('close',)):
        t = time.time(); p = _gp(self, start, end, period, features)
        N = len(p.minor_axis)
        trp = 1 - FLAGS.test_portion; s = float(trp + FLAGS.test_portion)
        split = int(((np.array([trp]) / s) * N).astype(int)[0])  # 코드의 __divide_data와 같은 식
        q = p.reindex(minor_axis=p.minor_axis[:split])
        if len(q.minor_axis) != split: raise RuntimeError('cut failed')
        mark('panel', n_full=N, n_kept=split, n_orig_test=N - split, first=str(p.minor_axis[0]), last_kept=str(p.minor_axis[split - 1]),
             orig_test_first=str(p.minor_axis[split]), last=str(p.minor_axis[-1]), coins=[str(c) for c in p.major_axis],
             shape=list(q.values.shape), dtype=str(q.values.dtype), load_sec=time.time() - t)
        return q
    HM.get_global_panel = cut_panel

    DMc = g['DataMatrices']; _init = DMc.__init__
    def dm_init(self, *a, **k):
        _init(self, *a, **k)
        mark('dm', n_periods=int(self._num_periods), n_train=int(self._num_train_samples), n_fake_test=int(len(self._test_ind)),
             test_first=int(self._test_ind[0]), test_last=int(self._test_ind[-1]))
    DMc.__init__ = dm_init

    cnt = [0]
    _tos = g['train_one_step']
    def tos(*a, **k):
        if cnt[0] % 1000 == 0: mark('step', step=cnt[0])
        cnt[0] += 1
        return _tos(*a, **k)
    g['train_one_step'] = tos

    _tb = g['test_batch']
    def tb(*a, **k):
        mark('eval_start', step=cnt[0] - 1); r = _tb(*a, **k); mark('eval_end', step=cnt[0] - 1); return r
    g['test_batch'] = tb

    _ton = g['test_online']
    def ton(*a, **k):
        mark('online_start'); r = _ton(*a, **k); mark('online_end'); return r
    g['test_online'] = ton

    _tn = g['train_net']
    def tn(*a, **k):
        mark('train_start'); r = _tn(*a, **k); mark('loop_end', steps=cnt[0]); return r
    g['train_net'] = tn

    _te = g['test_net']
    def te(*a, **k):
        mark('final_start'); r = _te(*a, **k); mark('final_end'); return r
    g['test_net'] = te

    exec(compile(tail, 'main.py', 'exec'), g)
except Exception:
    err(); mark('main_error'); raise
mark('main_end')
'''
(WORK / 'out' / 'run_rat.py').write_text(WRAP)
print('wrapper ok')

# ---- 측정 (노트북 cell-7, 경로만 WORK/OUT) ----
CAP = 3 * 3600; STEPS = 2001; K = 80  # 상한, 실행 길이, 80,000스텝 = 블록 80개
ARGS = ['--total_step', str(STEPS), '--x_window_size', '31', '--batch_size', '128', '--coin_num', '11', '--feature_number', '4',
        '--output_step', '1000', '--test_portion', '0.08', '--trading_consumption', '0.0025', '--variance_penalty', '0.0',
        '--cost_penalty', '0.0', '--learning_rate', '0.0001', '--start', '2016/01/01', '--end', '2018/01/01',
        '--model_name', 'RAT', '--model_index', '1', '--model_dim', '12', '--multihead_num', '2', '--local_context_length', '5',
        '--weight_decay', '5e-8', '--daily_interest_rate', '0.001']  # run_main.sh 그대로, total_step만 2001


def load_ev(path):
    out = []
    if os.path.exists(path):
        for l in open(path, errors='ignore'):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def measures(ev):
    first = lambda e, **kw: next((x for x in ev if x['ev'] == e and all(x.get(a) == b for a, b in kw.items())), None)
    rs, m0, m1, m2 = first('run_start'), first('step', step=0), first('step', step=1000), first('step', step=2000)
    es, ee, le, fe = first('eval_start', step=1000), first('eval_end', step=1000), first('loop_end'), first('final_end')
    os_, oe, pn, dm = first('online_start'), first('online_end'), first('panel'), first('dm')
    d = lambda a, b: (b['t'] - a['t']) if (a and b) else None
    return {'device': rs['device'] if rs else None, 'startup': d(rs, m0), 'first_block': d(m0, m1), 'block': d(m1, m2), 'e': d(es, ee),
            'tail': d(le, fe), 't_on': d(os_, oe), 'n_orig_test': pn['n_orig_test'] if pn else None,
            'n_fake_test': dm['n_fake_test'] if dm else None, 'has_1000': bool(m1), 'loop_end': bool(le), 'final_end': bool(fe),
            'main_end': bool(first('main_end')), 'panel': pn, 'dm': dm}


def lower_bound(m):
    blk = m['block'] or m['first_block']
    return (m['startup'] + K * blk) / 3600 if (m['startup'] is not None and blk is not None) else None


def converted(m, k):
    if None in (m['startup'], m['block'], m['e'], m['tail'], m['t_on'], m['n_orig_test'], m['n_fake_test']):
        return None
    r_b = m['n_orig_test'] / m['n_fake_test']; r_on = (m['n_orig_test'] - 32) / (m['n_fake_test'] - 32)
    return (m['startup'] + k * ((m['block'] - m['e']) + m['e'] * r_b) + ((m['tail'] - m['t_on']) + m['t_on'] * r_on)) / 3600


def run(name='S'):
    fj, dt = OUT / f'f4_{name}.json', OUT / f'{name}_times.jsonl'
    if fj.exists():
        rr = json.loads(fj.read_text())
        if rr.get('f4_pass') or rr.get('killed_at_cap') or rr.get('decided_by_interrupted_attempt'):
            print(f'{name}: 끝난 기록이 있어 건너뜁니다(사전 등록 2.4)'); return rr
    prev = load_ev(dt); attempt = len(list(OUT.glob(f'{name}_times.attempt*.jsonl'))) + 1
    if prev:
        shutil.copy(dt, OUT / f'{name}_times.attempt{attempt}.jsonl'); attempt += 1
        pm = measures(prev); lb = lower_bound(pm)
        print(f'{name}: 이전 시도 기록 있음, 하한 {lb}')
        if lb is not None and lb > 10:
            rr = {'run': name, 'rc': None, 'killed_at_cap': False, 'f4_pass': False, 'hours_converted': None, 'hours_lower_bound': lb,
                  'decided_by_interrupted_attempt': True, 'device': pm['device'], 'measures': {a: b for a, b in pm.items() if a not in ('panel', 'dm')}}
            fj.write_text(json.dumps(rr, indent=1)); print(json.dumps(rr, indent=1)); return rr
    w = str(WORK / f'run_{name}')
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(str(WORK / 'RAT'), w, ignore=shutil.ignore_patterns('.git', 'database'))
    os.symlink(str(WORK / 'RAT' / 'database'), w + '/database')
    os.makedirs(w + '/log', exist_ok=True); os.makedirs(w + '/model', exist_ok=True)
    times, errp = str(WORK / 'out' / f'{name}_times.jsonl'), str(WORK / 'out' / f'{name}_error.log')
    for f in (times, errp):
        pathlib.Path(f).unlink(missing_ok=True)
    env = dict(os.environ, RAT_TIMES=times, RAT_ERR=errp, RAT_DEVICE=DEVICE, TZ='Asia/Shanghai', LANG='en_US.UTF-8', MPLBACKEND='agg')
    gpu_f = open(str(WORK / 'out' / f'{name}_gpu.csv'), 'w')
    sampler = subprocess.Popen(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits', '-l', '1'],
                                stdout=gpu_f) if DEVICE == 'gpu' else None
    cpu0 = resource.getrusage(resource.RUSAGE_CHILDREN); t0 = time.time(); killed = False
    with open(times, 'a') as f:
        f.write(json.dumps({'ev': 'run_start', 't': t0, 'device': DEVICE, 'attempt': attempt}) + '\n')
    shutil.copy(times, dt); last_sync = t0
    cmd = [str(WORK / 'p37' / 'bin' / 'python'), str(WORK / 'out' / 'run_rat.py')] + ARGS + ['--model_dir', w + '/model', '--log_dir', w + '/log']
    with open(str(WORK / 'out' / f'{name}_smoke.log'), 'w') as f, open(str(WORK / 'out' / f'{name}_smoke_err.log'), 'w') as g:
        p = subprocess.Popen(cmd, cwd=w, stdout=f, stderr=g, env=env, start_new_session=True)
        while p.poll() is None:
            time.sleep(10)
            if time.time() - last_sync > 60:
                last_sync = time.time()
                try:
                    shutil.copy(times, dt)
                except OSError:
                    pass
            if time.time() - t0 > CAP:
                os.killpg(p.pid, signal.SIGKILL); killed = True; p.wait(); break
    rc = p.returncode; sec = time.time() - t0
    cpu1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    gpu_f.close()
    if sampler:
        sampler.terminate(); sampler.wait()
    smp = [[float(x) for x in l.split(',')] for l in open(str(WORK / 'out' / f'{name}_gpu.csv')) if l.count(',') == 1 and '[' not in l]
    ev = load_ev(times); m = measures(ev)
    summary = os.path.exists(w + '/log/train_summary.csv')
    rr = {'run': name, 'attempt': attempt, 'rc': rc, 'killed_at_cap': killed, 'seconds': sec,
          'f4_pass': bool(rc == 0 and m['loop_end'] and m['final_end'] and m['main_end'] and summary), 'train_summary_exists': summary,
          **{a: m[a] for a in ('startup', 'first_block', 'block', 'e', 'tail', 't_on', 'n_orig_test', 'n_fake_test')},
          'panel': m['panel'], 'dm': m['dm'], 'events': [x['ev'] for x in ev],
          'cpu_seconds_per_wall_second': (cpu1.ru_utime + cpu1.ru_stime - cpu0.ru_utime - cpu0.ru_stime) / sec, 'cpu_count': os.cpu_count(),
          'gpu_util_mean': (sum(x[0] for x in smp) / len(smp) if smp else None), 'gpu_mem_mb_max': (max(x[1] for x in smp) if smp else None),
          'device': DEVICE, 'gpu': GPU_NAME, 'args': ARGS}
    rr['hours_converted'] = converted(m, K)
    rr['hours_repo_50000'] = converted(m, 50)
    rr['hours_lower_bound'] = lower_bound(m)
    if rr['hours_lower_bound'] is None and killed and not m['has_1000']:
        rr['hours_lower_bound'] = K * CAP / 3600
    se = str(WORK / 'out' / f'{name}_smoke_err.log')
    if os.path.exists(se):
        keep = [l.rstrip()[:200] for l in open(se, errors='ignore')
                if _re.search(r'Traceback|Error|Killed|CUDA|OOM|Segmentation|Aborted', l)
                and not _re.search(r'portfolio|log.?mean|loss|pv|value|benefit|fAPV|SR|CR', l, _re.I)]
        rr['stderr_filtered_tail'] = keep[-15:]
    for n in [f'{name}_times.jsonl', f'{name}_error.log', f'{name}_gpu.csv', f'{name}_smoke.log', f'{name}_smoke_err.log']:
        src = str(WORK / 'out' / n)
        if os.path.exists(src):
            shutil.copy(src, OUT / n)
    fj.write_text(json.dumps(rr, indent=1))
    print(json.dumps({k2: v for k2, v in rr.items() if k2 not in ('args',)}, indent=1))
    if os.path.exists(errp):
        print('--- traceback(마지막 30줄) ---'); print(''.join(open(errp).readlines()[-30:]))
    return rr


rS = run('S')

# ---- 판정 (노트북 cell-8, 장치 표기만 GTX 1650) ----
A, A_lb, B = rS.get('hours_converted'), rS.get('hours_lower_bound'), rS.get('hours_repo_50000')
if A is not None:
    f5 = '한도 초과' if A > 10 else '통과(멈추고 사용자 보고 후 F7 사전 등록)'
elif A_lb is not None and A_lb > 10:
    f5 = '한도 초과(하한 기준)'
else:
    f5 = 'F5 측정 실패'
f4 = '통과(가짜 시험 구간 기준, 원 시험 구간 미실행)' if rS.get('f4_pass') else ('상한 내 미완' if rS.get('killed_at_cap') else '실패')
f5 += ' [장치: GTX 1650(노트북)]'
res = {'F4': f4, 'A_hours_paper_80000': A, 'A_lower_bound': A_lb, 'B_hours_repo_50000(참고)': B, 'device': rS.get('device'), 'F5': f5}
print(json.dumps(res, indent=1, ensure_ascii=False))
(OUT / 'f5_result.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print('작업 시간(시간):', round((time.time() - START) / 3600, 2))
(OUT / 'log.txt').open('a').write(f'end {time.ctime()}\n')
