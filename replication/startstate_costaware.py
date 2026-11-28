# -*- coding: utf-8 -*-
"""RAT·WaveCorr 학습된 관성(α_eff)과 평가 시작 상태 효과. 사전 등록 notes/startstate_costaware_prereg.md (e9211dc, 수정 036e3fd).
실행 전 커밋. 아래 정의는 사전 등록 2·3장을 구현별로 구체화한 것이며 결과를 본 뒤 바꾸지 않는다.

[모델 존재 확인, 2026-11-28 실행 전]
- RAT: F7 실행기(funnel_f7_rat_local.py)가 성공한 실행의 model/ 폴더를 지웠다. 서버에 RAT 모델 파일 없음
  (~/ToBeRich/data/funnel/rat_f7_gtx1650/*, ~/f4work/f7_P*/ 에 *.pkl 없음) → 사전 등록 1장대로 다시 학습한다.
  설정 = F7 주 조건 P(논문 값: total_step 80000, weight_decay 1e-7, x_window_size 30, 나머지 run_main.sh), 같은 F7 래퍼
  (~/f4work/out/run_rat_f7.py, sha256 8facdc68… = funnel_f7_rat_local.py의 WRAP 문자열과 같음 확인), GTX 1650, TZ Asia/Shanghai.
  "시드" = model_index 1, 2, 3(코드는 시드를 정하지 않는다, F7과 같음). 대상 상한 GPU 12시간(시도 합계).
  다음 실행은 남은 예산이 F7 P1 실측 16,395초 이상일 때만 시작한다(못 끝낼 실행을 시작하지 않음). 남은 예산을 그 실행의 상한으로 쓴다.
  각 실행에서 모델 2개: P = 코드가 고른 체크포인트(<idx>.pkl, 시험 구간 최대 포트폴리오 가치 시점), F = 학습 마지막 스텝(final_<idx>.pkl).
- WaveCorr: F7x 시드 1112~1116의 마지막 에폭 체크포인트(~/f4work/wavecorr/repo/src/results/can_waveCorr_50stocks_seed<s>_permutation1/
  model.ckpt, pvm.csv; F7x done.json 모두 ok, 3000행)가 남아 있다 → 그대로 쓴다(5개 모델). 코드의 저장 규칙이 epoch == epochs−1에서 저장.

[직전 가중치 입력, 정적 확인]
- RAT main.py 601·630–631행: forward(…, previous_w, …)에서 previous_w([B,1,11], 현금 제외)를 decode_out에 concat해 linear_out·
  linear_out2로 결정. test_online(1222–1223행)은 직전 출력 out[:,:,1:]을 다음 previous_w로 넘긴다. 시험 시작의 previous_w =
  PVM[test_ind[0]−1] = 1/11(PVM 초기값 367–369행; train_ind가 window+1만큼 잘려 이 행은 학습에서 덮이지 않는다 → 측정에서 assert).
- WaveCorr wavecorr_network.py 228–241행(RNN=True, wavecorr_run.py 기본값): 청크 첫 결정은 wIn의 위치 −32(=drift(pvm[t−1]))를,
  이후는 직전 출력을 concat해 action_var 층으로 결정. 현금 자산 없음(50종목 softmax, 합 1).
  → 두 구현 모두 관성 경로가 있다. 측정한다.

[RAT 측정 정의]
- 펼치기(rat_roll): test_online(main.py 1196–1225행)과 같은 계산을 임의 시작 인덱스 s·스텝 수·시작 previous_w로 한다.
  get_test_set_online(s, s+xw+steps, xw). 스텝 j의 결정 시점은 봉 s+j+xw−1. 시험 구간 원래 평가(s=test_ind[0], steps=len(test_ind)−xw−1,
  previous_w=PVM 행)와 코드 test_online 결과의 fAPV가 1e-6 안에서 같아야 한다(assert). 저장된 train_summary(P)·final_summary(F)의
  fAPV와의 차이도 기록한다.
- 지표: 코드 Test_Loss(거래비용 0.0025, 이자 0.001/48)로 fAPV, SR(코드 비율), SR% = SR×100(논문 표기, F7 판정과 같은 단위), CR, TO.
- α_eff: 학습 구간 20개 시점 s = linspace(train_ind[0]+1, train_ind[-1]−xw−60, 20) 정수. 시작 두 가지: 현금(previous_w = 0) 대 등가중
  (previous_w = 1/11, 코드 a0). 60스텝. 노출 x = 1 − w_cash(출력 0번). gap_k = 20개 평균 |x_e,k − x_c,k|(k = 1..60번째 출력).
  α = Σ_{k=0}^{59}(1−α)^(k+1) = Σ gap 의 해(finrl_costgrad.py alpha_from_gap과 같음; 시작 차이 1). 보조: L1 전체 가중치 거리/2.
- 시작 상태 효과: 원래 시작 = PVM 행(1/11). 워밍업 시작 = s = test_ind[0]−60에서 원래 시작으로 60스텝 펼친 뒤 마지막 출력의
  out[:,:,1:](코드가 넘기는 형태). 워밍업 결정 시점은 시험의 첫 결정 직전 60개 봉이다(입력만 쓰고 시험 수익은 쓰지 않음).
  효과 = 지표(원래) − 지표(워밍업). 보조: 현금 시작(0) 지표.

[WaveCorr 측정 정의]
- 복원: runSingleExperiment와 같은 인자로 agent_manager 생성, saver.restore(model.ckpt), pvm = pvm.csv(코드의 restoreSavedModel 경로와 같음).
- 펼치기: 코드 train_test의 평가 패스(do_backprop=False, time_spots 순서) 그대로 agent.trainOnMinibatch_PG를 쓴다. 청크 시작 i에서
  결정 위치 t = i+31..i+62, 시작 보유 = drift(pvm[i+30]). 비용 mu는 코드대로 wPrime(일부는 pvm.csv의 이전 값)으로 계산된다.
- 원래 시작(보고 지표) = 복원 뒤 전체 패스(데이터 처음 1/N에서 이어진 보유가 시험 구간으로 넘어감). 저장 APV_.csv SR과의 차이 기록.
- 워밍업 시작 = 결정 위치가 trainSetLen−60 이하에서 시작하는 마지막 청크 k0부터만 패스(그 청크 시작 pvm[i0+30] = 1/N, 코드 초기값).
  청크 격자(30) 때문에 워밍업 길이 = trainSetLen − (i0+31) (≥ 60, 최소값; 기록).
- 지표: 시험 구간 APV = cumprod(pvm_reward[trainSetLen:]), SR = 연수익/연변동성(코드 compute_performance_measures = F7x 판정 식).
  보조: 일관 비용 SR(같은 행동에서 mu를 drift(w_{t−1}) 대 w_t로 다시 계산), 차가운 시작(시험 첫 결정 직전 청크 시작을 1/N).
- α_eff: 현금 자산 없음 → 시작 두 가지 = "한 자산 집중"(종목 0번 one-hot) 대 등가중(1/N). 학습 구간 청크 시작 20개
  (k = linspace(1, kmax, 20), kmax = 결정 위치 i+31+60 ≤ trainSetLen인 최대 청크), 청크 k, k+1 두 개 패스 → 결정 60개.
  gap_k = 20개 평균 L1(w_e,k − w_c,k) / L1(drift(시작_e) − drift(시작_c)). α는 RAT와 같은 식.

[판정 (사전 등록 3장)] 단위 = 모델. RAT 모델 = 실행별 P·F(완료 실행 수 × 2), WaveCorr 모델 = 시드 5개.
- H-I: α_eff < 0.5인 모델 수 ≥ 모델 수/2 → "이 구현은 관성을 학습했다", 아니면 "학습하지 않았다".
- H-S: RAT — 모델별 |ΔfAPV|/fAPV(원래)의 중앙값 ≥ 0.05 또는 |ΔSR%|의 중앙값 ≥ 0.1 → "보고 지표에 실질적 영향".
  WaveCorr — |ΔSR|(코드 SR)의 중앙값 ≥ 0.1 → "실질적 영향". 아니면 "실질적 영향 아님". 보조로 RAT P·F 따로의 중앙값.
- 기술적 판정이며 유의성 검정이 아니다.

사용(서버 WSL):
  python3 startstate_costaware.py rat-train                      (오케스트레이터, tmux 안에서)
  <p37 python> startstate_costaware.py rat-measure <run_dir> <idx>   (cwd = 실행 작업 폴더; rat-train이 부른다)
  <wavecorr p37 python> startstate_costaware.py wc-measure <seed>  (cwd = ~/f4work/wavecorr/repo/src)
  python3 startstate_costaware.py judge <out_dir>
성과 비노출: 학습 표준 출력·train_summary는 열지 않는다. 측정 JSON은 측정이 끝난 뒤 판정에서 읽는다.
"""
import hashlib
import json
import os
import pathlib
import signal
import subprocess
import sys
import time

HOME = pathlib.Path.home()
WORK = HOME / 'f4work'
SS = WORK / 'ssca'
OUTD = SS / 'out'
STOP = pathlib.Path(os.environ.get('SSCA_STOP', str(SS / 'STOP')))
H, NPTS = 60, 20

RAT_PY = WORK / 'p37' / 'bin' / 'python'
RAT_WRAP = WORK / 'out' / 'run_rat_f7.py'
RAT_WRAP_SHA = '8facdc688a11143591b99b4d9be8c3b28e92b4dfd0cf373b091a498956c94c13'
RAT_MAIN_SHA = 'f7ff0b45bdfe8b411e7453ee1c65f15a1976205ed82c750436efeafdf84ecc94'
RAT_DB_SHA = 'e8a0da9e0344bdbff2daaf9403d6fead76b5c591857f71a65c108fd2baca7edf'
RAT_COMMON = ['--batch_size', '128', '--coin_num', '11', '--feature_number', '4', '--output_step', '1000',
              '--test_portion', '0.08', '--trading_consumption', '0.0025', '--variance_penalty', '0.0', '--cost_penalty', '0.0',
              '--learning_rate', '0.0001', '--start', '2016/01/01', '--end', '2018/01/01', '--model_name', 'RAT',
              '--model_dim', '12', '--multihead_num', '2', '--local_context_length', '5', '--daily_interest_rate', '0.001']
RAT_P = ['--total_step', '80000', '--weight_decay', '1e-7', '--x_window_size', '30']
RAT_IDX = [1, 2, 3]
RAT_BUDGET = 12 * 3600
RAT_MIN_START = 16395          # F7 P1 실측(초)
MAX_ATT = 3

WC_SRC = WORK / 'wavecorr' / 'repo' / 'src'
WC_SEEDS = [1112, 1113, 1114, 1115, 1116]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


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


def jlog(path, **kw):
    kw['t'] = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(path, 'a') as f:
        f.write(json.dumps(kw, ensure_ascii=False) + '\n')


# ======================================================================= RAT 학습(오케스트레이터)
def rat_train():
    import shutil
    OUTD.mkdir(parents=True, exist_ok=True)
    assert sha(RAT_WRAP) == RAT_WRAP_SHA, 'F7 래퍼 해시 불일치'
    assert sha(WORK / 'RAT' / 'main.py') == RAT_MAIN_SHA and sha(WORK / 'RAT' / 'database' / 'Data.db') == RAT_DB_SHA
    gpu = subprocess.getoutput('nvidia-smi -L')
    assert 'GTX 1650' in gpu, gpu
    led = OUTD / 'rat_train.jsonl'
    used = 0.0
    for e in (json.loads(l) for l in open(led)) if led.exists() else []:
        if e.get('ev') == 'attempt_end' and not e.get('disk_stop'):
            used += e['seconds']
    for idx in RAT_IDX:
        rd = SS / f'rat_run{idx}'
        if (rd / 'done.json').exists():
            continue
        att = 0
        while True:
            if STOP.exists():
                jlog(led, ev='stop_file', idx=idx); print('STOP'); return
            remaining = RAT_BUDGET - used
            if remaining < RAT_MIN_START:
                jlog(led, ev='not_started_budget', idx=idx, remaining=remaining)
                print(f'run{idx}: 남은 예산 {remaining:.0f}s < {RAT_MIN_START}s → 시작 안 함'); return
            att += 1
            if att > MAX_ATT:
                (rd / 'done.json').write_text(json.dumps({'status': 'failed_max_attempts'})); break
            shutil.rmtree(rd, ignore_errors=True)
            shutil.copytree(str(WORK / 'RAT'), str(rd), ignore=shutil.ignore_patterns('.git', 'database', 'model', 'log', '__pycache__'))
            os.symlink(str(WORK / 'RAT' / 'database'), str(rd / 'database'))
            (rd / 'log').mkdir(); (rd / 'model').mkdir()
            cmd = [str(RAT_PY), str(RAT_WRAP)] + RAT_COMMON + RAT_P + ['--model_index', str(idx), '--model_dir', str(rd / 'model'),
                                                                     '--log_dir', str(rd / 'log')]
            env = dict(os.environ, RAT_TIMES=str(rd / 'times.jsonl'), RAT_ERR=str(rd / 'error.log'), RAT_CUT='0', RAT_RUN_DIR=str(rd),
                       TZ='Asia/Shanghai', LANG='en_US.UTF-8', MPLBACKEND='agg')
            jlog(led, ev='attempt_start', idx=idx, attempt=att, cap=remaining)
            t0 = time.time(); killed = disk = False
            with open(rd / 'stdout.log', 'w') as fo, open(rd / 'stderr.log', 'w') as fe:
                p = subprocess.Popen(cmd, cwd=str(rd), stdout=fo, stderr=fe, env=env, start_new_session=True)
                while p.poll() is None:
                    time.sleep(15)
                    if STOP.exists():
                        os.killpg(p.pid, signal.SIGKILL); disk = True; p.wait(); break
                    if time.time() - t0 > remaining:
                        os.killpg(p.pid, signal.SIGKILL); killed = True; p.wait(); break
            sec = time.time() - t0
            evs = [json.loads(l).get('ev') for l in open(rd / 'times.jsonl')] if (rd / 'times.jsonl').exists() else []
            ok = p.returncode == 0 and 'final_eval_done' in evs and (rd / 'model' / f'{idx}.pkl').exists() \
                and (rd / 'model' / f'final_{idx}.pkl').exists()
            jlog(led, ev='attempt_end', idx=idx, attempt=att, rc=p.returncode, seconds=sec, ok=ok, killed_at_cap=killed,
                 disk_stop=disk, events_tail=evs[-5:])
            if not disk:
                used += sec
            if disk:
                print('STOP(디스크)'); return
            if ok:
                (rd / 'done.json').write_text(json.dumps({'status': 'ok', 'attempt': att, 'seconds': sec, 'gpu': gpu}))
                break
            if killed:
                (rd / 'done.json').write_text(json.dumps({'status': 'killed_at_cap', 'attempt': att, 'seconds': sec})); return
            if (rd / 'error.log').exists():
                print(''.join(open(rd / 'error.log').readlines()[-20:]))
        # 측정(같은 GPU, 학습이 끝난 뒤)
        if json.loads((rd / 'done.json').read_text()).get('status') == 'ok':
            r = subprocess.run([str(RAT_PY), str(pathlib.Path(__file__).resolve()), 'rat-measure', str(rd), str(idx)], cwd=str(rd),
                               env=dict(os.environ, TZ='Asia/Shanghai', LANG='en_US.UTF-8'), capture_output=True, text=True)
            jlog(led, ev='measure', idx=idx, rc=r.returncode, err_tail=r.stderr[-1500:] if r.returncode else '')
    print('rat-train 끝')


# ======================================================================= RAT 측정(p37, cwd = 실행 폴더)
def rat_measure(rd, idx):
    import numpy as np
    rd = pathlib.Path(rd)
    sys.argv = ['main.py'] + RAT_COMMON + RAT_P + ['--model_index', str(idx), '--model_dir', str(rd / 'model'), '--log_dir', str(rd / 'log')]
    src = open('main.py').read()
    CUTLINE = '\nstart = parse_time(FLAGS.start)\n'
    assert src.count(CUTLINE) == 1
    head = src.split(CUTLINE)[0]
    g = sys.modules['__main__'].__dict__
    exec(compile(head, 'main.py', 'exec'), g)
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    import torch
    FL = g['FLAGS']
    DM = g['DataMatrices'](start=g['parse_time'](FL.start), end=g['parse_time'](FL.end), market="poloniex",
                           feature_number=FL.feature_number, window_size=FL.x_window_size, online=False, period=1800,
                           coin_filter=11, is_permed=False, buffer_bias_ratio=5e-5, batch_size=FL.batch_size,
                           volume_average_days=30, test_portion=FL.test_portion, portion_reversed=False)
    xw, lcl = FL.x_window_size, FL.local_context_length
    crit = g['Test_Loss'](FL.trading_consumption, FL.daily_interest_rate / 24 / 2, FL.variance_penalty, FL.cost_penalty, False)
    tst_compute = g['SimpleLossCompute_tst'](crit, None)
    t0i = int(DM._test_ind[0])
    assert (t0i - 1) not in set(int(i) for i in DM._train_ind)
    w_orig = np.asarray(DM.global_weights.values[t0i - 1], dtype=float)
    assert np.allclose(w_orig, 1 / 11)
    n_test_steps = len(DM._test_ind) - xw - 1

    def roll(model, s, steps, w0):
        b = DM.get_test_set_online(s, s + xw + steps, xw)
        X = b['X'].transpose((1, 0, 2, 3)).transpose((0, 1, 3, 2))
        srct = torch.tensor(X, dtype=torch.float).cuda()
        mask = (torch.ones(srct.size()[1], 1, xw) == 1)
        cur = srct.permute((3, 1, 2, 0))[:, :, xw - 1:, :]
        tmask = g['make_std_mask'](cur[:, :, 0:1, :], srct.size()[1])
        ys = torch.tensor(b['y'].transpose((0, 3, 2, 1)), dtype=torch.float).cuda()
        prev = torch.tensor(np.asarray(w0, dtype=float).reshape(1, 1, 11), dtype=torch.float).cuda()
        outs = []
        for j in range(steps):
            pad = srct[:, :, j + xw - 1 - lcl * 2 + 2:j + xw - 1, :].permute((3, 1, 2, 0)) if lcl > 1 else None
            out = model.forward(srct[:, :, j:j + xw, :], cur[:, :, j:j + 1, :], prev, mask, tmask, pad)
            outs.append(out.unsqueeze(0)); prev = out[:, :, 1:]
        W = torch.cat(outs, 0).permute(1, 0, 2, 3)
        return W, ys

    def metr(W, ys):
        _, pv, SR, CR, _, _, TO = crit(W, ys)
        return {'fAPV': float(pv.item()), 'SR': float(SR.item()), 'SR_pct': float(SR.item()) * 100, 'CR': float(CR.item()),
                'TO': float(TO.item())}

    import pandas as pd
    res = {'idx': idx, 'xw': xw, 'test_first': t0i, 'n_test_steps': n_test_steps, 'models': {}}
    tr = [int(i) for i in DM._train_ind]
    pts = np.linspace(tr[0] + 1, tr[-1] - xw - H, NPTS).astype(int)
    for tag, fn, summ in (('P', f'{idx}.pkl', 'train_summary.csv'), ('F', f'final_{idx}.pkl', 'final_summary.csv')):
        model = torch.load(str(rd / 'model' / fn)); model.eval()
        with torch.no_grad():
            # 검증: 코드 test_online과 같은가
            v_code = g['test_online'](DM, xw, model, tst_compute, lcl)[1].item()
            W0, ys0 = roll(model, t0i, n_test_steps, w_orig)
            m_orig = metr(W0, ys0)
            assert abs(m_orig['fAPV'] - v_code) <= 1e-6 * max(1.0, abs(v_code)), (m_orig['fAPV'], v_code)
            saved = float(pd.read_csv(str(rd / 'log' / summ))['fAPV'].iloc[-1])
            # 워밍업
            Ww, _ = roll(model, t0i - H, H, w_orig)
            w_warm = Ww[0, -1, 0, 1:].cpu().numpy()
            Wt, yst = roll(model, t0i, n_test_steps, w_warm)
            m_warm = metr(Wt, yst)
            Wc, ysc = roll(model, t0i, n_test_steps, np.zeros(11))
            m_cash = metr(Wc, ysc)
            # α_eff
            gx, gl = [], []
            for s in pts:
                We, _ = roll(model, int(s), H, np.full(11, 1 / 11))
                Wc2, _ = roll(model, int(s), H, np.zeros(11))
                we, wc = We[0, :, 0, :].cpu().numpy(), Wc2[0, :, 0, :].cpu().numpy()
                gx.append(np.abs((1 - we[:, 0]) - (1 - wc[:, 0]))); gl.append(np.abs(we - wc).sum(1) / 2)
            gx, gl = np.mean(gx, 0), np.mean(gl, 0)
        res['models'][tag] = {
            'alpha_eff': alpha_from_gap(gx), 'alpha_eff_L1_aux': alpha_from_gap(gl), 'gap_head': [float(v) for v in gx[:5]],
            'gap_sum': float(gx.sum()), 'orig': m_orig, 'warm': m_warm, 'cash_aux': m_cash,
            'd_fAPV_rel': (m_orig['fAPV'] - m_warm['fAPV']) / m_orig['fAPV'], 'd_SR_pct': m_orig['SR_pct'] - m_warm['SR_pct'],
            'verify_code_test_online_fAPV': v_code, 'saved_summary_fAPV': saved, 'saved_minus_ours': saved - m_orig['fAPV'],
            'w_warm_exposure': float(w_warm.sum()), 'w_orig_exposure': float(w_orig.sum())}
        del model; torch.cuda.empty_cache()
    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / f'rat_run{idx}.json').write_text(json.dumps(res, indent=1))
    print('rat-measure done', idx)


# ======================================================================= WaveCorr 측정(p37 TF1, cwd = repo/src)
def wc_measure(seed):
    import numpy as np
    os.chdir(str(WC_SRC)); sys.path.insert(0, str(WC_SRC))
    sys.argv = ['wavecorr_run.py']
    src = open('wavecorr_run.py', encoding='utf-8').read()
    CUTLINE = "\n# load the data from the assigned data set\n"
    assert src.count(CUTLINE) == 1
    head, rest = src.split(CUTLINE)
    g = {'__name__': 'wavecorr_run_head', '__builtins__': __builtins__}
    exec(compile(head, 'wavecorr_run.py', 'exec'), g)
    assert g['epochs'] == 3000 and g['dataset_name'] == 'can' and g['tradeFee'] == 0.0005 and g['RNN'] is True
    g['train_mode'] = 0
    exec(compile(CUTLINE.lstrip('\n') + rest, 'wavecorr_run.py', 'exec'), g)
    import tensorflow as tf
    data, N, T = g['data'], g['number_of_stocks'], g['trainSetLen']
    path = f'results/can_waveCorr_{N}stocks_seed{seed}_permutation1'
    ag = g['agent_manager'](g['dataset_name'], data.x, data.y, g['learningRate'], g['decayRate'], g['minimmumRate'],
                            g['minibatchSize'], g['epochs'], N, g['lookback_window'], g['planning_horizon'], g['tradeFee'], seed,
                            constrain_action=False, maxStockWeight=g['maxStockWeight'], network_model=g['network_model'],
                            net_depth=g['net_depth'], regularizer_multiplier=g['regularizer_multiplier'], RNN=g['RNN'],
                            keep_prob_value=g['keep_prob_value'])
    x, y = data.x, data.y
    LB, PH, MB = ag.lookback_window, ag.planning_horizon, ag.minibatchSize
    assert MB == 1 and LB == 32 and PH == 32
    last_index = y.shape[0] - LB - PH
    ts = [1 + i * ag.minibatchCount for i in range(int(last_index / ag.minibatchCount) + 1)] + [last_index]
    ts = ts + [last_index] * (MB - len(ts) % MB)
    ts = np.reshape(np.array(ts), [-1, MB])
    pvm_saved = np.loadtxt(path + '/pvm.csv', delimiter=',')

    def code_metrics(v):
        n = len(v); ar = v[-1] ** (252 / n) - 1
        lr = np.diff(np.log(v)); vol = np.std(lr) * np.sqrt(252)
        return {'AR': float(ar), 'vol': float(vol), 'SR': float(ar / vol)}

    def passes(sess, spots, overrides):
        ag.pvm = pvm_saved.copy(); ag.pvm_reward = np.ones(len(y))
        for pos, w in overrides.items():
            ag.pvm[pos] = w
        for t_ in spots:
            ag.trainOnMinibatch_PG(sess, t_, x, y, do_backprop=False, is_train=False, trainSetLen=T, off_policy=False)
        return ag.pvm.copy(), ag.pvm_reward.copy()

    def consistent_apv(pvm):
        w = pvm[T - 1:]; r = y[T - 1:]
        out = []
        for k in range(1, len(w)):
            wp = w[k - 1] * r[k - 1]; wp = wp / wp.sum()
            mu = ag.calculateMu(wp.reshape(1, 1, -1), w[k].reshape(1, 1, -1))[0, 0]
            out.append(float(np.dot(w[k], r[k]) * mu))
        return np.cumprod(out)

    def drift(w, r):
        z = w * r; return z / z.sum()

    with tf.compat.v1.Session() as sess:
        sess.run(ag.init_op)
        ag.saver.restore(sess, path + '/model.ckpt')
        pv_o, rw_o = passes(sess, ts, {})
        apv_o = np.cumprod(rw_o[T:])
        saved_apv = np.array([float(l.split(',')[1]) for l in open(path + '/APV_.csv') if l.strip()])
        starts = [int(r[0]) for r in ts]
        # 워밍업: 결정 위치 i+31 <= T-60 인 마지막 청크
        k0 = max(k for k, i in enumerate(starts) if i + LB - 1 <= T - H)
        i0 = starts[k0]
        pv_w, rw_w = passes(sess, ts[k0:], {i0 + LB - 2: np.full(N, 1 / N)})
        apv_w = np.cumprod(rw_w[T:])
        kc = max(k for k, i in enumerate(starts) if i + LB - 1 <= T)
        ic = starts[kc]
        pv_c, rw_c = passes(sess, ts[kc:], {ic + LB - 2: np.full(N, 1 / N)})
        apv_c = np.cumprod(rw_c[T:])
        # α_eff
        kmax = max(k for k, i in enumerate(starts) if i + LB - 1 + H <= T and k + 1 < len(starts))
        ks = np.linspace(1, kmax, NPTS).astype(int)
        gaps = []
        one = np.zeros(N); one[0] = 1.0
        for k in ks:
            i = starts[k]; pos = i + LB - 2
            pe, _ = passes(sess, ts[k:k + 2], {pos: np.full(N, 1 / N)})
            pc, _ = passes(sess, ts[k:k + 2], {pos: one})
            d0 = np.abs(drift(np.full(N, 1 / N), y[pos]) - drift(one, y[pos])).sum()
            gaps.append(np.abs(pe[pos + 1:pos + 1 + H] - pc[pos + 1:pos + 1 + H]).sum(1) / d0)
        gap = np.mean(gaps, 0)
    m_o, m_w, m_c = code_metrics(apv_o), code_metrics(apv_w), code_metrics(apv_c)
    res = {'seed': seed, 'trainSetLen': T, 'n_test': int(len(apv_o)), 'warm_len': int(T - (i0 + LB - 1)), 'cold_offset': int(T - (ic + LB - 1)),
           'alpha_eff': alpha_from_gap(gap), 'gap_head': [float(v) for v in gap[:5]], 'gap_sum': float(gap.sum()),
           'orig': m_o, 'warm': m_w, 'cold_aux': m_c, 'd_SR': m_o['SR'] - m_w['SR'],
           'saved_APV_SR': code_metrics(saved_apv)['SR'], 'saved_minus_ours_SR': code_metrics(saved_apv)['SR'] - m_o['SR'],
           'consistent_cost_aux': {'orig_SR': code_metrics(consistent_apv(pv_o))['SR'], 'warm_SR': code_metrics(consistent_apv(pv_w))['SR']},
           'test_weight_L1_orig_vs_warm_first5': [float(v) for v in np.abs(pv_o[T:T + 5] - pv_w[T:T + 5]).sum(1)]}
    res['consistent_cost_aux']['d_SR'] = res['consistent_cost_aux']['orig_SR'] - res['consistent_cost_aux']['warm_SR']
    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / f'wc_seed{seed}.json').write_text(json.dumps(res, indent=1))
    print('wc-measure done', seed)


# ======================================================================= 판정
def judge(od):
    import statistics as st
    od = pathlib.Path(od)
    out = {'prereg': 'notes/startstate_costaware_prereg.md (e9211dc, 036e3fd)', 'RAT': {}, 'WaveCorr': {}}
    rows = []
    for p in sorted(od.glob('rat_run*.json')):
        r = json.loads(p.read_text())
        for tag, m in r['models'].items():
            rows.append(dict(model=f"run{r['idx']}{tag}", kind=tag, alpha=m['alpha_eff'], dF=abs(m['d_fAPV_rel']), dS=abs(m['d_SR_pct'])))
    if rows:
        n = len(rows); k = sum(r['alpha'] < 0.5 for r in rows)
        mF, mS = st.median([r['dF'] for r in rows]), st.median([r['dS'] for r in rows])
        out['RAT'] = {'n_models': n, 'models': rows, 'H-I': {'n_alpha_lt_0.5': k, 'verdict': '관성을 학습했다' if k >= n / 2 else '학습하지 않았다'},
                      'H-S': {'median_abs_dfAPV_rel': mF, 'median_abs_dSR_pct': mS,
                              'verdict': '보고 지표에 실질적 영향' if (mF >= 0.05 or mS >= 0.1) else '실질적 영향 아님'},
                      'aux_by_kind': {t: {'median_abs_dfAPV_rel': st.median([r['dF'] for r in rows if r['kind'] == t]),
                                          'median_abs_dSR_pct': st.median([r['dS'] for r in rows if r['kind'] == t]),
                                          'n_alpha_lt_0.5': sum(r['alpha'] < 0.5 for r in rows if r['kind'] == t)}
                                      for t in ('P', 'F') if any(r['kind'] == t for r in rows)}}
    wr = [json.loads(p.read_text()) for p in sorted(od.glob('wc_seed*.json'))]
    if wr:
        n = len(wr); k = sum(r['alpha_eff'] < 0.5 for r in wr); mS = st.median([abs(r['d_SR']) for r in wr])
        out['WaveCorr'] = {'n_models': n, 'models': [dict(seed=r['seed'], alpha=r['alpha_eff'], dSR=r['d_SR']) for r in wr],
                           'H-I': {'n_alpha_lt_0.5': k, 'verdict': '관성을 학습했다' if k >= n / 2 else '학습하지 않았다'},
                           'H-S': {'median_abs_dSR': mS, 'verdict': '보고 지표에 실질적 영향' if mS >= 0.1 else '실질적 영향 아님'}}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return out


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'rat-train':
        rat_train()
    elif mode == 'rat-measure':
        rat_measure(sys.argv[2], int(sys.argv[3]))
    elif mode == 'wc-measure':
        wc_measure(int(sys.argv[2]))
    elif mode == 'judge':
        r = judge(sys.argv[2])
        if len(sys.argv) > 3:
            pathlib.Path(sys.argv[3]).write_text(json.dumps(r, ensure_ascii=False, indent=1))
