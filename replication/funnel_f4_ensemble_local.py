# -*- coding: utf-8 -*-
# Ensemble(AI4Finance ICAIF-2020) F4/F5 로컬 실행. notes/funnel_f4_ensemble.md 사전 등록 그대로.
# 패키지 구조(run_DRL.py/model/models.py/env/*/preprocessing/*)를 그대로 import해서 쓰고,
# model.models의 train_A2C/train_PPO/train_DDPG/DRL_validation/DRL_prediction만 래퍼로 감싼다(허용 수정 1).
# 전체 18사이클 중 첫 사이클만 돌고 멈춘다(허용 수정 2). 성과(Sharpe 등)는 기록하지 않는다(2.1).
import json, os, pathlib, resource, shutil, signal, subprocess, sys, time

HOME = pathlib.Path.home()
WORK = HOME / 'f4work' / 'ensemble'
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'ensemble'
WORK.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
START = time.time()
(OUT / 'log.txt').open('a').write(f'start {time.ctime()}\n')

REPO = WORK / 'repo'

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
step pydeps $P install -q numpy==1.16.4 pandas==1.0.3 scikit-learn==0.21.0 gym==0.15.3 joblib==0.15.1 matplotlib==3.2.1 stockstats
step tf $P install -q tensorflow==1.15.2
step protobuf $P install -q "protobuf<3.20"
if $P install -q "stable-baselines[mpi]" > "$W/out/install_sb_mpi.log" 2>&1; then
  echo "stable-baselines[mpi] 설치 성공"; echo mpi > "$W/out/sb_variant.txt"
else
  echo "mpi 확장 실패(OpenMPI 없음 등), mpi 없이 재시도"
  step sb_plain $P install -q stable-baselines
  echo plain > "$W/out/sb_variant.txt"
fi
# stable-baselines[mpi]가 numpy/pandas/gym/matplotlib 등을 더 새 버전으로 끌어올릴 수 있어 고정 버전으로 되돌린다(허용 수정 아님, 설치 순서 보정)
step repin $P install -q --force-reinstall --no-deps numpy==1.16.4 pandas==1.0.3 gym==0.15.3 matplotlib==3.2.1 scikit-learn==0.21.0 joblib==0.15.1
[ -d "$W/repo" ] || git clone -q https://github.com/AI4Finance-LLC/Deep-Reinforcement-Learning-for-Automated-Stock-Trading-Ensemble-Strategy-ICAIF-2020.git "$W/repo"
cd "$W/repo" && git checkout -q f02a762 && git log -1 --format='%h %ad' --date=short
sha256sum run_DRL.py model/models.py | tee "$W/out/main_sha.txt"
grep -q '^a2f8261cababca92f1d11040a0631c9b5ae52d06d78d0ccfc59b8a01be4f6dd5  run_DRL.py' "$W/out/main_sha.txt" || { echo "run_DRL.py 해시가 기록과 다름"; exit 1; }
grep -q '^026987d83b620da66cabf7b7625154438eaabac766b9d1455d56da623dfeb540  model/models.py' "$W/out/main_sha.txt" || { echo "models.py 해시가 기록과 다름"; exit 1; }
touch "$W/out/env_ok"
'''

r = subprocess.run(['bash', '-c', INSTALL_SH], env=dict(os.environ, W=str(WORK)))
if r.returncode != 0:
    raise SystemExit(f'설치 실패: rc={r.returncode}')
print('설치 완료')

PY37 = str(WORK / 'p37' / 'bin' / 'python')

# ---- 관문 ----
GATE_PY = r'''
import sys, numpy, pandas, sklearn, gym, tensorflow, stockstats, py_compile
print('python', sys.version.split()[0])
print('numpy', numpy.__version__, 'pandas', pandas.__version__, 'sklearn', sklearn.__version__)
print('gym', gym.__version__, 'tensorflow', tensorflow.__version__)
assert sys.version_info[:2] == (3, 7)
assert numpy.__version__ == '1.16.4' and pandas.__version__ == '1.0.3' and sklearn.__version__ == '0.21.0' and gym.__version__ == '0.15.3' and tensorflow.__version__ == '1.15.2'
import stable_baselines
from stable_baselines import A2C, PPO2, DDPG
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv
print('stable_baselines ok', stable_baselines.__version__)
py_compile.compile('run_DRL.py', doraise=True)
py_compile.compile('model/models.py', doraise=True)
print('compile ok')
open('GATE_OK_PATH', 'w').write('1')
'''.replace('GATE_OK_PATH', str(WORK / 'out' / 'gate_ok.txt'))
(WORK / 'out' / 'gate.py').write_text(GATE_PY)
rg = subprocess.run([PY37, str(WORK / 'out' / 'gate.py')], cwd=str(REPO),
                     stdout=open(WORK / 'out' / 'install_versions.log', 'w'), stderr=subprocess.STDOUT)
print((WORK / 'out' / 'install_versions.log').read_text())
if not (WORK / 'out' / 'gate_ok.txt').exists():
    raise SystemExit('관문 실패(버전·import 확인). 설치 로그를 보고 허용 수정 2.3-4 범위에서만 고친다.')
print('관문 통과')

# ---- 실행 래퍍(모듈로 직접 import, exec 없음) ----
RUN_PY = r'''# -*- coding: utf-8 -*-
import os, sys, time, json, traceback
sys.path.insert(0, os.getcwd())
TIM = os.environ['ENS_TIMES']; ERR = os.environ['ENS_ERR']

def mark(ev, **kw):
    d = {'ev': ev, 't': time.time(), 'pid': os.getpid()}; d.update(kw)
    with open(TIM, 'a') as f: f.write(json.dumps(d) + '\n')

def err():
    with open(ERR, 'a') as f: traceback.print_exc(file=f)

class StopAfterOneCycle(Exception):
    pass

mark('run_start')
try:
    os.makedirs('trained_models', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    from preprocessing.preprocessors import preprocess_data, add_turbulence
    from model import models

    mark('preprocess_start')
    data = preprocess_data()
    data = add_turbulence(data)
    mark('preprocess_end')

    unique_trade_date = data[(data.datadate > 20151001) & (data.datadate <= 20200707)].datadate.unique()
    rebalance_window = 63
    validation_window = 63

    _orig_a2c, _orig_ppo, _orig_ddpg = models.train_A2C, models.train_PPO, models.train_DDPG
    _orig_val, _orig_pred = models.DRL_validation, models.DRL_prediction
    _calls = {'a2c': 0, 'val': 0}

    def w_a2c(env_train, model_name, timesteps=50000):
        _calls['a2c'] += 1
        if _calls['a2c'] > 1:
            raise StopAfterOneCycle()
        mark('a2c_start'); r = _orig_a2c(env_train, model_name, timesteps=timesteps); mark('a2c_end'); return r

    def w_ppo(env_train, model_name, timesteps=50000):
        mark('ppo_start'); r = _orig_ppo(env_train, model_name, timesteps=timesteps); mark('ppo_end'); return r

    def w_ddpg(env_train, model_name, timesteps=50000):
        mark('ddpg_start'); r = _orig_ddpg(env_train, model_name, timesteps=timesteps); mark('ddpg_end'); return r

    def w_val(model, test_data, test_env, test_obs):
        _calls['val'] += 1
        tag = {1: 'val_a2c', 2: 'val_ppo', 3: 'val_ddpg'}.get(_calls['val'], 'val_extra')
        mark(tag + '_start'); r = _orig_val(model, test_data, test_env, test_obs); mark(tag + '_end'); return r

    def w_pred(**kw):
        mark('trade_start'); r = _orig_pred(**kw); mark('trade_end'); return r

    models.train_A2C, models.train_PPO, models.train_DDPG = w_a2c, w_ppo, w_ddpg
    models.DRL_validation, models.DRL_prediction = w_val, w_pred

    try:
        models.run_ensemble_strategy(df=data, unique_trade_date=unique_trade_date,
                                      rebalance_window=rebalance_window, validation_window=validation_window)
    except StopAfterOneCycle:
        mark('cycle1_done')
except Exception:
    err(); mark('main_error'); raise
mark('main_end')
'''
(WORK / 'out' / 'run_ensemble.py').write_text(RUN_PY)

# ---- 측정(사전 등록 2.4) ----
CAP = 3 * 3600


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
    first = lambda e: next((x for x in ev if x['ev'] == e), None)
    rs = first('run_start')
    a2c0, a2c1 = first('a2c_start'), first('a2c_end')
    ppo0, ppo1 = first('ppo_start'), first('ppo_end')
    ddpg0, ddpg1 = first('ddpg_start'), first('ddpg_end')
    va0, va1 = first('val_a2c_start'), first('val_a2c_end')
    vp0, vp1 = first('val_ppo_start'), first('val_ppo_end')
    vd0, vd1 = first('val_ddpg_start'), first('val_ddpg_end')
    tr0, tr1 = first('trade_start'), first('trade_end')
    cycle1 = first('cycle1_done')
    d = lambda a, b: (b['t'] - a['t']) if (a and b) else None
    return {'startup': d(rs, a2c0), 'a2c': d(a2c0, a2c1), 'ppo': d(ppo0, ppo1), 'ddpg': d(ddpg0, ddpg1),
            'val_a2c': d(va0, va1), 'val_ppo': d(vp0, vp1), 'val_ddpg': d(vd0, vd1), 'trade': d(tr0, tr1),
            'cycle1_done': bool(cycle1), 'main_end': bool(first('main_end')), 'has_a2c': bool(a2c1)}


def lower_bound(m):
    # 끝난 알고리즘만으로 하한을 추정한다. 목표 스텝 대비 끝난 비율의 역수로 끊긴 알고리즘을 추정하지 않고,
    # 끝난 알고리즘의 합만 쓴다(보수적 하한, 2.5).
    parts = [m[k] for k in ('a2c', 'ppo', 'ddpg', 'val_a2c', 'val_ppo', 'val_ddpg', 'trade') if m[k] is not None]
    if m['startup'] is None or not parts:
        return None
    return (m['startup'] + 18 * sum(parts)) / 3600


def converted(m):
    keys = ('startup', 'a2c', 'ppo', 'ddpg', 'val_a2c', 'val_ppo', 'val_ddpg', 'trade')
    if any(m[k] is None for k in keys):
        return None
    return (m['startup'] + 18 * (m['a2c'] + m['ppo'] + m['ddpg'] + m['val_a2c'] + m['val_ppo'] + m['val_ddpg'] + m['trade'])) / 3600


def run(name='S'):
    fj, dt = OUT / f'f4_{name}.json', OUT / f'{name}_times.jsonl'
    if fj.exists():
        rr = json.loads(fj.read_text())
        if rr.get('f4_pass') or rr.get('killed_at_cap'):
            print(f'{name}: 끝난 기록이 있어 건너뜁니다(사전 등록 2.4)'); return rr
    prev = load_ev(dt); attempt = len(list(OUT.glob(f'{name}_times.attempt*.jsonl'))) + 1
    if prev:
        shutil.copy(dt, OUT / f'{name}_times.attempt{attempt}.jsonl'); attempt += 1
        pm = measures(prev); lb = lower_bound(pm)
        print(f'{name}: 이전 시도 기록 있음, 하한 {lb}')
        if lb is not None and lb > 10:
            rr = {'run': name, 'rc': None, 'killed_at_cap': False, 'f4_pass': False, 'hours_converted': None,
                  'hours_lower_bound': lb, 'decided_by_interrupted_attempt': True,
                  'measures': {a: b for a, b in pm.items()}}
            fj.write_text(json.dumps(rr, indent=1)); print(json.dumps(rr, indent=1)); return rr
    w = str(WORK / 'run')
    if not w or not os.path.isdir(REPO):
        raise SystemExit('repo 없음')
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(str(REPO), w, ignore=shutil.ignore_patterns('.git'))
    times, errp = str(WORK / 'out' / f'{name}_times.jsonl'), str(WORK / 'out' / f'{name}_error.log')
    for f in (times, errp):
        pathlib.Path(f).unlink(missing_ok=True)
    env = dict(os.environ, ENS_TIMES=times, ENS_ERR=errp)
    cpu0 = resource.getrusage(resource.RUSAGE_CHILDREN); t0 = time.time(); killed = False
    last_sync = t0
    cmd = [PY37, str(WORK / 'out' / 'run_ensemble.py')]
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
    ev = load_ev(times); m = measures(ev)
    rr = {'run': name, 'attempt': attempt, 'rc': rc, 'killed_at_cap': killed, 'seconds': sec,
          'f4_pass': bool(rc == 0 and m['cycle1_done'] and m['main_end']),
          **{a: m[a] for a in ('startup', 'a2c', 'ppo', 'ddpg', 'val_a2c', 'val_ppo', 'val_ddpg', 'trade')},
          'events': [x['ev'] for x in ev],
          'cpu_seconds_per_wall_second': (cpu1.ru_utime + cpu1.ru_stime - cpu0.ru_utime - cpu0.ru_stime) / sec,
          'cpu_count': os.cpu_count()}
    rr['hours_converted'] = converted(m)
    rr['hours_lower_bound'] = lower_bound(m)
    if rr['hours_lower_bound'] is None and killed and not m['has_a2c']:
        rr['hours_lower_bound'] = 18 * CAP / 3600
    se = str(WORK / 'out' / f'{name}_smoke_err.log')
    if os.path.exists(se):
        import re as _re
        keep = [l.rstrip()[:200] for l in open(se, errors='ignore')
                if _re.search(r'Traceback|Error|Killed|Segmentation|Aborted', l)
                and not _re.search(r'sharpe|portfolio|account_value|return', l, _re.I)]
        rr['stderr_filtered_tail'] = keep[-15:]
    for n in [f'{name}_times.jsonl', f'{name}_error.log', f'{name}_smoke.log', f'{name}_smoke_err.log']:
        src = str(WORK / 'out' / n)
        if os.path.exists(src):
            shutil.copy(src, OUT / n)
    fj.write_text(json.dumps(rr, indent=1))
    print(json.dumps({k2: v for k2, v in rr.items() if k2 != 'events'}, indent=1))
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
f4 = '통과(첫 사이클 기준, 전체 18사이클 중 1회만 실행)' if rS.get('f4_pass') else ('상한 내 미완' if rS.get('killed_at_cap') else '실패')
f5 += ' [장치: 서버 노트북(CPU)]'
res = {'F4': f4, 'A_hours_18cycles': A, 'A_lower_bound': A_lb, 'F5': f5, 'n_cycles_assumed': 18}
print(json.dumps(res, indent=1, ensure_ascii=False))
(OUT / 'f5_result.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print('작업 시간(시간):', round((time.time() - START) / 3600, 2))
(OUT / 'log.txt').open('a').write(f'end {time.ctime()}\n')
