# -*- coding: utf-8 -*-
# 사전 등록 notes/prereg_stat_power_v2.md §1 입력 준비. 통계량은 계산하지 않고 일별 순수익만 쓴다.
#   python3 prep.py fd                      # 맥: F(FinRL O2 조건 b, c=0.001), D·D'(DeepAries W0, c=0.0001)
#   python3 prep.py e <ensemble_f7 폴더> <run 폴더(data/dow_30_2009_2020.csv, data/^DJI.csv 포함)>   # 서버: E
# 출력: inputs/F_{W}.csv, inputs/D.csv, inputs/Dp.csv, inputs/E.csv  (열: date, base, <정책 열...>)
# 모든 파일은 판정 코드와 같은 함수(finrl_t3_run.u1_returns·baseline_weights, deeparies_run.expand)를 쓴다.
import sys, csv, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPL = HERE.parent
OUT = HERE / 'inputs'
ALGOS = ('a2c', 'ppo', 'ddpg', 'td3')
SEEDS = range(5)


def write(path, dates, cols):
    # cols: dict 이름 -> 길이 len(dates) 배열. 첫 열 base.
    OUT.mkdir(exist_ok=True)
    names = list(cols)
    with open(path, 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['date'] + names)
        for i, d in enumerate(dates):
            w.writerow([d] + [repr(float(cols[n][i])) for n in names])


def prep_fd():
    import numpy as np, pandas as pd
    sys.path.insert(0, str(REPL))
    import finrl_t3_run as F
    for w in F.WINDOWS:
        RW = F.window_returns(w); tics = list(RW.columns); Rn = RW.to_numpy()
        base, _ = F.u1_returns(F.baseline_weights(Rn, 'daily'), Rn, F.C_PAPER)
        cols = {'base': base[1:]}
        for a in ALGOS:
            for s in SEEDS:
                r = pd.read_csv(F.D / 'o2' / f'{a}_{w}_b_s{s}.csv', index_col='date')
                assert list(r.index) == list(RW.index)
                net, _ = F.u1_returns(r[[f'w_{t}' for t in tics]].to_numpy(), Rn, F.C_PAPER)
                cols[f'{a}_s{s}'] = net[1:]   # 행 0(현금 시작 자리, 수익 0)은 뺀다
        write(OUT / f'F_{w}.csv', list(RW.index[1:]), cols)

    import deeparies_run as DA
    px = DA.daily_panel('W0'); dates = list(px.index); pos = {d: j for j, d in enumerate(dates)}
    import pandas as pd
    for tag, folder, cond in (('D', 'runs', 'a'), ('Dp', 'e10', 'e10')):
        per = {}
        for s in range(10):
            df = pd.read_csv(DA.D / folder / f'W0_{cond}_s{s}.csv')
            W, R, err, h = DA.expand(df, px)
            assert err < 1e-6, (tag, s, err)
            j0 = pos[df.date.iloc[0]]
            net, _ = F.u1_returns(W, R, DA.C_PAPER)
            per[s] = {dates[j0 + k]: net[k] for k in range(1, len(net))}   # 행 k = dates[j0+k] 종가 기준 수익
        common = sorted(set.intersection(*[set(v) for v in per.values()]))
        # 교집합은 연속 구간이어야 한다(각 시드 범위가 연속이므로)
        idx = [pos[d] for d in common]; assert idx == list(range(idx[0], idx[-1] + 1))
        j0, j1 = idx[0] - 1, idx[-1]
        P = px.to_numpy(); R = np.zeros((j1 - j0 + 1, P.shape[1])); R[1:] = P[j0 + 1:j1 + 1] / P[j0:j1] - 1
        assert np.isfinite(R).all()
        base, _ = F.u1_returns(F.baseline_weights(R, 'daily'), R, DA.C_PAPER)
        cols = {'base': base[1:]}
        for s in range(10):
            cols[f's{s}'] = np.array([per[s][d] for d in common])
        write(OUT / f'{tag}.csv', common, cols)
        print(tag, '교집합 일수', len(common), common[0], common[-1])


def prep_e(ens_dir, run_dir):
    # Ensemble F7: 파일 i의 행 k = unique_trade_date[i-63+k] 종가 시점 계좌 가치(run_DRL.py 25행, models.py 77행).
    # 저자 backtesting.ipynb·판정 스크립트와 같이 이어 붙인 뒤 앞 1,097행을 쓴다(창 경계의 수익 0 행 포함).
    ens_dir, run_dir = pathlib.Path(ens_dir), pathlib.Path(run_dir)
    ITERS = list(range(126, 1198, 63)); ROWS = 1097
    with open(run_dir / 'data' / 'dow_30_2009_2020.csv') as fh:
        dd = sorted({int(r['datadate']) for r in csv.DictReader(fh)})
    utd = [d for d in dd if 20151001 < d <= 20200707]
    with open(run_dir / 'data' / '^DJI.csv') as fh:
        dji = {r['Date'].replace('-', ''): float(r['Adj Close']) for r in csv.DictReader(fh) if r['Adj Close'] not in ('null', '')}
    runs = {}
    for k in range(1, 6):
        rd = ens_dir / f'E{k}'
        assert json.loads((rd / 'done.json').read_text())['status'] == 'ok'
        vals, ds = [], []
        for i in ITERS:
            with open(rd / 'account_value' / f'account_value_trade_ensemble_{i}.csv') as fh:
                rows = list(csv.DictReader(fh))
            assert len(rows) == 63
            vals += [float(x['0']) for x in rows]; ds += [utd[i - 63 + j] for j in range(63)]
        runs[k] = (vals[:ROWS], ds[:ROWS])
    dates = runs[1][1]
    assert all(runs[k][1] == dates for k in runs) and len(set(dates)) == ROWS
    assert all(str(d) in dji for d in dates), [d for d in dates if str(d) not in dji][:5]
    # 창 경계(행 63·j, j ≥ 1): env reset이 첫 행 가치를 직전 날 가격으로 매기므로(EnvMultipleStock_trade.py 222–224행)
    # E 수익은 경계일 0, 다음 날 2거래일치다. ^DJI도 같게 맞춘다(경계일 0, 다음 날 2일 복리). 저자 집계 Sharpe는 바꾸지 않는다.
    px = [dji[str(d)] for d in dates]
    bnd = {63 * j for j in range(1, ROWS // 63 + 1) if 63 * j < ROWS}
    base = []
    for t in range(1, ROWS):
        if t in bnd:
            base.append(0.0)
        elif t - 1 in bnd:
            base.append(px[t] / px[t - 2] - 1)
        else:
            base.append(px[t] / px[t - 1] - 1)
    cols = {'base': base}
    for k in runs:
        v = runs[k][0]; cols[f'E{k}'] = [v[t] / v[t - 1] - 1 for t in range(1, ROWS)]
    write(OUT / 'E.csv', [f'{str(d)[:4]}-{str(d)[4:6]}-{str(d)[6:]}' for d in dates[1:]], cols)
    print('E 일수', ROWS - 1, dates[0], dates[-1], '경계 행', len(bnd))
    zero = [t for t in range(1, ROWS) if all(cols[f'E{k}'][t - 1] == 0.0 for k in runs)]
    assert bnd <= set(zero), sorted(bnd - set(zero))   # 경계 행은 모두 수익 0(현금 보유일도 0이므로 포함 관계만 본다)
    print('경계 행 수익 0 확인')


if __name__ == '__main__':
    if sys.argv[1] == 'fd':
        prep_fd()
    else:
        prep_e(sys.argv[2], sys.argv[3])
