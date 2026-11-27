# -*- coding: utf-8 -*-
# Ensemble 출판 이후 검정 — 탐색판(WBA 제외 29종목) 실행기. 사전 등록 notes/ensemble_postpub_29_prereg.md(33f5819),
# 주 사전 등록 notes/ensemble_postpub_prereg.md 1장. replication/funnel_f7_ensemble_local.py를 복사해 다음만 바꿨다.
#   (i)  데이터 파일: config.TRAINING_DATA_FILE을 실행 시 새 CSV(~/f4work/postpub29/dow_29_2009_2025.csv)로 지정.
#   (ii) unique_trade_date: 새 데이터에서 datadate > 20200707 이고 ≤ 종료일(END, 데이터 마지막 날)인 거래일.
#        사이클 ITERS = range(126, len(unique_trade_date), 63)(코드 루프 그대로)를 데이터에서 계산해 기록한다.
#   (iii) 출력 폴더: ~/f4work/postpub29/out/E1..E5, 작업 사본: ~/f4work/postpub29/run_E{k}.
#   (iv) STOCK_DIM = 29(탐색판): env 세 모듈(train·validation·trade)을 가져올 때 저장소 파일은 고치지 않고, 파일 원문을
#        읽어 메모리에서 아래 세 가지만 바꿔 컴파일한 모듈을 sys.modules에 먼저 넣는다(models.py가 그 모듈을 쓴다).
#          'STOCK_DIM = 30\n' → 'STOCK_DIM = 29\n'           (각 파일 1곳)
#          'shape = (181,)'   → 'shape = (6*STOCK_DIM+1,)'  (관측 차원 1+29·6 = 175, 각 파일 1곳)
#          ':61]'             → ':(STOCK_DIM*2+1)]'          (보유 주식 조각의 상수 끝 61 = 2·30+1; train 4곳,
#                                                             validation 1곳(주석), trade 1곳(종료 시 print))
#        모듈 상수만 덮어쓰면 181·61이 30종목 값으로 남아 상태 길이가 어긋나므로, 맞물린 상태 차원 상수를 함께 바꾼다.
#        바꾼 개수가 위와 다르면 시작하지 않는다. 모델·난류 문턱(140/100/90, 사이클 인덱스) 코드는 그대로다.
# 시작·종료 기한(F7의 START_DEADLINE·STOP_AT)은 지난 날짜라 뺐다. 실행당 6시간 상한, 오류 시 최대 3회 시도는 그대로.
# 서버 C: 여유가 3GB 미만이면 새 실행을 시작하지 않는다(Windows 쪽 확인은 맥 감시 루프가 한다).
# 사용(WSL): python3 ensemble_postpub29_run.py   (같은 폴더에 dow_29_2009_2025.csv)
import csv, json, os, pathlib, shutil, signal, subprocess, sys, time

HOME = pathlib.Path.home()
WORK = HOME / 'f4work' / 'ensemble'
REPO = WORK / 'repo'
PY37 = str(WORK / 'p37' / 'bin' / 'python')
PP = HOME / 'f4work' / 'postpub29'
DATA = PP / 'dow_29_2009_2025.csv'
OUT = PP / 'out'
OUT.mkdir(parents=True, exist_ok=True)

N_RUNS = 5
CAP = 6 * 3600
MAX_ATTEMPTS = 3

for f in (WORK / 'out' / 'env_ok', WORK / 'out' / 'gate_ok.txt', pathlib.Path(PY37), DATA):
    if not f.exists():
        raise SystemExit(f'환경·데이터 없음: {f}')
sha = subprocess.run(['sha256sum', 'run_DRL.py', 'model/models.py', 'env/EnvMultipleStock_trade.py',
                      'env/EnvMultipleStock_train.py', 'env/EnvMultipleStock_validation.py',
                      'preprocessing/preprocessors.py', 'config/config.py'],
                     cwd=str(REPO), capture_output=True, text=True).stdout
for h in ('a2f8261cababca92f1d11040a0631c9b5ae52d06d78d0ccfc59b8a01be4f6dd5  run_DRL.py',
          '026987d83b620da66cabf7b7625154438eaabac766b9d1455d56da623dfeb540  model/models.py'):
    if h not in sha:
        raise SystemExit('저장소 해시가 F4 기록과 다름')
(OUT / 'repo_sha.txt').write_text(sha)

dates = sorted({int(r['datadate']) for r in csv.DictReader(open(DATA))})
END = dates[-1]
UTD = [d for d in dates if 20200707 < d <= END]
ITERS = list(range(126, len(UTD), 63))
ticn = {}
for r in csv.DictReader(open(DATA)):
    ticn[r['datadate']] = ticn.get(r['datadate'], 0) + 1
if set(ticn.values()) != {29}:
    raise SystemExit('날마다 29종목이 아님')
(OUT / 'plan.json').write_text(json.dumps({'END': END, 'n_utd': len(UTD), 'utd_first': UTD[0], 'utd_last': UTD[-1],
                                           'ITERS': ITERS, 'n_days_total': len(dates),
                                           'data_sha256': subprocess.run(['sha256sum', str(DATA)], capture_output=True,
                                                                         text=True).stdout.split()[0]}, indent=1))

RUN_PY = r'''# -*- coding: utf-8 -*-
import os, sys, time, json, traceback, importlib.util, hashlib
sys.path.insert(0, os.getcwd())
TIM = os.environ['ENS_TIMES']; ERR = os.environ['ENS_ERR']; CHO = os.environ['ENS_CHOSEN']
DATA = os.environ['ENS_DATA']; END = int(os.environ['ENS_END'])

def mark(ev, **kw):
    d = {'ev': ev, 't': time.time()}; d.update(kw)
    with open(TIM, 'a') as f: f.write(json.dumps(d) + '\n')

PATCH = [('STOCK_DIM = 30\n', 'STOCK_DIM = 29\n'), ('shape = (181,)', 'shape = (6*STOCK_DIM+1,)'),
         (':61]', ':(STOCK_DIM*2+1)]')]
EXPECT = {'EnvMultipleStock_train': (1, 1, 4), 'EnvMultipleStock_validation': (1, 1, 1),
          'EnvMultipleStock_trade': (1, 1, 1)}

mark('run_start')
try:
    os.makedirs('trained_models', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    import numpy as np
    mark('np_seed_state', head=int(np.random.get_state()[1][0]))
    from config import config
    config.TRAINING_DATA_FILE = DATA
    import env as _envpkg
    for name, cnts in EXPECT.items():
        path = os.path.join(os.getcwd(), 'env', name + '.py')
        src = open(path).read()
        got = tuple(src.count(a) for a, _ in PATCH)
        if got != cnts:
            raise RuntimeError('patch count mismatch %s %s' % (name, got))
        for a, b in PATCH:
            src = src.replace(a, b)
        spec = importlib.util.spec_from_file_location('env.' + name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules['env.' + name] = mod
        exec(compile(src, path, 'exec'), mod.__dict__)
        setattr(_envpkg, name, mod)
        assert mod.STOCK_DIM == 29
        mark('env_patched', mod=name, counts=got, sha=hashlib.sha256(src.encode()).hexdigest())
    from preprocessing.preprocessors import preprocess_data, add_turbulence
    from model import models
    assert models.StockEnvTrain.__module__ == 'env.EnvMultipleStock_train'
    assert sys.modules['env.EnvMultipleStock_trade'].STOCK_DIM == 29

    data = preprocess_data()
    data = add_turbulence(data)
    assert data.tic.nunique() == 29 and data.groupby('datadate').tic.count().eq(29).all()
    mark('preprocess_end', n_dates=int(data.datadate.nunique()))
    unique_trade_date = data[(data.datadate > 20200707) & (data.datadate <= END)].datadate.unique()
    mark('utd', n=len(unique_trade_date), first=int(unique_trade_date[0]), last=int(unique_trade_date[-1]))

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
(OUT / 'run_ensemble_postpub29.py').write_text(RUN_PY)


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
    starts = load(rd / 'starts.jsonl')
    if len(starts) >= MAX_ATTEMPTS:
        r = {'run': f'E{idx}', 'status': 'failed_max_attempts', 'attempts': len(starts)}
        (rd / 'done.json').write_text(json.dumps(r, indent=1)); return r
    att = len(starts) + 1
    with open(rd / 'starts.jsonl', 'a') as f:
        f.write(json.dumps({'attempt': att, 't': time.time()}) + '\n')
    w = PP / f'run_E{idx}'
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(str(REPO), str(w), ignore=shutil.ignore_patterns('.git', 'trained_models', 'results'))
    times, errp, cho = rd / f'times.attempt{att}.jsonl', rd / f'error.attempt{att}.log', rd / f'chosen.attempt{att}.jsonl'
    env = dict(os.environ, ENS_TIMES=str(times), ENS_ERR=str(errp), ENS_CHOSEN=str(cho), ENS_DATA=str(DATA),
               ENS_END=str(END))
    t0 = time.time(); killed = False
    with open(rd / f'stdout.attempt{att}.log', 'w') as fo, open(rd / f'stderr.attempt{att}.log', 'w') as fe:
        p = subprocess.Popen([PY37, str(OUT / 'run_ensemble_postpub29.py')], cwd=str(w), stdout=fo, stderr=fe,
                             env=env, start_new_session=True)
        while p.poll() is None:
            time.sleep(20)
            if time.time() - t0 > CAP or (PP / 'STOP').exists():
                os.killpg(p.pid, signal.SIGKILL); killed = True; p.wait(); break
    rc, sec = p.returncode, time.time() - t0
    evs = [e['ev'] for e in load(times)]
    av = [w / 'results' / f'account_value_trade_ensemble_{i}.csv' for i in ITERS]
    have = [f.exists() for f in av]
    ok = (rc == 0 and not killed and 'main_end' in evs and all(have))
    with open(rd / 'attempts.jsonl', 'a') as f:
        f.write(json.dumps({'attempt': att, 'rc': rc, 'killed': killed, 'seconds': sec, 'ok': ok,
                            'n_account_files': sum(have), 'events_tail': evs[-4:]}) + '\n')
    if ok:
        dst = rd / 'account_value'
        dst.mkdir(exist_ok=True)
        for f in av:
            shutil.copy(f, dst / f.name)
        r = {'run': f'E{idx}', 'status': 'ok', 'attempt': att, 'seconds': sec}
    elif killed:
        r = {'run': f'E{idx}', 'status': 'stopped' if (PP / 'STOP').exists() else 'killed_at_cap', 'attempt': att,
             'seconds': sec}
    else:
        r = {'run': f'E{idx}', 'status': 'error', 'attempt': att, 'rc': rc}
    shutil.rmtree(w, ignore_errors=True)
    if r['status'] != 'error':
        (rd / 'done.json').write_text(json.dumps(r, indent=1))
    return r


for idx in range(1, N_RUNS + 1):
    while True:
        if (PP / 'STOP').exists():
            print('STOP 파일: 새 실행을 시작하지 않습니다.'); sys.exit(0)
        r = run_one(idx)
        print(json.dumps({k: r[k] for k in ('run', 'status', 'attempt') if k in r}, ensure_ascii=False), flush=True)
        if r.get('status') != 'error':
            break
(OUT / 'all_done').write_text(str(time.time()))
print('postpub29 전체 실행 끝. 판정은 replication/ensemble_postpub29_judge.py')
