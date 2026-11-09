# -*- coding: utf-8 -*-
# Ensemble(AI4Finance ICAIF-2020 @f02a762) F7 본 실행. 사전 등록 notes/funnel_f7_ensemble_prereg.md 그대로.
# 서버 노트북 WSL, F4·F5와 같은 환경(~/f4work/ensemble/p37, 관문 통과 기록 env_ok·gate_ok 필요).
# 저장소 코드를 수정하지 않고 run_ensemble_strategy 전체(18사이클)를 실행한다. 래퍼는 시간 표시와
# 거래에 쓰인 모델 이름만 기록한다. 표준출력(Sharpe 등)·results/는 파일로만 보내고 화면에 내지 않는다.
import json, os, pathlib, shutil, signal, subprocess, sys, time

HOME = pathlib.Path.home()
WORK = HOME / 'f4work' / 'ensemble'
REPO = WORK / 'repo'
PY37 = str(WORK / 'p37' / 'bin' / 'python')
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'ensemble_f7'
OUT.mkdir(parents=True, exist_ok=True)

N_RUNS = 5
CAP = 6 * 3600                 # 실행당 벽시계 상한(F5 A=1.12h의 약 5배). 넘으면 미완, 재실행 없음
MAX_ATTEMPTS = 3               # 같은 실행의 오류 시도 최대 횟수
START_DEADLINE = 1794322800    # 2026-11-11 00:00 KST: 첫 실행을 이때까지 시작하지 못하면 '미시험(일정)'(프로토콜 3.3-4)
STOP_AT = 1795532400           # 2026-11-25 00:00 KST: 이후 새 실행을 시작하지 않는다
ITERS = list(range(126, 1198, 63))  # 18사이클(F4 1절에서 번들 데이터로 집계)

for f in (WORK / 'out' / 'env_ok', WORK / 'out' / 'gate_ok.txt', pathlib.Path(PY37)):
    if not f.exists():
        raise SystemExit(f'F4 환경 없음: {f}')
sha = subprocess.run(['sha256sum', 'run_DRL.py', 'model/models.py', 'env/EnvMultipleStock_trade.py'],
                     cwd=str(REPO), capture_output=True, text=True).stdout
for h in ('a2f8261cababca92f1d11040a0631c9b5ae52d06d78d0ccfc59b8a01be4f6dd5  run_DRL.py',
          '026987d83b620da66cabf7b7625154438eaabac766b9d1455d56da623dfeb540  model/models.py'):
    if h not in sha:
        raise SystemExit('저장소 해시가 F4 기록과 다름')
(OUT / 'repo_sha.txt').write_text(sha)

RUN_PY = r'''# -*- coding: utf-8 -*-
import os, sys, time, json, traceback
sys.path.insert(0, os.getcwd())
TIM = os.environ['ENS_TIMES']; ERR = os.environ['ENS_ERR']; CHO = os.environ['ENS_CHOSEN']

def mark(ev, **kw):
    d = {'ev': ev, 't': time.time()}; d.update(kw)
    with open(TIM, 'a') as f: f.write(json.dumps(d) + '\n')

mark('run_start')
try:
    os.makedirs('trained_models', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    import numpy as np
    mark('np_seed_state', head=int(np.random.get_state()[1][0]))
    from preprocessing.preprocessors import preprocess_data, add_turbulence
    from model import models

    data = preprocess_data()
    data = add_turbulence(data)
    mark('preprocess_end')
    unique_trade_date = data[(data.datadate > 20151001) & (data.datadate <= 20200707)].datadate.unique()

    _o = {'a2c': models.train_A2C, 'ppo': models.train_PPO, 'ddpg': models.train_DDPG, 'pred': models.DRL_prediction}
    _last = {}

    def _wrap(name):
        def f(env_train, model_name, timesteps=50000):
            mark(name + '_start'); m = _o[name](env_train, model_name, timesteps=timesteps); mark(name + '_end')
            _last[name] = m; return m
        return f

    def w_pred(**kw):
        used = next((k for k, v in _last.items() if v is kw.get('model')), 'unknown')
        with open(CHO, 'a') as f: f.write(json.dumps({'iter': kw.get('iter_num'), 'model': used}) + '\n')
        mark('trade_start', iter=kw.get('iter_num'))
        r = _o['pred'](**kw)
        mark('trade_end', iter=kw.get('iter_num'))
        return r

    models.train_A2C, models.train_PPO, models.train_DDPG = _wrap('a2c'), _wrap('ppo'), _wrap('ddpg')
    models.DRL_prediction = w_pred
    models.run_ensemble_strategy(df=data, unique_trade_date=unique_trade_date, rebalance_window=63, validation_window=63)
except Exception:
    with open(ERR, 'a') as f: traceback.print_exc(file=f)
    mark('main_error'); raise
mark('main_end')
'''
(OUT / 'run_ensemble_f7.py').write_text(RUN_PY)


def load(path):
    out = []
    if path.exists():
        for l in open(path, errors='ignore'):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def run_one(idx):
    rd = OUT / f'E{idx}'
    rd.mkdir(exist_ok=True)
    if (rd / 'done.json').exists():
        return json.loads((rd / 'done.json').read_text())
    # 시도 횟수는 시작 기록(starts.jsonl)으로 센다. 재부팅·강제 종료로 끝 기록이 없는 시도도 센다.
    starts = load(rd / 'starts.jsonl')
    if len(starts) >= MAX_ATTEMPTS:
        r = {'run': f'E{idx}', 'status': 'failed_max_attempts', 'attempts': len(starts)}
        (rd / 'done.json').write_text(json.dumps(r, indent=1)); return r
    att = len(starts) + 1
    with open(rd / 'starts.jsonl', 'a') as f:
        f.write(json.dumps({'attempt': att, 't': time.time()}) + '\n')
    w = WORK / f'run_f7_E{idx}'
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(str(REPO), str(w), ignore=shutil.ignore_patterns('.git', 'trained_models', 'results'))
    times, errp, cho = rd / f'times.attempt{att}.jsonl', rd / f'error.attempt{att}.log', rd / f'chosen.attempt{att}.jsonl'
    env = dict(os.environ, ENS_TIMES=str(times), ENS_ERR=str(errp), ENS_CHOSEN=str(cho))
    t0 = time.time(); killed = False
    with open(rd / f'stdout.attempt{att}.log', 'w') as fo, open(rd / f'stderr.attempt{att}.log', 'w') as fe:
        p = subprocess.Popen([PY37, str(OUT / 'run_ensemble_f7.py')], cwd=str(w), stdout=fo, stderr=fe,
                             env=env, start_new_session=True)
        while p.poll() is None:
            time.sleep(20)
            if time.time() - t0 > CAP:
                os.killpg(p.pid, signal.SIGKILL); killed = True; p.wait(); break
    rc, sec = p.returncode, time.time() - t0
    evs = [e['ev'] for e in load(times)]
    av = [w / 'results' / f'account_value_trade_ensemble_{i}.csv' for i in ITERS]
    have = [f.exists() for f in av]
    ok = (rc == 0 and not killed and 'main_end' in evs and all(have))
    with open(rd / 'attempts.jsonl', 'a') as f:
        f.write(json.dumps({'attempt': att, 'rc': rc, 'killed_at_cap': killed, 'seconds': sec, 'ok': ok,
                            'n_account_files': sum(have), 'events_tail': evs[-4:]}) + '\n')
    if ok:
        dst = rd / 'account_value'
        dst.mkdir(exist_ok=True)
        for f in av:
            shutil.copy(f, dst / f.name)
        r = {'run': f'E{idx}', 'status': 'ok', 'attempt': att, 'seconds': sec}
    elif killed:
        r = {'run': f'E{idx}', 'status': 'killed_at_cap', 'attempt': att, 'seconds': sec}
    else:
        r = {'run': f'E{idx}', 'status': 'error', 'attempt': att, 'rc': rc}
    shutil.rmtree(w, ignore_errors=True)  # 작업 폴더·모델 파일 정리(판정에 쓰지 않음, 디스크 절약)
    if r['status'] != 'error':
        (rd / 'done.json').write_text(json.dumps(r, indent=1))
    return r


started = any((OUT / f'E{k}' / 'starts.jsonl').exists() for k in range(1, N_RUNS + 1))
if not started and time.time() >= START_DEADLINE:
    (OUT / 'not_started.json').write_text(json.dumps({'status': '미시험(일정)', 't': time.time()}))
    print('F7 시작 마감(11-10) 경과: 시작하지 않습니다(미시험(일정)).'); sys.exit(0)

for idx in range(1, N_RUNS + 1):
    while True:
        if not (OUT / f'E{idx}' / 'done.json').exists() and time.time() >= STOP_AT:
            print('11-24 마감: 새 실행을 시작하지 않습니다.'); sys.exit(0)
        r = run_one(idx)
        print(json.dumps({k: r[k] for k in ('run', 'status', 'attempt') if k in r}, ensure_ascii=False), flush=True)
        if r.get('status') != 'error':
            break
print('Ensemble F7 전체 실행 끝. 판정은 replication/funnel_f7_ensemble_judge.py')
