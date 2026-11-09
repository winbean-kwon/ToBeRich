# -*- coding: utf-8 -*-
# RAT F7 판정(사전 등록 notes/funnel_f7_rat_prereg.md §4·§5). 확정 커밋에 포함되고, 결과를 본 뒤 바꾸지 않는다.
# 사용: python3 funnel_f7_rat_judge.py <rat_f7 결과 폴더>   (P 5회 완료 또는 11-24 이후 1회 실행)
# 표준 라이브러리 + numpy만 쓴다.
import csv, json, math, sys, pathlib
import numpy as np

REPORT = {'APV': 156.53, 'SR_pct': 7.13, 'CR': 304.26}
MTL = {'APV': 19.69, 'SR_pct': 6.90, 'CR': 79.21}
R1_A = (156.53 - 68.42, 156.53 + 68.42)        # 주 판정(사용자 결정 2026-11-09): v3 ½(RAT−MTL)
R1_B = (156.53 - 17.7, 156.53 + 17.7)          # 보조: 예측구간 1.96·√(2·14.25²/5)
COST = 0.0025
UCRP_PAPER = 2.37


def mdd(pc):
    pv, peak, dd = 1.0, 0.0, [0.0]
    v = []
    for i, x in enumerate(pc):
        pv = x if i == 0 else v[-1] * x
        v.append(pv)
        if pv > peak:
            peak = pv; dd.append(0.0)
        else:
            dd.append(1.0 - pv / peak)
    return max(dd)


def read_summary(p):
    with open(p, newline='') as f:
        row = next(csv.DictReader(f))
    pc = np.array([float(x) for x in row['backtest_test_history'].split(',') if x.strip()])
    sr_code = float(row['SR'])
    return {'fAPV': float(row['fAPV']), 'SR_pct': sr_code * 100.0, 'CR': float(row['CR']), 'TO': float(row['TO']),
            'MDD': mdd(pc), 'n_steps': int(len(pc)),
            'check_fAPV_from_history': float(np.prod(pc)),
            'check_SR_pct_from_history': float((pc - 1).mean() / (pc - 1).std(ddof=1) * 100.0)}, pc


def ucrp(rel):
    # rel: [coins, T] 종가 비율. 현금 포함 12자산 균등, 매 시점 재조정, 코드와 같은 비용식, 이자 0.
    T = rel.shape[1]
    c = np.vstack([np.ones((1, T)), rel])            # [12, T]
    w = np.full(c.shape[0], 1.0 / c.shape[0])
    out, prev_drift = [], None
    for t in range(T):
        r = float(w @ c[:, t])
        pc = 1.0 if prev_drift is None else 1.0 - np.abs(prev_drift - w).sum() * COST
        out.append(r * pc)
        prev_drift = w * c[:, t] / r
    out = np.array(out)
    apv = float(np.prod(out))
    return {'APV': apv, 'SR_pct': float((out - 1).mean() / (out - 1).std(ddof=1) * 100.0), 'CR': apv / mdd(out), 'n_steps': T}


def cond_block(root, cond):
    runs, F = [], []
    for i in range(1, 6):
        d = root / f'{cond}{i}'
        done = d / 'done.json'
        if not done.exists() or json.loads(done.read_text()).get('status') != 'ok':
            continue
        m, pc = read_summary(d / 'train_summary.csv')
        f, _ = read_summary(d / 'final_summary.csv')
        sel = [json.loads(l) for l in open(sorted(d.glob('times.attempt*.jsonl'))[-1]) if '"ckpt"' in l]
        m['idx'] = i; m['selected_ckpt_step'] = sel[-1]['step'] if sel else None; m['n_ckpt_saves'] = len(sel)
        f['idx'] = i
        runs.append(m); F.append(f)
    return runs, F


def summarize(runs):
    if not runs:
        return None
    a = np.array([r['fAPV'] for r in runs])
    return {'n': len(runs), 'mean_fAPV': float(a.mean()), 'min_fAPV': float(a.min()), 'max_fAPV': float(a.max()),
            'mean_SR_pct': float(np.mean([r['SR_pct'] for r in runs])), 'mean_CR': float(np.mean([r['CR'] for r in runs])),
            'n_in_R1_A': int(sum(R1_A[0] <= x <= R1_A[1] for x in a)), 'n_in_R1_B': int(sum(R1_B[0] <= x <= R1_B[1] for x in a)),
            'n_beat_MTL_all3': int(sum(r['fAPV'] > MTL['APV'] and r['SR_pct'] > MTL['SR_pct'] and r['CR'] > MTL['CR'] for r in runs))}


def judge(runs):
    s = summarize(runs)
    n = s['n'] if s else 0
    if n >= 3:
        m = s['mean_fAPV']
        r1 = 'pass' if R1_A[0] <= m <= R1_A[1] else ('fail_low' if m < R1_A[0] else 'fail_high')
        r1_b = 'pass' if R1_B[0] <= m <= R1_B[1] else ('fail_low' if m < R1_B[0] else 'fail_high')
    else:
        r1, r1_b = 'undecidable', 'undecidable'
    if n >= 5:
        r2 = 'pass' if s['n_beat_MTL_all3'] >= math.ceil(0.7 * n) else 'fail'
    else:
        r2 = 'undecidable'
    if 'undecidable' in (r1, r2):
        grade = '판정 불가'
    else:
        k = (r1 == 'pass') + (r2 == 'pass')
        grade = {2: '재현', 1: '부분 재현', 0: '미재현'}[k]
    return s, r1, r1_b, r2, grade


def main():
    root = pathlib.Path(sys.argv[1])
    P, PF = cond_block(root, 'P')
    R, RF = cond_block(root, 'R')
    sP, r1, r1_b, r2, grade = judge(P)
    sPF = summarize(PF)
    # 고정 해석(§5)
    if grade == '재현':
        interp = '논문 절차를 공개 코드와 저자 데이터로 실행해 Crypto-A 보고 수치를 재현했다. 보고 절차는 시험 구간으로 체크포인트를 고른다.'
        if sPF and not (R1_A[0] <= sPF['mean_fAPV'] <= R1_A[1]):
            interp += ' 시험 구간 선택 없이 학습 마지막 모델을 쓰면 보고 수치에 미치지 못했다.'
    elif grade == '부분 재현':
        interp = f'부분 재현: R1={r1}, R2={r2}.'
    elif grade == '미재현':
        interp = '재현하지 못했다(' + ('보고값보다 높은 방향의 불일치' if r1 == 'fail_high' else '보고값보다 낮음') + ').'
    else:
        interp = '판정 불가: 끝난 값만 기술한다.'
    u = None
    rel_p = root / 'P1' / 'test_close_relatives.npy'
    if rel_p.exists():
        u = ucrp(np.load(rel_p))
        u['rel_diff_vs_paper'] = (u['APV'] - UCRP_PAPER) / UCRP_PAPER
        u['flag_data_mismatch'] = abs(u['rel_diff_vs_paper']) > 0.20
        if P:
            u['steps_match_P1'] = (u['n_steps'] == P[0]['n_steps'])
    res = {'grade_P': grade, 'R1_A(주)': r1, 'R1_B(보조)': r1_b, 'R2': r2, 'interpretation': interp,
           'R1_A_range': R1_A, 'R1_B_range': R1_B, 'report': REPORT, 'MTL': MTL,
           'P_summary': sP, 'P_runs': P, 'F_summary(보조)': sPF, 'F_runs(보조)': PF,
           'R_summary(병기)': summarize(R), 'R_runs(병기)': R, 'R_F_summary(병기)': summarize(RF), 'UCRP(점검)': u}
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (root / 'f7_result.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
