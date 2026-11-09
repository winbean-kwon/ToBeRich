# -*- coding: utf-8 -*-
# RAT F7 실행(서버 노트북 GTX 1650, WSL2). 사전 등록 notes/funnel_f7_rat_prereg.md.
# F4 로컬 스크립트(replication/funnel_f4_rat_local.py)의 설치·데이터·래퍼를 재사용하고 다음만 바꾼다.
#   - 입력 자르기 없음(원래 시험 구간). 단, --check 모드는 F4와 같은 가짜 시험 구간으로 경로만 점검한다.
#   - 조건 P(80000, 1e-7, x_window 30)·R(run_main.sh: 50000, 5e-8, 31), model_index 1~5, 순서 P1..P5 → R1..R5.
#   - 기록(허용 수정 4): 난수 상태 요약, 체크포인트 저장 스텝, 학습 마지막 모델(보조 F) 저장과 test_online 평가,
#     UCRP 계산용 시험 구간 종가 비율(시장 데이터, 성과 아님).
# 성과(train_summary.csv, final_summary.csv, 표준 출력)는 화면에 내지 않는다. 판정은 replication/funnel_f7_rat_judge.py.
# 사용: python3 funnel_f7_rat_local.py --check   (확정 전 점검, 2.3)
#       python3 funnel_f7_rat_local.py           (본 실행, tmux 안에서)
import hashlib, json, os, pathlib, shutil, signal, subprocess, sys, time

HOME = pathlib.Path.home()
WORK = HOME / 'f4work'                      # F4에서 만든 환경(p37, RAT @d1cbe96, Data.db)
OUT = HOME / 'ToBeRich' / 'data' / 'funnel' / 'rat_f7_gtx1650'
CHECK = '--check' in sys.argv
STOP_AT = 1795532400                        # 2026-11-25 00:00 KST: 이후 새 실행을 시작하지 않는다(2.2)
MAX_ATTEMPTS = 3
CAP = {'P': 12 * 3600, 'R': 8 * 3600}      # 실행당 벽시계 상한(F5 측정의 약 2.7배). 넘으면 미완으로 기록, 재실행 없음
OUT.mkdir(parents=True, exist_ok=True)

COMMON = ['--batch_size', '128', '--coin_num', '11', '--feature_number', '4', '--output_step', '1000',
          '--test_portion', '0.08', '--trading_consumption', '0.0025', '--variance_penalty', '0.0', '--cost_penalty', '0.0',
          '--learning_rate', '0.0001', '--start', '2016/01/01', '--end', '2018/01/01', '--model_name', 'RAT',
          '--model_dim', '12', '--multihead_num', '2', '--local_context_length', '5', '--daily_interest_rate', '0.001']
COND = {'P': ['--total_step', '80000', '--weight_decay', '1e-7', '--x_window_size', '30'],
        'R': ['--total_step', '50000', '--weight_decay', '5e-8', '--x_window_size', '31']}


def die(msg):
    print(msg); sys.exit(1)


# ---- 환경 확인(F4 설치 재사용, 새로 설치하지 않음) ----
PY = WORK / 'p37' / 'bin' / 'python'
if not (WORK / 'out' / 'env_ok').exists() or not PY.exists():
    die('F4 환경이 없습니다. 먼저 replication/funnel_f4_rat_local.py의 설치 단계를 돌리세요.')
sha = hashlib.sha256(open(WORK / 'RAT' / 'main.py', 'rb').read()).hexdigest()
if sha != 'f7ff0b45bdfe8b411e7453ee1c65f15a1976205ed82c750436efeafdf84ecc94':
    die('main.py 해시가 기록과 다릅니다.')
db = WORK / 'RAT' / 'database' / 'Data.db'
if hashlib.sha256(open(db, 'rb').read()).hexdigest() != 'e8a0da9e0344bdbff2daaf9403d6fead76b5c591857f71a65c108fd2baca7edf':
    die('Data.db 해시가 기록과 다릅니다.')
GPU_NAME = subprocess.getoutput('nvidia-smi -L')
if 'GTX 1650' not in GPU_NAME:
    die('GTX 1650을 찾지 못했습니다(장치 고정, 2.2).')
gate = subprocess.run([str(PY), '-c', 'import torch; x=torch.randn(64,64).cuda(); print(float((x@x.t()).sum()) == float((x@x.t()).sum()))'],
                      capture_output=True, text=True)
if gate.returncode != 0 or 'True' not in gate.stdout:
    die('GPU 연산 시험 실패: ' + gate.stderr[-300:])

# ---- 래퍼 ----
WRAP = r'''# -*- coding: utf-8 -*-
import os, sys, time, json, traceback
import numpy as np
TIM = os.environ['RAT_TIMES']; ERR = os.environ['RAT_ERR']; CUT = os.environ.get('RAT_CUT') == '1'; RUN_DIR = os.environ['RAT_RUN_DIR']
def mark(ev, **kw):
    d = {'ev': ev, 't': time.time(), 'pid': os.getpid()}; d.update(kw)
    with open(TIM, 'a') as f: f.write(json.dumps(d) + '\n')
def err():
    with open(ERR, 'a') as f: traceback.print_exc(file=f)
src = open('main.py').read()
CUTLINE = '\nstart = parse_time(FLAGS.start)\n'
assert src.count(CUTLINE) == 1, 'split marker'
head, rest = src.split(CUTLINE)
tail = '\n' * (head.count('\n') + 1) + CUTLINE.lstrip('\n') + rest
g = sys.modules['__main__'].__dict__
g['__file__'] = os.path.abspath('main.py')
mark('main_start', tz=list(time.tzname), argv=sys.argv[1:])
try:
    exec(compile(head, 'main.py', 'exec'), g)
    import torch
    assert not getattr(torch.cuda, '_initialized', False), 'cuda initialized before device override'
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    FLAGS = g['FLAGS']
    mark('seed', torch_initial_seed=int(torch.initial_seed()), np_state_head=[int(v) for v in np.random.get_state()[1][:4]])

    HM = g['HistoryManager']; _gp = HM.get_global_panel
    def panel(self, start, end, period=300, features=('close',)):
        p = _gp(self, start, end, period, features); N = len(p.minor_axis)
        info = dict(n_full=N, first=str(p.minor_axis[0]), last=str(p.minor_axis[-1]), coins=[str(c) for c in p.major_axis], cut=CUT)
        if CUT:  # --check 전용: F4와 같은 가짜 시험 구간(원래 시험 구간을 계산에 쓰지 않음)
            trp = 1 - FLAGS.test_portion; s = float(trp + FLAGS.test_portion)
            split = int(((np.array([trp]) / s) * N).astype(int)[0])
            p = p.reindex(minor_axis=p.minor_axis[:split]); info['n_kept'] = split
        mark('panel', **info); return p
    HM.get_global_panel = panel

    DMc = g['DataMatrices']; _init = DMc.__init__
    def dm_init(self, *a, **k):
        _init(self, *a, **k)
        mark('dm', n_periods=int(self._num_periods), n_train=int(self._num_train_samples), n_test=int(len(self._test_ind)),
             test_first=int(self._test_ind[0]), test_last=int(self._test_ind[-1]))
    DMc.__init__ = dm_init

    _gto = DMc.get_test_set_online
    def gto(self, *a, **k):
        b = _gto(self, *a, **k)
        pth = os.path.join(RUN_DIR, 'test_close_relatives.npy')
        if not os.path.exists(pth): np.save(pth, np.asarray(b['y'])[0, 0])  # [coins, T] 종가 비율(시장 데이터), UCRP용
        return b
    DMc.get_test_set_online = gto

    cnt = [0]; phase = ['train']
    _tos = g['train_one_step']
    def tos(*a, **k):
        if cnt[0] % 1000 == 0: mark('step', step=cnt[0])
        cnt[0] += 1
        return _tos(*a, **k)
    g['train_one_step'] = tos

    _save = torch.save
    def save(obj, f, *a, **k):
        if phase[0] == 'train': mark('ckpt', step=cnt[0] - 1)
        return _save(obj, f, *a, **k)
    torch.save = save

    _tn = g['train_net']
    def tn(*a, **k):
        mark('train_start'); r = _tn(*a, **k); phase[0] = 'after'
        mark('loop_end', steps=cnt[0])
        _save(a[5], os.path.join(FLAGS.model_dir, 'final_%d.pkl' % FLAGS.model_index)); mark('final_model_saved')
        return r
    g['train_net'] = tn

    _te = g['test_net']
    def te(*a, **k):
        mark('eval_start'); r = _te(*a, **k); mark('eval_end'); return r
    g['test_net'] = te

    exec(compile(tail, 'main.py', 'exec'), g)
    mark('main_eval_done')

    # 보조 F: 학습 마지막 모델을 같은 test_online 경로로 평가(main의 평가가 끝난 뒤, PVM 변경 없음)
    import pandas as pd
    mf = torch.load(os.path.join(FLAGS.model_dir, 'final_%d.pkl' % FLAGS.model_index))
    v, SR, CR, St_v, pc, TO = g['test_net'](g['DM'], 1, 1, g['x_window_size'], g['local_context_length'], mf,
                                            g['loss_compute'], g['test_loss_compute'], False, True)
    pd.DataFrame({'net_dir': [FLAGS.model_index], 'fAPV': [v.item()], 'SR': [SR.item()], 'CR': [CR.item()], 'TO': [TO.item()],
                  'St_v': [''.join(str(e) + ', ' for e in St_v)],
                  'backtest_test_history': [''.join(str(e) + ', ' for e in pc.cpu().numpy())]}).set_index('net_dir').to_csv(
        os.path.join(FLAGS.log_dir, 'final_summary.csv'))
    mark('final_eval_done')
except Exception:
    err(); mark('main_error'); raise
mark('main_end')
'''
(WORK / 'out' / 'run_rat_f7.py').write_text(WRAP)


def load_ev(path):
    out = []
    if os.path.exists(path):
        for l in open(path, errors='ignore'):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def run_one(cond, idx, cut=False, steps=None, cap=None):
    name = f'{cond}{idx}' if not cut else 'check'
    rd = OUT / name
    done = rd / 'done.json'
    if done.exists():
        print(f'{name}: 끝난 기록이 있어 건너뜁니다'); return json.loads(done.read_text())
    rd.mkdir(parents=True, exist_ok=True)
    att_f = rd / 'attempts.jsonl'
    attempts = load_ev(att_f)
    if len(attempts) >= MAX_ATTEMPTS:
        r = {'run': name, 'status': 'failed_max_attempts', 'attempts': len(attempts)}
        done.write_text(json.dumps(r, indent=1)); print(json.dumps(r)); return r
    attempt = len(attempts) + 1
    w = WORK / f'f7_{name}'
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(str(WORK / 'RAT'), str(w), ignore=shutil.ignore_patterns('.git', 'database', 'model', 'log'))
    os.symlink(str(WORK / 'RAT' / 'database'), str(w / 'database'))
    (w / 'log').mkdir(); (w / 'model').mkdir()
    times, errp = rd / f'times.attempt{attempt}.jsonl', rd / f'error.attempt{attempt}.log'
    args = COND[cond][:]
    if steps:
        args[1] = str(steps)
    cmd = [str(PY), str(WORK / 'out' / 'run_rat_f7.py')] + COMMON + args + ['--model_index', str(idx),
                                                                           '--model_dir', str(w / 'model'), '--log_dir', str(w / 'log')]
    env = dict(os.environ, RAT_TIMES=str(times), RAT_ERR=str(errp), RAT_CUT='1' if cut else '0', RAT_RUN_DIR=str(rd),
               TZ='Asia/Shanghai', LANG='en_US.UTF-8', MPLBACKEND='agg')
    t0 = time.time(); killed = False
    with open(times, 'a') as f:
        f.write(json.dumps({'ev': 'run_start', 't': t0, 'attempt': attempt, 'cond': cond, 'idx': idx, 'gpu': GPU_NAME, 'cmd': cmd[2:]}) + '\n')
    with open(rd / f'stdout.attempt{attempt}.log', 'w') as fo, open(rd / f'stderr.attempt{attempt}.log', 'w') as fe:
        p = subprocess.Popen(cmd, cwd=str(w), stdout=fo, stderr=fe, env=env, start_new_session=True)
        while p.poll() is None:
            time.sleep(15)
            if time.time() - t0 > (cap or CAP[cond]):
                os.killpg(p.pid, signal.SIGKILL); killed = True; p.wait(); break
    rc, sec = p.returncode, time.time() - t0
    evs = [e['ev'] for e in load_ev(times)]
    ok = rc == 0 and 'final_eval_done' in evs and (w / 'log' / 'train_summary.csv').exists() and (w / 'log' / 'final_summary.csv').exists()
    with open(att_f, 'a') as f:
        f.write(json.dumps({'attempt': attempt, 'rc': rc, 'killed_at_cap': killed, 'seconds': sec, 'ok': ok, 'events_tail': evs[-6:]}) + '\n')
    if ok:
        for fn in ('train_summary.csv', 'final_summary.csv'):
            shutil.copy(str(w / 'log' / fn), str(rd / fn))
        r = {'run': name, 'status': 'ok', 'attempt': attempt, 'seconds': sec, 'gpu': GPU_NAME}
        done.write_text(json.dumps(r, indent=1))
        shutil.rmtree(w / 'model', ignore_errors=True)
    elif killed:
        r = {'run': name, 'status': 'killed_at_cap', 'attempt': attempt, 'seconds': sec}
        done.write_text(json.dumps(r, indent=1))
    else:
        r = {'run': name, 'status': 'error', 'attempt': attempt, 'rc': rc}
        if errp.exists():
            print('--- traceback(마지막 20줄) ---'); print(''.join(open(errp).readlines()[-20:]))
    print(json.dumps({k: v for k, v in r.items()}, ensure_ascii=False))
    return r


if CHECK:
    # 확정 전 점검(2.3): 가짜 시험 구간, P 설정, 2001스텝. 이벤트만 확인하고 성과 파일은 열지 않는다.
    r = run_one('P', 1, cut=True, steps=2001, cap=3 * 3600)
    evs = [e['ev'] for e in load_ev(sorted((OUT / 'check').glob('times.attempt*.jsonl'))[-1])]
    need = ['seed', 'panel', 'dm', 'ckpt', 'loop_end', 'final_model_saved', 'main_eval_done', 'final_eval_done', 'main_end']
    res = {'check_status': r.get('status'), 'missing_events': [e for e in need if e not in evs],
           'ucrp_input_saved': (OUT / 'check' / 'test_close_relatives.npy').exists(),
           'ckpt_events': evs.count('ckpt')}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (OUT / 'check_result.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    sys.exit(0 if (r.get('status') == 'ok' and not res['missing_events'] and res['ucrp_input_saved']) else 1)

for cond in ('P', 'R'):
    for idx in range(1, 6):
        while True:
            if not (OUT / f'{cond}{idx}' / 'done.json').exists() and time.time() >= STOP_AT:
                print('11-24 마감: 새 실행을 시작하지 않습니다.'); sys.exit(0)
            r = run_one(cond, idx)
            if r.get('status') != 'error':
                break
print('전체 실행 끝. 판정은 replication/funnel_f7_rat_judge.py')
