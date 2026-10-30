# T1 DeepAries(CIKM 2025) — O1 재현·O2 재평가 실행기(로컬 맥 CPU).
# 사전 등록: notes/prereg_reeval_v3.md 2장(T1 집계량)·3장(O1)·4장(O2), O5 결과 notes/deeparies_o5_result.md.
# 판정 기준은 그 문서 그대로이고, 이 파일은 그 기준을 계산하는 방법을 실행 전에 고정한다.
#
# 사용:
#   python3 deeparies_run.py run <창> <조건> <시드>     # 학습 1회 + 백테스트, 결과 deeparies/runs/{창}_{조건}_s{시드}.csv
#   python3 deeparies_run.py judge1 | judge2             # O1 | O2 사전 판정
#
# 고정 사항 — 공통:
# - 코드: dmis-lab/DeepAries @634f559, 저장소 밖 .t1env/DeepAries(setup_t1env.sh). main.py의 main()을 그대로 부른다.
#   인자는 --seed와 (롤링 창만) --valid_year·--test_year뿐이고 나머지는 코드 기본값(iTransformer, train_epochs 1,
#   patience 3, lr 1e-5, num_stocks 20, horizons 1 5 20, fee_rate 0.0001, complex_fee False)이다.
# - 데이터: 저장소 포함 data/dj30/dj30_general_data.csv(26종목, 2000-01-03~2025-02-07), 다시 받지 않는다.
#   md5 1c3432510aa93980f6534d6906315041. dj30_data.csv(원자료)는 main()이 존재만 확인한다.
# - 수정(v3 2.3): (4) 결과 기록 — TradingEnvironment를 기록용 하위 클래스로 바꿔 백테스트의 매 스텝 가중치·구간·
#   시작일과 코드가 계산한 가치를 저장하고, vali()의 검증 손실을 저장한다(계산 동작 동일). (2) 롤링 창은 입력 CSV를
#   창 끝 날짜에서 자른다(코드에 끝 날짜 인자가 없음). (3) 조건 (b)(c)는 step의 비용 계산을 U1 참조 명세로 바꾼다.
#   torch 스레드 2개(병렬 4개). 체크포인트(약 27MB)는 디스크 여유가 없어 실행 후 지운다.
# - 창(v3 U3, 테스트 시작 = --test_year, 검증 = 직전 1년, 그 이전 학습):
#   W0 = 2021-12-31~2025-02-07(코드 기본, 자르지 않음), W1 = 2015-12-31~2017-12-31, W2 = 2017-12-31~2019-12-31,
#   W3 = 2019-12-31~2021-12-31. 롤링 창 CSV는 date < 창 끝인 행만 남긴다. 코드 구조상 거래는 테스트 시작 후
#   seq_len(20)거래일부터, 마지막 시작일은 끝에서 seq_len+pred_len(40)거래일 전까지다(W0와 같은 구조).
# - 조건(v3 U6): (a) 원래 코드, (b) U1 c = c_paper = 0.0001, (c) U1 c = 0.001. 학습·검증·백테스트 env 모두 바꾼다.
#   U1: 현금 시작(직전 보유 0), τ = Σ|w − w′|, V ← V·(1 − c·τ)·(1 + w·r_h), w′ ← w⊙(1+r_h)/(1 + w·r_h).
# - 실행 목록: O1 = W0 (a) 시드 0–9. O2 = W0 (b)(c) 시드 0–9, W1–W3 (a)(b) 시드 0–4(v3 9장). O2 실행은 O1 판정이
#   재현 또는 부분 재현일 때만 한다(v3 4장).
#
# 고정 사항 — O1(judge1):
# - 시드 10개 각각의 코드 출력 CAGR·MDD(코드 식: 가치 = [1] + 스텝 후 가치, 날짜 = [테스트 첫날] + 스텝 시작일,
#   CAGR = V_끝^(365/일수) − 1)를 기록 가치·날짜로 다시 계산하고, 출력 값(소수 둘째 자리)과 0.006%p 안에서 같은지 확인한다.
# - 선택 시드 = 검증 손실 최소(논문 5.1절). R1: |CAGR − 7.90| ≤ 0.87%p 이고 |MDD| − 13.67 의 절댓값 ≤ 5.0%p.
# - R2: CAGR이 같은 기간 ^DJI CAGR보다 높은 시드 ≥ 7/10. ^DJI(deeparies/data/dji.csv, Yahoo 종가, auto_adjust=False)
#   CAGR = (P(날짜 끝)/P(날짜 처음))^(365/일수) − 1, 날짜는 그 시드의 코드 날짜 열 처음·끝(그날 종가가 없으면 직전 거래일).
# - 등급: R1·R2 모두 재현, 하나 부분 재현, 없음 미재현.
#
# 고정 사항 — O2(judge2):
# - 무상태 정책(입력 = 시장 텐서)이라 가중치·구간 선택은 env 비용과 무관하다. 그래서 평가는 기록한 가중치로 사후 계산한다.
#   스텝 k(시작 거래일 d_k, 구간 h_k, 목표 w_k)를 일간 목표 행렬로 펼친다: d_k 다음 행에 w_k, 보유 중인 날은 드리프트
#   보유(τ = 0). 행 j는 날짜 j−1 → j 수익에 적용. 범위 = 첫 시작일 ~ 마지막 스텝의 끝(d_k + h_k).
#   일간 수익은 같은 CSV의 close(코드 라벨과 같은 가격)로 계산한다. 이 펼침의 무비용 곱이 코드 라벨 w·r_h와 같은지 확인한다.
# - Δ = (252/N)·Σ log(1 + 순수익)(방법) − 같은 값(매일 등가중 26종목, 같은 범위·U1 비용·현금 시작).
#   계산은 finrl_t3_run.u1_returns·baseline_weights·ann_log 그대로다(N = 행 수, 첫 행 0 포함 — T3와 같은 정의).
# - 주 판정: 조건 (b), c = 0.0001. 창 분류: W0 ≥8/10, 롤링 ≥4/5 시드에서 Δ>0 우위, Δ<0 열위, 그 밖 불확정.
#   대상 분류: W0 우위이고 우위 창 ≥3/4 → 유지, W0 열위이거나 열위 창 ≥2(= ½ 이상) → 소실, 그 밖 불확정.
#   모든 창 시드 중앙값 |Δ| < 2%p/년이면 '차이 작음'.
# - 2차: (a)@0.0001, (c)@0.001, (b)@0.001, 매월·buy-and-hold·최댓값 기준선, 블록 부트스트랩 CI·샤프 차이 p(T3와 같은
#   함수), O4 = 원래 env 기록 가치의 연율 로그 성장 − U1 c=0.0001 값(조건 (a)), 평균 회전율.
#
# 고정 사항 — O1 변형 E(judge_e, notes/deeparies_e10_prereg.md, 실행 전 커밋):
# - 조건 e1 = 원래 코드(train_epochs 1), e10 = 원래 코드 + --train_epochs 10(README 'Training with more epochs').
#   나머지 인자·데이터·기록은 (a)와 같다. 창 W0, 시드 0–9, Colab에서 시드마다 e1 → e10 순으로 같은 런타임에서 실행.
# - 경로: 환경변수 DA_CODE(공식 코드 위치), DA_RUNS(결과 폴더), DA_THREADS(torch 스레드, 기본 2)로 바꿀 수 있다.
import sys, os, json, time, hashlib, pathlib, re, io, contextlib, types

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
D = HERE / 'deeparies'
CODE = pathlib.Path(os.environ.get('DA_CODE', ROOT / '.t1env' / 'DeepAries'))
RUNS = pathlib.Path(os.environ.get('DA_RUNS', D / 'runs'))
GEN_MD5 = '1c3432510aa93980f6534d6906315041'
WINDOWS = {'W0': ('2021-12-31', None, '2020-12-31'), 'W1': ('2015-12-31', '2017-12-31', '2014-12-31'),
           'W2': ('2017-12-31', '2019-12-31', '2016-12-31'), 'W3': ('2019-12-31', '2021-12-31', '2018-12-31')}
COND_COST = {'a': None, 'b': 0.0001, 'c': 0.001, 'e1': None, 'e10': None}
COND_EPOCHS = {'e1': 1, 'e10': 10}
C_PAPER = 0.0001
REPORTED_CAGR, TOL_CAGR, REPORTED_MDD, TOL_MDD = 7.90, 0.87, 13.67, 5.0
RUNS_O1 = [('W0', 'a', s) for s in range(10)]
RUNS_O2 = [('W0', c, s) for c in 'bc' for s in range(10)] + [(w, c, s) for w in ('W1', 'W2', 'W3') for c in 'ab' for s in range(5)]


def run_path(w, c, s):
    return RUNS / f'{w}_{c}_s{s}.csv'


def window_csv(w):
    # 롤링 창 입력: date < 창 끝인 행만(파일 순서 유지). 한 번 만들고 다시 쓴다(원자적 쓰기).
    src = CODE / 'data' / 'dj30' / 'dj30_general_data.csv'
    end = WINDOWS[w][1]
    if end is None:
        return src
    dst = CODE.parent / 'data' / f'dj30_general_{w}.csv'
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        lines = src.read_text().splitlines(keepends=True)
        keep = [lines[0]] + [l for l in lines[1:] if l[:10] < end]
        tmp = dst.with_suffix('.tmp'); tmp.write_text(''.join(keep)); os.replace(tmp, dst)
    return dst


def cmd_run(w, c, s):
    out = run_path(w, c, s)
    if out.exists():
        print('이미 있음', out.name); return
    src = CODE / 'data' / 'dj30' / 'dj30_general_data.csv'
    assert hashlib.md5(src.read_bytes()).hexdigest() == GEN_MD5, '데이터 해시 불일치'
    # 실행마다 작업 디렉터리를 따로 둔다: 코드가 ./data/dj30/·./checkpoints/·./results/를 상대 경로로 쓴다.
    wd = CODE.parent / 'work' / f'{w}_{c}_s{s}'
    import shutil
    shutil.rmtree(wd, ignore_errors=True); (wd / 'data' / 'dj30').mkdir(parents=True)
    for n in ('main.py', 'exp', 'models', 'layers', 'utils', 'data_provider', 'complete_dj30_tickers.csv'):
        (wd / n).symlink_to(CODE / n)
    (wd / 'data' / 'dj30' / 'dj30_data.csv').symlink_to(CODE / 'data' / 'dj30' / 'dj30_data.csv')
    (wd / 'data' / 'dj30' / 'dj30_general_data.csv').symlink_to(window_csv(w))
    smoke = os.environ.get('DA_SMOKE') == '1'   # 구현 점검용(공개 체크포인트 추론). 판정 실행에는 쓰지 않는다.
    if smoke:
        (wd / 'checkpoints').symlink_to(CODE / 'checkpoints'); out = D / 'smoke' / out.name
    os.chdir(wd); sys.path.insert(0, str(wd))
    import numpy as np, torch
    torch.set_num_threads(int(os.environ.get('DA_THREADS', '2')))
    import exp.exp_DeepAries as E
    import main as M
    rec = {'steps': [], 'vali': []}
    last = {}
    cost = COND_COST[c]

    class Rec(E.TradingEnvironment):
        def get_sample(self, dataset, index, device):
            last['ds'], last['i'] = dataset, index
            return super().get_sample(dataset, index, device)

        def reset(self):
            super().reset(); self.hold = np.zeros(self.args.total_stocks)

        def step(self, weights, returns):
            if cost is None:
                r = super().step(weights, returns)
            else:   # U1 참조 명세(헤더). 메모리 기록은 원래 else 분기와 같다.
                wv = weights.detach().cpu().numpy() if isinstance(weights, torch.Tensor) else weights
                rv = returns.detach().cpu().numpy() if isinstance(returns, torch.Tensor) else returns
                self.weights_memory.append(wv)
                tau = np.abs(wv - self.hold).sum(); g = 1 + float(np.sum(wv * rv))
                new = self.portfolio_value * (1 - cost * tau) * g
                r = (new - self.portfolio_value) / self.portfolio_value
                self.hold = wv * (1 + rv) / g
                self.portfolio_value = new
                self.portfolio_return_memory.append(r); self.asset_memory.append(new)
            ds = last.get('ds')
            if ds is not None and ds.flag == 'backtest':
                wv = weights.detach().cpu().numpy() if isinstance(weights, torch.Tensor) else weights
                rv = returns.detach().cpu().numpy() if isinstance(returns, torch.Tensor) else returns
                rec['steps'].append((str(ds.unique_dates[last['i'] + self.args.seq_len])[:10], last['i'],
                                     np.array(wv, dtype=float), np.array(rv, dtype=float), self.portfolio_value))
                rec['first_date'] = str(ds.unique_dates[0])[:10]
            return r

    E.TradingEnvironment = Rec
    orig_vali = E.Exp_DeepAries.vali

    def vali(self):
        v = orig_vali(self); rec['vali'].append(float(v[0])); return v
    E.Exp_DeepAries.vali = vali

    argv = ['main.py', '--seed', str(s)]
    if c in COND_EPOCHS:
        assert w == 'W0'
        argv += ['--train_epochs', str(COND_EPOCHS[c])]
    if w != 'W0':
        argv += ['--test_year', WINDOWS[w][0], '--valid_year', WINDOWS[w][2]]
    if smoke:
        argv += ['--is_training', '0']
        rec['vali'].append(float('nan'))
    sys.argv = argv
    buf = io.StringIO(); t0 = time.time()
    with contextlib.redirect_stdout(buf):
        M.main()
    mins = (time.time() - t0) / 60
    txt = buf.getvalue()
    printed = {k: float(re.search(p, txt).group(1)) for k, p in
               (('cagr', r'Annualized Return: ([-\d.]+)%'), ('mdd', r'Maximum Drawdown: ([-\d.]+)%'))}
    # 로그만 남기고 작업 디렉터리(체크포인트 포함)는 끝에 지운다
    logs = list((wd / 'results').glob('*/experiment.log'))
    (RUNS / 'logs').mkdir(parents=True, exist_ok=True)
    if logs:
        shutil.copy(logs[0], RUNS / 'logs' / f'{w}_{c}_s{s}.log')
    import pandas as pd
    tics = sorted(pd.read_csv(window_csv(w), usecols=['tic']).tic.unique())   # 코드의 종목 순서(sort_index)
    st = rec['steps']
    df = pd.DataFrame({'date': [x[0] for x in st], 'i': [x[1] for x in st], 'pv': [x[4] for x in st]})
    for k, t in enumerate(tics):
        df[f'w_{t}'] = [x[2][k] for x in st]
    for k, t in enumerate(tics):
        df[f'r_{t}'] = [x[3][k] for x in st]
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix('.tmp'); df.to_csv(tmp, index=False, float_format='%.10g')
    meta = {'vali_loss': rec['vali'], 'first_date': rec['first_date'], 'printed': printed, 'minutes': round(mins, 2),
            'torch': torch.__version__, 'numpy': np.__version__, 'argv': argv[1:],
            'device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}
    out.with_suffix('.json').write_text(json.dumps(meta, indent=1))
    os.replace(tmp, out)
    os.chdir(ROOT); shutil.rmtree(wd, ignore_errors=True)
    print(f'{w} {c} seed {s}: {mins:.1f}분, CAGR {printed["cagr"]}%, MDD {printed["mdd"]}%', flush=True)


def load_run(w, c, s):
    import pandas as pd
    p = run_path(w, c, s)
    return pd.read_csv(p), json.loads(p.with_suffix('.json').read_text())


def code_metrics(df, meta):
    # 코드 backtest의 식 그대로(헤더 O1)
    import numpy as np, pandas as pd
    pv = np.r_[1.0, df.pv.to_numpy()]
    dates = pd.to_datetime([meta['first_date']] + list(df.date))
    days = (dates[-1] - dates[0]).days
    cagr = (pv[-1] ** (365 / days) - 1) * 100
    mdd = ((pv - np.maximum.accumulate(pv)) / np.maximum.accumulate(pv)).min() * 100
    return cagr, mdd, dates[0], dates[-1]


def cmd_judge1(cond='a', out_name='judge_o1.json'):
    import numpy as np, pandas as pd
    dji = pd.read_csv(D / 'data' / 'dji.csv', index_col=0, parse_dates=True).Close
    rows = []
    for w, c, s in [('W0', cond, s) for s in range(10)]:
        df, meta = load_run(w, c, s)
        cagr, mdd, d0, d1 = code_metrics(df, meta)
        assert abs(cagr - meta['printed']['cagr']) < 0.006 and abs(mdd - meta['printed']['mdd']) < 0.006, (s, cagr, mdd, meta['printed'])
        p0, p1 = dji[:d0].iloc[-1], dji[:d1].iloc[-1]
        dcagr = ((p1 / p0) ** (365 / (d1 - d0).days) - 1) * 100
        rows.append({'시드': s, '검증 손실': min(meta['vali_loss']),
                     'CAGR(%)': round(cagr, 3), 'MDD(%)': round(mdd, 3), '^DJI CAGR(%)': round(dcagr, 3),
                     '기간': f'{d0.date()}~{d1.date()}', '검증 손실 기록': meta['vali_loss'],
                     '장치': meta.get('device'), '분': meta['minutes']})
    sel = min(rows, key=lambda r: r['검증 손실'])
    r1 = abs(sel['CAGR(%)'] - REPORTED_CAGR) <= TOL_CAGR and abs(abs(sel['MDD(%)']) - REPORTED_MDD) <= TOL_MDD
    k = sum(r['CAGR(%)'] > r['^DJI CAGR(%)'] for r in rows)
    r2 = k >= 7
    res = {'시드별': rows, '선택 시드(검증 손실 최소)': sel['시드'],
           'R1': {'선택 CAGR': sel['CAGR(%)'], '선택 MDD': sel['MDD(%)'], '보고값': [REPORTED_CAGR, REPORTED_MDD],
                  '허용 폭': [TOL_CAGR, TOL_MDD], '통과': bool(r1)},
           'R2': {'^DJI 초과 시드 수': int(k), '기준': '≥7/10', '통과': bool(r2)},
           '등급': '재현' if r1 and r2 else ('부분 재현' if r1 or r2 else '미재현')}
    (RUNS / out_name).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != '시드별'}, ensure_ascii=False, indent=1))
    return res


def cmd_judge_e():
    # O1 변형 E: e10·e1 각각에 O1 기준을 그대로 적용하고, 시드별 짝 차이(e10 − e1)를 2차로 적는다.
    import numpy as np
    out = {}
    for c in ('e1', 'e10'):
        out[c] = cmd_judge1(c, f'judge_{c}.json')
    a, b = out['e1']['시드별'], out['e10']['시드별']
    d = [y['CAGR(%)'] - x['CAGR(%)'] for x, y in zip(a, b)]
    same = [x['장치'] == y['장치'] for x, y in zip(a, b)]
    res = {'등급': {c: out[c]['등급'] for c in out}, 'R1': {c: out[c]['R1'] for c in out}, 'R2': {c: out[c]['R2'] for c in out},
           '2차: 시드별 CAGR 차이 e10−e1(%p)': [round(x, 3) for x in d], '중앙값': round(float(np.median(d)), 3),
           '양수 시드 수': int(sum(x > 0 for x in d)), '같은 장치 짝 수': int(sum(same)),
           '2차: e10 선택 epoch(검증 손실 최소 위치, 1부터)': [int(np.argmin(r['검증 손실 기록'])) + 1 for r in b],
           '2차: e10 실행 epoch 수(조기 종료 포함)': [len(r['검증 손실 기록']) for r in b]}
    (RUNS / 'judge_e.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))


def daily_panel(w):
    import pandas as pd
    px = pd.read_csv(window_csv(w), usecols=['date', 'tic', 'close'])
    px['date'] = px.date.str[:10]
    return px.pivot(index='date', columns='tic', values='close').sort_index()


def expand(df, px):
    # 스텝 → 일간 목표 행렬(헤더 O2). 반환: W (N+1, n), R (N+1, n), 확인용 무비용 스텝 성장 오차
    import numpy as np
    tics = list(px.columns); dates = list(px.index); pos = {d: j for j, d in enumerate(dates)}
    Wk = df[[f'w_{t}' for t in tics]].to_numpy(); Rk = df[[f'r_{t}' for t in tics]].to_numpy()
    start = [pos[d] for d in df.date]
    h = [0] * len(start)
    P = px.to_numpy()
    for k, j in enumerate(start):   # 기록한 h구간 수익 r_h와 종가로 구간 길이를 찾는다
        cand = [hh for hh in (1, 5, 20) if j + hh < len(P) and np.allclose(P[j + hh] / P[j] - 1, Rk[k], rtol=1e-6, atol=1e-9)]
        assert len(cand) >= 1, (k, df.date[k]); h[k] = cand[0]
    for k in range(len(start) - 1):
        assert start[k] + h[k] == start[k + 1], ('구간이 이어지지 않음', k)
    j0, j1 = start[0], start[-1] + h[-1]
    R = np.zeros((j1 - j0 + 1, len(tics))); R[1:] = P[j0 + 1:j1 + 1] / P[j0:j1] - 1
    W = np.zeros_like(R); hold = None; err = 0.0
    for k, j in enumerate(start):
        g = 1.0
        for dd in range(h[k]):
            row = j - j0 + 1 + dd
            wt = Wk[k] if dd == 0 else hold
            W[row] = wt; gr = 1 + float(wt @ R[row]); g *= gr
            hold = wt * (1 + R[row]) / gr
        err = max(err, abs(g - (1 + float(Wk[k] @ Rk[k]))))
    return W, R, err, h


def cmd_judge2():
    import numpy as np, pandas as pd
    sys.path.insert(0, str(HERE))
    from finrl_t3_run import u1_returns, baseline_weights, ann_log, block_boot_ci, sharpe_diff_p
    px = {w: daily_panel(w) for w in WINDOWS}
    seeds = {w: (range(10) if w == 'W0' else range(5)) for w in WINDOWS}
    need = {'W0': 8, 'W1': 4, 'W2': 4, 'W3': 4}
    conds = {'W0': 'abc', 'W1': 'ab', 'W2': 'ab', 'W3': 'ab'}
    from scipy.stats import t as tdist

    def classify(ds, k):
        return '우위' if sum(x > 0 for x in ds) >= k else ('열위' if sum(x < 0 for x in ds) >= k else '불확정')

    def target(cls):
        if cls['W0'] == '우위' and sum(v == '우위' for v in cls.values()) >= 3:
            return '유지'
        if cls['W0'] == '열위' or sum(v == '열위' for v in cls.values()) >= 2:
            return '소실'
        return '불확정'

    per = {}; checks = []
    for key, cond, ce in (('b@0.0001', 'b', 0.0001), ('a@0.0001', 'a', 0.0001), ('b@0.001', 'b', 0.001), ('c@0.001', 'c', 0.001)):
        per[key] = {}
        for w in WINDOWS:
            if cond not in conds[w]:
                continue
            ds, sens, ci, pv, o4, tv = [], [], [], [], [], []
            for s in seeds[w]:
                df, meta = load_run(w, cond, s)
                W, R, err, h = expand(df, px[w]); checks.append(err)
                net, taus = u1_returns(W, R, ce)
                base = {k: u1_returns(baseline_weights(R, k), R, ce)[0] for k in ('daily', 'monthly', 'bh')}
                ds.append((ann_log(net) - ann_log(base['daily'])) * 100)
                sens.append({k: round((ann_log(net) - ann_log(base[k])) * 100, 3) for k in ('monthly', 'bh')})
                sens[-1]['최댓값 기준선'] = round((ann_log(net) - max(ann_log(v) for v in base.values())) * 100, 3)
                x = np.log1p(net[1:]) - np.log1p(base['daily'][1:])
                ci.append([round(v * 100, 2) for v in block_boot_ci(x)])
                pv.append(round(sharpe_diff_p(net[1:], base['daily'][1:]), 4))
                tv.append(round(float(taus[2:][taus[2:] > 0].mean()) if (taus[2:] > 0).any() else 0.0, 4))
                if cond == 'a':
                    o4.append(round((252 / len(net) * np.log(df.pv.iloc[-1]) - ann_log(net)) * 100, 3))
            mult = (tdist.ppf(0.975, len(ds) - 1) + tdist.ppf(0.8, len(ds) - 1)) / np.sqrt(len(ds))
            per[key][w] = {'Δ(%p/년)': [round(x, 3) for x in ds], '분류': classify(ds, need[w]),
                           '시드 중앙값': round(float(np.median(ds)), 3), 'MDE80': round(float(mult * np.std(ds, ddof=1)), 3),
                           '민감도': sens, '부트스트랩 95% CI(%p/년)': ci, 'Sharpe 차이 p': pv,
                           'p<0.05 시드 수': int(sum(p < 0.05 for p in pv)), '리밸런싱일 평균 회전율': tv}
            if o4:
                per[key][w]['O4 원래env−U1(%p/년)'] = o4
        if all(w in per[key] for w in WINDOWS):
            cls = {w: per[key][w]['분류'] for w in WINDOWS}
            per[key]['대상 분류'] = target(cls)
            per[key]['차이 작음'] = all(abs(per[key][w]['시드 중앙값']) < 2 for w in WINDOWS)
    main = per['b@0.0001']
    res = {'주 판정(조건 b, c=0.0001, 매일 등가중)': {
        '창별': {w: {k: main[w][k] for k in ('Δ(%p/년)', '분류', '시드 중앙값')} for w in WINDOWS},
        '판정': main['대상 분류'], '차이 작음': main['차이 작음']},
        '2차': per, '점검: 일간 펼침 무비용 성장 − 코드 라벨 성장 최대 오차': float(max(checks))}
    (D / 'judge_o2.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res['주 판정(조건 b, c=0.0001, 매일 등가중)'], ensure_ascii=False, indent=1))


if __name__ == '__main__':
    cmd, *a = sys.argv[1:]
    {'run': lambda: cmd_run(a[0], a[1], int(a[2])), 'judge1': cmd_judge1, 'judge2': cmd_judge2, 'judge_e': cmd_judge_e}[cmd]()
