# -*- coding: utf-8 -*-
"""PGPortfolio 원조(Jiang et al., 2017; 48cc5a4)의 학습된 관성(α_eff)과 평가 시작 상태 효과.
사전 등록 notes/startstate_pgportfolio_prereg.md(e5b124c) → v2(3ff53f2) → v3(1ee572a, 정정 9b004c6). 실행 전 커밋.
아래 정의는 사전 등록 2·3장을 이 구현에 맞게 구체화한 것이며 결과를 본 뒤 바꾸지 않는다.

[환경·설정]
- 서버 WSL ~/f4work/pgss/repo = 원 저장소 복사본(코드 수정 없음), repo/database/Data.db → ~/f4work/Data.db 심볼릭 링크.
- python ~/f4work/adrl/p37(TF 1.15.4, tflearn 0.5.0, numpy 1.16.4), PYTHONPATH = pgss/pylib_pd(pandas 0.24.2 링크):pgss/pylib(Pillow 9.5.0).
- 설정 = 기본 pgportfolio/net_config.json(load_config), 바꾸는 것: start_date 2017/01/01, end_date 2018/01/01(v3), random_seed = 시드
  (generate.add_packages와 같은 키). 서버 TZ Asia/Seoul(parse_time = 로컬 mktime; G1 v3도 이 TZ로 확인).
- 네트워크 차단: Poloniex.__init__·api를 예외로 바꾼다(오프라인이라 원래 호출되지 않음; 호출되면 멈춤).
- 학습: train_package/<idx>/net_config.json(시드 s → idx = s+1, add_packages와 같은 번호·json 형식)을 쓰고,
  autotrain.training.train_one(train_all의 processes=1 호출과 같은 인자: save_path=./train_package/<idx>/netfile,
  config=load_config(idx), log_file_dir=./train_package/<idx>/tensorboard, logfile DEBUG, console INFO, device cpu).
  train_one은 코드 기본대로 끝에 rolling training 백테스트를 하고 train_summary.csv를 쓴다. 모델 = netfile
  (snap_shot false → 마지막 기록 스텝 저장, 코드 규칙). 학습 표준 출력·programlog·train_summary는 측정 전 열지 않는다.

[직전 가중치 입력(G3)] network.py 102–108행(EIIE_Output_WithW, previous_w concat → 1×1 conv). 백테스트 nnagent.py 212행
  (last_w[1:]), trader.py 91행, backtest.py 77행(직전 보유 = 비용·가격 반영 뒤 가중치), 초기 보유 trader.py 42–43행(BTC 100%).

[측정 정의]
- 펼치기 roll(agent, dm, idxs, w0): BackTest.trade_by_strategy와 같은 계산. 인덱스 t마다 M = dm.get_submatrix(t),
  X = M[:, :, :-1], y = M[0, :, -1] / M[0, :, -2](__pack_samples의 y[0]), omega = agent.decide_by_history(X, last.copy()),
  pv = calculate_pv_after_commission(omega, last, 0.0025), change = pv·(omega·[1, y]), last = pv·omega·[1, y]/change.
  온라인 학습 없음(결정적). 현금 = BTC(자산 0).
- 검증: 시험 구간 원래 시작 roll의 fAPV와, 코드 BackTest(trading.rolling_training_steps = 0, 같은 모델)의 test_pv가
  상대 1e-6 안에서 같아야 한다(assert).
- 지표: fAPV = Π change, SR = pgportfolio.tools.indicator.sharpe(change)(코드 정의, 기간당), 보조 MDD(indicator.max_drawdown).
- 시험 구간 = dm.test_indices(코드 BackTest와 같음). 원래 시작 = BTC 100%(one-hot 0).
  워밍업 시작 = 인덱스 test_indices[0]−60 … test_indices[0]−1을 원래 시작에서 roll한 뒤의 last(코드가 다음 스텝에 넘기는
  보유). 워밍업 결정의 수익 y는 시험 첫 결정 입력 창 안의 가격까지만 쓴다(시험 수익 미사용).
  효과 = 지표(원래) − 지표(워밍업). 보조: 등가중 시작(1/12) 지표.
- α_eff: 학습 구간 20개 시점 s = linspace(train_ind[0], train_ind[−1] − 60, 20) 정수, 각 s에서 60스텝 roll.
  시작 두 가지 = 현금(BTC one-hot) 대 등가중(모든 자산 1/m, m = 12). 노출 x = 1 − omega[0](스텝 k = 1..60의 결정).
  gap_k = 20개 평균 |x_e,k − x_c,k| / (11/12)(시작 노출 차이로 정규화, 시작 차이 1).
  α = Σ_{k=0}^{59}(1−α)^(k+1) = Σ gap 의 해(finrl_costgrad.py alpha_from_gap과 같은 식).
  보조: (a) L1 전체 가중치 거리/2를 시작 L1/2(11/12)로 정규화한 α, (b) 코드 PVM 초기값(BTC 0, 코인 1/11) 대 현금 시작의 노출 α.
- 보조(rolling training 켬, 코드 기본): 코드 BackTest(rolling_training_steps 85 그대로)를 새로 복원한 모델로 두 번 돌린다.
  한 번은 원래 시작, 한 번은 BackTest._last_omega를 워밍업 보유(위 결정적 워밍업)로 바꾼 뒤 시작. 지표 차이를 기술만 한다.
  코드가 기록한 train_summary.csv backtest_test_pv와 원래 시작 rolling fAPV도 함께 기록(재현성 확인용, 판정 아님).

[판정(사전 등록 3장)] 단위 = 모델(시드). 완료 모델 수 n.
- H-I: α_eff < 0.5인 모델 수 ≥ n/2(3개면 2개 이상) → "이 구현은 관성을 학습했다", 아니면 "학습하지 않았다".
- H-S: 모델별 |ΔfAPV|/fAPV(원래)의 중앙값 ≥ 0.05 또는 |ΔSR|(코드 SR)의 중앙값 ≥ 0.1 → "보고 지표에 실질적 영향",
  아니면 "실질적 영향 아님". 주 판정은 결정적(온라인 학습 끔) 평가. rolling 쪽은 같은 수치를 기술만.
- 기술적 판정이며 유의성 검정이 아니다.

[자원] 모델(시드)마다 학습 상한 6시간(timeout), 측정 상한 2시간, 전체 14시간(다음 모델은 남은 예산이 6시간 이상일 때만 시작;
  아니면 끝난 시드만 쓴다). 모델 사이 180초 간격. C: 감시(watch.sh)가 STOP을 만들고 train/measure 프로세스를 죽이면
  디스크 중단으로 기록하고 시도 수에 넣지 않으며, 모델당 시도 최대 2회. 재시도 전 C: 여유 ≥ 3 GB를 최대 30분 기다린다.

사용(서버 WSL, cwd 무관):
  PY=~/f4work/adrl/p37/bin/python; export PYTHONPATH=~/f4work/pgss/pylib_pd:~/f4work/pgss/pylib PYTHONDONTWRITEBYTECODE=1
  $PY startstate_pgportfolio.py orchestrate          (tmux pgss 안에서)
  $PY startstate_pgportfolio.py train <seed>  /  measure <idx>  /  judge
"""
import json
import os
import subprocess
import sys
import time

PG = os.path.expanduser('~/f4work/pgss')
REPO = os.path.join(PG, 'repo')
OUT = os.path.join(PG, 'out')
STOP = os.path.join(PG, 'STOP')
SEEDS = [0, 1, 2]
H, NPTS = 60, 20
START, END = '2017/01/01', '2018/01/01'
TRAIN_CAP, MEAS_CAP, TOTAL_CAP, GAP = 6 * 3600, 2 * 3600, 14 * 3600, 180


def jlog(**kw):
    os.makedirs(OUT, exist_ok=True)
    kw['t'] = time.strftime('%F %T')
    with open(os.path.join(OUT, 'orchestrate.jsonl'), 'a') as f:
        f.write(json.dumps(kw, ensure_ascii=False) + '\n')


def c_free_kb():
    return int(subprocess.check_output("df -k /mnt/c | tail -1 | awk '{print $4}'", shell=True).decode().strip())


def setup_code():
    os.environ['CUDA_VISIBLE_DEVICES'] = ''     # CPU(학습 cpu 경로와 같음)
    sys.path.insert(0, REPO)
    os.chdir(REPO)
    import pgportfolio.marketdata.poloniex as polo

    def no_net(*a, **k):
        raise RuntimeError('network access blocked (pgss offline run)')
    polo.Poloniex.__init__ = no_net
    polo.Poloniex.api = no_net


def alpha_from_gap(gn):
    import numpy as np
    S, K = float(np.clip(gn, 0, None).sum()), len(gn)
    f = lambda a: ((1 - a) ** (np.arange(K) + 1)).sum() - S  # noqa: E731
    if S <= 1e-12:
        return 1.0
    if f(1e-4) < 0:
        return 1e-4
    lo, hi = 1e-4, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


# ------------------------------------------------------------------ train
def train(seed):
    setup_code()
    import logging
    from pgportfolio.tools.configprocess import load_config
    from pgportfolio.autotrain.training import train_one
    idx = str(seed + 1)
    cfg = load_config()
    cfg['input']['start_date'], cfg['input']['end_date'] = START, END
    cfg['random_seed'] = seed
    d = os.path.join('train_package', idx)
    os.makedirs(d)
    with open(os.path.join(d, 'net_config.json'), 'w') as f:
        json.dump(cfg, f, indent=4, sort_keys=True)
    train_one('./train_package/' + idx + '/netfile', load_config(idx), './train_package/' + idx + '/tensorboard',
              idx, logging.DEBUG, logging.INFO, 'cpu')
    with open(os.path.join(d, 'TRAIN_DONE'), 'w') as f:
        f.write(time.strftime('%F %T'))


# ------------------------------------------------------------------ measure
def measure(idx):
    setup_code()
    import numpy as np
    import pandas as pd
    import tensorflow as tf
    from pgportfolio.tools.configprocess import load_config
    from pgportfolio.marketdata.datamatrices import DataMatrices
    from pgportfolio.learn.nnagent import NNAgent
    from pgportfolio.tools.trade import calculate_pv_after_commission
    from pgportfolio.tools.indicator import sharpe, max_drawdown
    from pgportfolio.trade.backtest import BackTest
    idx = str(idx)
    cfg = load_config(idx)
    net = './train_package/' + idx + '/netfile'
    c = cfg['trading']['trading_consumption']
    m1 = cfg['input']['coin_number'] + 1
    t0 = time.time()
    dm = DataMatrices.create_from_config(json.loads(json.dumps(cfg)))
    tf.reset_default_graph()
    agent = NNAgent(cfg, restore_dir=net)

    def roll(idxs, w0):
        last = np.array(w0, dtype=np.float64)
        om, ch = [], []
        for t in idxs:
            M = dm.get_submatrix(t)
            X = M[:, :, :-1]
            fp = np.concatenate((np.ones(1), M[0, :, -1] / M[0, :, -2]))
            omega = agent.decide_by_history(X, last.copy())
            pv = calculate_pv_after_commission(omega, last, c)
            change = pv * np.dot(omega, fp)
            last = pv * omega * fp / change
            om.append(omega)
            ch.append(change)
        return np.array(om), np.array(ch), last

    def metr(ch):
        ch = np.asarray(ch, dtype=np.float64)
        return {'fAPV': float(np.prod(ch)), 'SR': float(sharpe(ch)), 'MDD': float(max_drawdown(ch)), 'n': int(len(ch))}

    cash = np.zeros(m1); cash[0] = 1.0
    ew = np.full(m1, 1.0 / m1)
    pvm0 = np.full(m1, 1.0 / (m1 - 1)); pvm0[0] = 0.0
    test = list(dm.test_indices)
    t_first = test[0]
    # 시작 상태(결정적)
    _, ch_o, _ = roll(test, cash)
    wom, _, w_warm = roll(range(t_first - H, t_first), cash)
    _, ch_w, _ = roll(test, w_warm)
    _, ch_e, _ = roll(test, ew)
    orig, warm, eqw = metr(ch_o), metr(ch_w), metr(ch_e)
    # α_eff (학습 구간)
    tr = dm._train_ind
    pts = [int(v) for v in np.linspace(tr[0], tr[-1] - H, NPTS)]
    gx, gl, gp = [], [], []
    for s in pts:
        oc, _, _ = roll(range(s, s + H), cash)
        oe, _, _ = roll(range(s, s + H), ew)
        op, _, _ = roll(range(s, s + H), pvm0)
        xc, xe, xp = 1 - oc[:, 0], 1 - oe[:, 0], 1 - op[:, 0]
        gx.append(np.abs(xe - xc) / (1 - 1.0 / m1))
        gl.append(0.5 * np.abs(oe - oc).sum(axis=1) / (0.5 * np.abs(ew - cash).sum()))
        gp.append(np.abs(xp - xc))
    gx, gl, gp = np.mean(gx, axis=0), np.mean(gl, axis=0), np.mean(gp, axis=0)
    det_s = time.time() - t0
    agent.recycle()

    # 검증: 코드 BackTest, rolling 끔
    def code_bt(rolling_steps, w0=None):
        cf = json.loads(json.dumps(cfg))
        if rolling_steps is not None:
            cf['trading']['rolling_training_steps'] = rolling_steps
        tf.reset_default_graph()
        ag = NNAgent(cf, restore_dir=net)
        bt = BackTest(cf, net_dir=None, agent=ag)
        if w0 is not None:
            bt._last_omega = np.array(w0, dtype=np.float64)
        bt.start_trading()                       # 끝에서 agent.recycle()
        return metr(bt.test_pc_vector), float(bt.test_pv)

    bt0, bt0_pv = code_bt(0)
    rel = abs(bt0_pv - orig['fAPV']) / orig['fAPV']
    assert rel < 1e-6, ('roll != BackTest', bt0_pv, orig['fAPV'])
    # 보조: rolling training 켬(코드 기본 85)
    t1 = time.time()
    roll_o, _ = code_bt(None)
    roll_w, _ = code_bt(None, w_warm)
    roll_s = time.time() - t1
    summ = None
    try:
        df = pd.read_csv('./train_package/train_summary.csv').set_index('net_dir')
        summ = float(df.loc[int(idx), 'backtest_test_pv'])
    except Exception as e:  # noqa: BLE001
        summ = 'unavailable: %s' % e
    res = {
        'idx': idx, 'seed': cfg['random_seed'], 'coins': list(dm.coin_list),
        'n_train': int(len(tr)), 'n_test': len(test), 'test_first_index': int(t_first),
        'det': {'orig': orig, 'warm': warm, 'eqw_aux': eqw,
                'd_fAPV_rel': (orig['fAPV'] - warm['fAPV']) / orig['fAPV'], 'd_SR': orig['SR'] - warm['SR'],
                'warm_holding': [float(v) for v in w_warm], 'warm_exposure': float(1 - w_warm[0]),
                'warm_mean_exposure': float(np.mean(1 - wom[:, 0]))},
        'check_code_backtest_norolling': {'test_pv': bt0_pv, 'rel_diff': rel, 'SR': bt0['SR']},
        'alpha_eff': alpha_from_gap(gx), 'alpha_eff_L1_aux': alpha_from_gap(gl), 'alpha_eff_pvm0_aux': alpha_from_gap(gp),
        'gap_exposure': [float(v) for v in gx], 'gap_L1': [float(v) for v in gl], 'alpha_points': pts,
        'rolling_aux': {'orig': roll_o, 'warm': roll_w,
                        'd_fAPV_rel': (roll_o['fAPV'] - roll_w['fAPV']) / roll_o['fAPV'],
                        'd_SR': roll_o['SR'] - roll_w['SR'], 'train_summary_backtest_test_pv': summ},
        'seconds': {'det': det_s, 'rolling': roll_s},
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'measure_%s.json' % idx), 'w') as f:
        json.dump(res, f, indent=1)


# ------------------------------------------------------------------ judge
def judge():
    import numpy as np
    ms = []
    for s in SEEDS:
        p = os.path.join(OUT, 'measure_%d.json' % (s + 1))
        if os.path.exists(p):
            ms.append(json.load(open(p)))
    n = len(ms)
    out = {'n_models': n, 'seeds': [m['seed'] for m in ms]}
    if n:
        al = [m['alpha_eff'] for m in ms]
        k = sum(a < 0.5 for a in al)
        dfa = [abs(m['det']['d_fAPV_rel']) for m in ms]
        dsr = [abs(m['det']['d_SR']) for m in ms]
        hs = float(np.median(dfa)) >= 0.05 or float(np.median(dsr)) >= 0.1
        rf = [abs(m['rolling_aux']['d_fAPV_rel']) for m in ms]
        rs = [abs(m['rolling_aux']['d_SR']) for m in ms]
        out.update({
            'alpha_eff': al, 'n_alpha_lt_0.5': int(k),
            'H_I': '이 구현은 관성을 학습했다' if k >= n / 2 else '학습하지 않았다',
            'abs_d_fAPV_rel': dfa, 'abs_d_SR': dsr,
            'median_abs_d_fAPV_rel': float(np.median(dfa)), 'median_abs_d_SR': float(np.median(dsr)),
            'H_S': '보고 지표에 실질적 영향' if hs else '실질적 영향 아님',
            'rolling_aux': {'abs_d_fAPV_rel': rf, 'abs_d_SR': rs,
                            'median_abs_d_fAPV_rel': float(np.median(rf)), 'median_abs_d_SR': float(np.median(rs))},
        })
    with open(os.path.join(OUT, 'judge.json'), 'w') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(out, ensure_ascii=False))


# ------------------------------------------------------------------ orchestrate
def run_child(args, cap, log):
    env = dict(os.environ)
    with open(log, 'a') as lf:
        p = subprocess.Popen([sys.executable, os.path.abspath(__file__)] + args, stdout=lf, stderr=subprocess.STDOUT,
                             env=env)
        try:
            rc = p.wait(timeout=cap)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait()
            rc = 'timeout'
    return rc


def orchestrate():
    import shutil
    t_start = time.time()
    os.makedirs(OUT, exist_ok=True)
    jlog(ev='start', c_free_kb=c_free_kb())
    for i, s in enumerate(SEEDS):
        idx = s + 1
        left = TOTAL_CAP - (time.time() - t_start)
        if left < TRAIN_CAP:
            jlog(ev='skip_budget', seed=s, left_s=left)
            break
        if i > 0:
            time.sleep(GAP)
        attempts, ok = 0, False
        while attempts < 2 and not ok:
            for _ in range(30):
                if c_free_kb() >= 3 * 1024 * 1024:
                    break
                time.sleep(60)
            if os.path.exists(STOP):
                os.remove(STOP)
            d = os.path.join(REPO, 'train_package', str(idx))
            if os.path.exists(d):
                shutil.rmtree(d)
            attempts += 1
            jlog(ev='train_start', seed=s, attempt=attempts, c_free_kb=c_free_kb())
            t0 = time.time()
            rc = run_child(['train', str(s)], min(TRAIN_CAP, TOTAL_CAP - (time.time() - t_start)),
                           os.path.join(OUT, 'train_%d.log' % idx))
            done = os.path.exists(os.path.join(d, 'TRAIN_DONE'))
            disk = os.path.exists(STOP)
            jlog(ev='train_end', seed=s, attempt=attempts, rc=rc, done=done, disk_stop=disk, sec=time.time() - t0,
                 c_free_kb=c_free_kb())
            if done:
                t1 = time.time()
                rc = run_child(['measure', str(idx)], MEAS_CAP, os.path.join(OUT, 'measure_%d.log' % idx))
                okm = os.path.exists(os.path.join(OUT, 'measure_%d.json' % idx))
                disk = os.path.exists(STOP)
                jlog(ev='measure_end', seed=s, rc=rc, ok=okm, disk_stop=disk, sec=time.time() - t1, c_free_kb=c_free_kb())
                ok = okm
            if not ok and not disk:
                break                                    # 디스크 외 실패: 재시도 안 함
    run_child(['judge'], 600, os.path.join(OUT, 'judge.log'))
    jlog(ev='all_done', total_s=time.time() - t_start)
    with open(os.path.join(OUT, 'ALL_DONE'), 'w') as f:
        f.write(time.strftime('%F %T'))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'train':
        train(int(sys.argv[2]))
    elif cmd == 'measure':
        measure(sys.argv[2])
    elif cmd == 'judge':
        judge()
    elif cmd == 'orchestrate':
        orchestrate()
