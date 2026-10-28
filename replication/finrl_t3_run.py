# T3 FinRL 포트폴리오 배분(Liu et al., ICAIF 2021) — O1 재현·O2 재평가·O5 동적 점검 실행기(로컬 맥 CPU).
# 사전 등록: notes/prereg_reeval_v3.md 3장(O1)·4장(O2)·5장(O5)·부록 A1, O5 정적 예측 notes/finrl_t3_o5_static.md.
# 판정 기준은 그 문서 그대로이고, 이 파일은 그 기준을 계산하는 방법을 실행 전에 고정한다.
#
# 사용:
#   python3 finrl_t3_run.py --fm <FinRL-Meta@286fef6 경로> train <algo> <seed> [<창> <조건>]   # 기본 W0 a
#   python3 finrl_t3_run.py --fm <경로> baselines                                           # O1: DJIA·Min-Var
#   python3 finrl_t3_run.py --fm <경로> o5                                                  # O5 동적 점검
#   python3 finrl_t3_run.py judge | judge2                                                  # O1 | O2 사전 판정
#
# 고정 사항 — O1(3aa1769에서 실행 전 커밋, 바꾸지 않음):
# - 데이터: data/snapshot.csv.gz (부록 A1 규칙 적용 28종목, 압축 해제 내용 md5 a4d0b008c5055781f5e518b108fc2532).
#   Colab 시간 측정 노트북이 Drive에 남긴 snapshot.csv는 A1 수정 전(2019-03-20부터 잘린) 데이터라 쓰지 않는다.
# - 기간: 학습 2009-01-01~2020-06-30(실효 2010-01-05부터), 거래 W0 = 2020-07-01~2021-06-30.
# - 하이퍼파라미터·timesteps: 튜토리얼(FinRL_PortfolioAllocation_NeurIPS_2020.py) 그대로.
# - 예측: 공식 DRLAgent.DRL_prediction(model.predict 기본값 deterministic=False). 재현성을 위해 예측 직전
#   np/torch 난수를 시드로 고정한다(결과 기록용, 동작 변경 아님).
# - torch 스레드 2개 고정(병렬 실행). 모델 파일은 디스크 여유가 없어 저장하지 않고, 매일 가중치·가치를 저장한다.
# - 연수익 = pyfolio/empyrical annual_return: (V_끝/V_처음)^(252/N) − 1, N = 일간 수익 행 수
#   (튜토리얼처럼 첫 행 0 포함). 샤프 = √252·평균/표준편차(ddof=1), 같은 일간 수익 열.
#   DJIA·Min-Var도 같은 거래일 행에 같은 정의를 쓴다.
# - DJIA: Yahoo ^DJI 종가(data/dji.csv, auto_adjust=False), 거래 창의 첫 거래일~마지막 거래일.
# - Min-Var: 튜토리얼 코드 그대로(직전 252일 수익 공분산, PyPortfolioOpt EfficientFrontier(None, Σ, (0, 0.1)),
#   min_volatility → clean_weights, 매일 재조정, 무비용).
#
# 고정 사항 — O2·O5(이 판, O2 학습 실행 전 커밋):
# - 창(v3 U3): W0 = 2020-07-01~2021-06-30, W1 = 2018-07-01~2019-06-30, W2 = 2019-07-01~2020-06-30.
#   학습은 항상 2009-01-01부터 창 시작 전날까지다. T3 절차(논문·튜토리얼)에는 검증 단계가 없고 학습 종료 모델을
#   쓰므로(v3 2.1), U3의 '직전 1년 검증'은 T3에서 쓰지 않는다. 이렇게 해야 W0 조건 (a)가 O1과 같은 절차가 된다.
#   W0 조건 (a)는 O1 실행 결과(o1/)를 그대로 쓴다.
# - 조건(v3 U6): (a) 원래 env로 학습, (b) U1 env c=0.001로 학습, (c) U1 env c=0.002로 학습. 하이퍼파라미터 동일.
# - U1 env(SPEU1): 원래 step과 같고 수익 계산만 참조 명세로 바꾼다. 현금 시작(직전 보유 w′=0, U2) →
#   τ_t = Σ|w_t − w′_t|, V_{t+1} = V_t·(1 − c·τ_t)·(1 + w_t·r_{t+1}), w′_{t+1} = w_t⊙(1+r_{t+1})/(1 + w_t·r_{t+1}).
#   보상은 원래처럼 새 가치 수준이다.
# - 평가: 정책이 무상태(관측 = 공분산 + 지표)라 예측 가중치는 env의 비용과 무관하다. 그래서 거래 창 예측은 원래 env로
#   한 번 하고, U1 수익은 저장한 가중치와 종가로 같은 식(u1_returns)으로 계산한다. u1_returns가 SPEU1 실행과 같은 값을
#   내는지는 o5에서 확인한다.
# - O2 지표: Δ = (252/N)·Σ log(1+순수익)(방법) − 같은 값(매일 등가중, 같은 U1 비용·현금 시작), N = 행 수(첫 행 0 포함).
#   주 판정은 조건 (b), c = 0.001. 창 분류: Δ>0 시드 ≥4/5 우위, Δ<0 시드 ≥4/5 열위, 그 밖 불확정.
#   대상(알고리즘) 분류: W0 우위이고 우위 창 ≥2/3 → 유지, W0 열위이거나 열위 창 ≥2(= ½ 이상) → 소실, 그 밖 불확정.
#   모든 창에서 시드 중앙값 |Δ| < 2%p/년이면 '차이 작음' 표지.
# - 2차(판정 아님): 조건 (a)·(c)의 같은 분류, (c)는 c=0.002 평가도 함께. 민감도 기준선: 매월(20거래일) 등가중,
#   등가중 buy-and-hold, 세 기준선 최댓값. O3: 창·조건별 Δ 시드 중앙값. O4: 조건 (a) 가중치를 원래 env와 U1 env로
#   평가한 연율 로그 성장 차이. 검출 가능 최소 효과: (t_{0.975,4} + t_{0.8,4})·sd(Δ)/√5.
#   보조 통계: 시드마다 일간 로그수익 차이의 원형 블록 부트스트랩(블록 20일, 2000회, 난수 0) 95% CI, 샤프 차이 검정은
#   Ledoit–Wolf(2008)의 HAC 델타법을 Bartlett 커널·대역폭 floor(4(T/100)^(2/9))로 단순화해 쓴다(원 논문의 사전백색화
#   QS 커널과 다름).
import sys, os, types, json, time, gzip, hashlib, argparse, pathlib

HERE = pathlib.Path(__file__).resolve().parent
D = HERE / 'finrl_t3'
SNAP_MD5 = 'a4d0b008c5055781f5e518b108fc2532'
W0 = ('2020-07-01', '2021-07-01')
TRAIN = ('2009-01-01', '2020-07-01')
WINDOWS = {'W0': W0, 'W1': ('2018-07-01', '2019-07-01'), 'W2': ('2019-07-01', '2020-07-01')}
COND_COST = {'a': None, 'b': 0.001, 'c': 0.002}
C_PAPER = 0.001
PARAMS = {'a2c': ({'n_steps': 5, 'ent_coef': 0.005, 'learning_rate': 0.0002}, 50000),
          'ppo': ({'n_steps': 2048, 'ent_coef': 0.005, 'learning_rate': 0.0001, 'batch_size': 128}, 80000),
          'ddpg': ({'batch_size': 128, 'buffer_size': 50000, 'learning_rate': 0.001}, 50000),
          'td3': ({'batch_size': 100, 'buffer_size': 1000000, 'learning_rate': 0.001}, 30000)}
SEEDS = [0, 1, 2, 3, 4]
# v3 3장 표
REPORTED = {'a2c': 42.57, 'ppo': 36.17, 'ddpg': 36.01, 'td3': 39.38}
TOL = {'a2c': 4.87, 'ppo': 1.67, 'ddpg': 1.59, 'td3': 3.27}


def setup_fm(fm):
    os.chdir(fm); sys.path.insert(0, fm)
    # 스냅샷을 쓰므로 다운로드 경로는 실행되지 않는다. 로컬 py3.9에서 import가 실패하는 모듈만 자리표시로 둔다.
    for m in ('pandas_market_calendars', 'talib'):
        try:
            __import__(m)
        except Exception:
            sys.modules[m] = types.ModuleType(m)


def load_data():
    import numpy as np, pandas as pd
    raw_bytes = gzip.decompress((D / 'data' / 'snapshot.csv.gz').read_bytes())
    assert hashlib.md5(raw_bytes).hexdigest() == SNAP_MD5, '스냅샷 해시 불일치'
    import io
    df = pd.read_csv(io.BytesIO(raw_bytes))
    # 이하 Colab 노트북(finrl_t3_timing.ipynb)과 같은 처리
    df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
    df = df.sort_values(['time', 'tic'], ignore_index=True)
    df.index = df.time.factorize()[0]
    cov_list, return_list, lookback = [], [], 252
    for i in range(lookback, len(df.index.unique())):
        data_lookback = df.loc[i - lookback:i, :]
        price_lookback = data_lookback.pivot_table(index='time', columns='tic', values='close').dropna(axis=1)
        return_lookback = price_lookback.pct_change().dropna()
        return_list.append(return_lookback); cov_list.append(return_lookback.cov().values)
    df_cov = pd.DataFrame({'time': df.time.unique()[lookback:], 'cov_list': cov_list, 'return_list': return_list})
    df = df.merge(df_cov, on='time').sort_values(['time', 'tic']).reset_index(drop=True)
    return df


def split(df, s, e):
    from meta.data_processor import DataProcessor
    return DataProcessor.data_split(None, df, s, e, target_date_col='time')


def env_kwargs(n):
    from meta import config
    return {'hmax': 100, 'initial_amount': 1000000, 'transaction_cost_pct': 0.001, 'state_space': n,
            'stock_dim': n, 'tech_indicator_list': config.INDICATORS, 'action_space': n, 'reward_scaling': 1e-4}


def make_spe():
    from meta.env_portfolio_allocation.env_portfolio_yahoofinance import StockPortfolioEnv

    class SPE(StockPortfolioEnv):
        # 이 커밋의 env는 gym 0.26 API인데 reset에 seed 인자가 없다 — 서명만 맞춘다(동작 동일)
        def reset(self, *, seed=None, options=None):
            return super().reset()
    return SPE


def make_spe_u1(c):
    import numpy as np
    SPE = make_spe()

    class SPEU1(SPE):
        # U1 참조 명세 비용(헤더 참조). 종료 분기·관측·행동 처리는 원래 step과 같다.
        def reset(self, *, seed=None, options=None):
            out = super().reset()
            self.hold = np.zeros(self.stock_dim)   # U2: 현금 시작
            return out

        def step(self, actions):
            if self.time_index >= len(self.sorted_times) - 1:
                return super().step(actions)
            self.terminal = False
            if np.sum(actions) == 1 and np.min(actions) >= 0:
                weights = actions
            else:
                weights = self.softmax_normalization(actions)
            self.actions_memory.append(weights)
            last_day_memory = self.data
            self.time_index += 1
            day = self.sorted_times[self.time_index]
            self.state, self.info = self.get_state_and_info_from_day(day)
            r = self.data.close.values / last_day_memory.close.values - 1
            w = np.asarray(weights, dtype=float)
            tau = float(np.abs(w - self.hold).sum())
            g = 1 + float(np.dot(r, w))
            portfolio_return = (1 - c * tau) * g - 1
            self.hold = w * (1 + r) / g
            new_portfolio_value = self.portfolio_value * (1 + portfolio_return)
            self.portfolio_value = new_portfolio_value
            self.portfolio_return_memory.append(portfolio_return)
            self.date_memory.append(day)
            self.asset_memory.append(new_portfolio_value)
            self.reward = new_portfolio_value
            return self.state, self.reward, self.terminal, False, self.info
    SPEU1.u1_c = c
    return SPEU1


def u1_returns(W, R, c):
    # W: (N, n) 행 j(≥1)는 날짜 j−1에 정한 가중치(날짜 j−1→j 수익에 적용), 행 0은 미사용. R: (N, n) 행 j = close_j/close_{j−1} − 1.
    # 반환: 길이 N 순수익(첫 행 0), 회전율. 현금 시작.
    import numpy as np
    N, n = W.shape
    hold = np.zeros(n); out = np.zeros(N); taus = np.zeros(N)
    for j in range(1, N):
        w = W[j]; tau = np.abs(w - hold).sum(); g = 1 + float(w @ R[j])
        out[j] = (1 - c * tau) * g - 1; taus[j] = tau
        hold = w * (1 + R[j]) / g
    return out, taus


def baseline_weights(R, kind):
    # 매일 등가중 / 매월(20거래일) 등가중 / 등가중 buy-and-hold. 재조정하지 않는 날은 드리프트 보유를 그대로 목표로 둔다(τ=0).
    import numpy as np
    N, n = R.shape
    W = np.zeros((N, n)); ew = np.full(n, 1 / n); hold = None
    for j in range(1, N):
        if kind == 'daily' or hold is None or (kind == 'monthly' and (j - 1) % 20 == 0):
            w = ew
        else:
            w = hold
        W[j] = w; hold = w * (1 + R[j]) / (1 + float(w @ R[j]))
    return W


def ann_return(r):
    import numpy as np
    r = np.asarray(r, dtype=float)
    return float(np.prod(1 + r) ** (252 / len(r)) - 1)


def ann_log(r):
    import numpy as np
    r = np.asarray(r, dtype=float)
    return float(252 / len(r) * np.log1p(r).sum())


def sharpe(r):
    import numpy as np
    r = np.asarray(r, dtype=float)
    return float(np.sqrt(252) * r.mean() / r.std(ddof=1))


def out_path(algo, seed, win, cond):
    if win == 'W0' and cond == 'a':
        return D / 'o1' / f'{algo}_W0_a_s{seed}.csv'
    return D / 'o2' / f'{algo}_{win}_{cond}_s{seed}.csv'


def cmd_train(algo, seed, win='W0', cond='a'):
    import numpy as np, pandas as pd, torch, random, contextlib, io
    torch.set_num_threads(2)
    from meta import config
    from agents.stablebaselines3_models import DRLAgent
    for d in [config.DATA_SAVE_DIR, config.TRAINED_MODEL_DIR, config.TENSORBOARD_LOG_DIR, config.RESULTS_DIR]:
        os.makedirs(d, exist_ok=True)
    out = out_path(algo, seed, win, cond)
    if out.exists():
        print('이미 있음', out); return
    df = load_data(); SPE = make_spe()
    TrainEnv = SPE if COND_COST[cond] is None else make_spe_u1(COND_COST[cond])
    train, trade = split(df, TRAIN[0], WINDOWS[win][0]), split(df, *WINDOWS[win])
    n = len(train.tic.unique()); kw = env_kwargs(n)
    assert n == 28 and n == len(trade.tic.unique())
    p, steps = PARAMS[algo]
    env_train, _ = TrainEnv(df=train.copy(), **kw).get_sb_env()
    agent = DRLAgent(env=env_train)
    with contextlib.redirect_stdout(io.StringIO()):
        model = agent.get_model(algo, model_kwargs=dict(p), seed=seed, verbose=0)
    t0 = time.time()
    model = agent.train_model(model=model, tb_log_name=f'{algo}_s{seed}', total_timesteps=steps)
    mins = (time.time() - t0) / 60
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):
        acc, acts = DRLAgent.DRL_prediction(model=model, environment=SPE(df=trade.copy(), **kw))
    assert len(acc) == trade.index.nunique() == len(acts)
    res = acts.copy(); res.columns = [f'w_{c}' for c in res.columns]
    res.insert(0, 'daily_return', acc['daily_return'].values)
    res.index.name = 'date'
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out, float_format='%.10g')
    meta = out.parent / 'train_minutes.json'
    m = json.loads(meta.read_text()) if meta.exists() else {}
    m[out.stem if out.parent.name == 'o2' else f'{algo}_s{seed}'] = round(mins, 2)
    meta.write_text(json.dumps(m, indent=1, sort_keys=True))
    print(f'{algo} {win} {cond} seed {seed}: 학습 {mins:.1f}분, 저장 {out.name}')


def cmd_baselines():
    import numpy as np, pandas as pd
    from pypfopt.efficient_frontier import EfficientFrontier
    out = D / 'o1' / 'baselines_W0.csv'
    df = load_data(); trade = split(df, *W0)
    dates = list(trade.time.unique())
    # Min-Var — 튜토리얼 코드 그대로(열 이름 date → time)
    portfolio = pd.DataFrame(index=range(1), columns=dates)
    portfolio.loc[0, dates[0]] = 1000000
    for i in range(len(dates) - 1):
        df_temp = df[df.time == dates[i]].reset_index(drop=True)
        df_temp_next = df[df.time == dates[i + 1]].reset_index(drop=True)
        Sigma = df_temp.return_list[0].cov()
        ef_min_var = EfficientFrontier(None, Sigma, weight_bounds=(0, 0.1))
        ef_min_var.min_volatility()
        cleaned = ef_min_var.clean_weights()
        cap = portfolio.iloc[0, i]
        current_cash = [w * cap for w in list(cleaned.values())]
        current_shares = list(np.array(current_cash) / np.array(df_temp.close))
        portfolio.iloc[0, i + 1] = np.dot(current_shares, np.array(df_temp_next.close))
    mv = portfolio.T.iloc[:, 0].astype(float)
    dji = pd.read_csv(D / 'data' / 'dji.csv', index_col='date')['close'].reindex(dates)
    assert dji.notna().all(), 'DJIA 날짜 누락'
    res = pd.DataFrame({'minvar_return': mv.pct_change().fillna(0).values,
                        'dji_return': dji.pct_change().fillna(0).values}, index=pd.Index(dates, name='date'))
    res.to_csv(out, float_format='%.10g'); print('저장', out)


def window_returns(win):
    # 거래 창 종가로 만든 일간 수익 행렬(행 0 = 0). 종목 순서는 env와 같은 알파벳순.
    import numpy as np, pandas as pd
    p = D / 'o2' / f'returns_{win}.csv'
    return pd.read_csv(p, index_col='date')


def cmd_prepare_returns():
    import pandas as pd
    df = load_data()
    (D / 'o2').mkdir(parents=True, exist_ok=True)
    for win, (s, e) in WINDOWS.items():
        tr = split(df, s, e)
        px = tr.pivot_table(index='time', columns='tic', values='close').sort_index()
        R = px.pct_change().fillna(0); R.index.name = 'date'
        R.to_csv(D / 'o2' / f'returns_{win}.csv', float_format='%.12g')
        print(win, R.index[0], R.index[-1], R.shape)


def cmd_o5():
    import numpy as np, pandas as pd
    df = load_data(); SPE = make_spe()
    trade = split(df, *W0)
    n = trade.tic.nunique(); kw = env_kwargs(n)
    K = 30   # 주입 스텝 수
    ew = np.full(n, 1 / n)
    A = np.zeros(n); A[:n // 2] = 1 / (n // 2)
    B = np.zeros(n); B[n // 2:] = 1 / (n - n // 2)
    cases = {'①등가중 유지': [ew] * K, '②A·B 교대': [A if k % 2 == 0 else B for k in range(K)], '③현금에서 첫 3스텝': [ew] * 3}

    def run(Env, acts, c):
        e = Env(df=trade.copy(), **dict(kw, transaction_cost_pct=c)); e.reset()
        rew = []
        for a in acts:
            with np.errstate(divide='ignore'):   # v2 3장: softmax env에는 logits = log w (softmax(log w) = w)
                _, r, *_ = e.step(np.log(np.asarray(a, dtype=np.float64)))
            rew.append(r)
        used = np.vstack([np.zeros(n)] + [np.asarray(x, dtype=float) for x in e.actions_memory[1:]])
        return np.array(rew), np.array(e.portfolio_return_memory[1:]), np.array(e.asset_memory[1:]), used

    R = window_returns('W0').to_numpy()
    out = {}
    for name, acts in cases.items():
        k = len(acts)
        W = run(SPE, acts, 0.0)[3]; Rk = R[:k + 1]   # env가 실제로 쓴 가중치
        inj_err = float(np.max(np.abs(W[1:] - np.vstack(acts))))
        ref_net, taus = u1_returns(W, Rk, C_PAPER)
        gross, _ = u1_returns(W, Rk, 0.0)
        ref_cost = 1 - (1 + ref_net[1:]) / (1 + gross[1:])          # 참조 비용(가치 비율)
        rec = {}
        for label, Env in (('원래 env', SPE), ('U1 env', make_spe_u1(C_PAPER))):
            if label == 'U1 env':
                rw1, rt1, v1, _ = run(Env, acts, C_PAPER); rw0, rt0, v0, _ = run(make_spe_u1(0.0), acts, 0.0)
            else:
                rw0, rt0, v0, _ = run(Env, acts, 0.0); rw1, rt1, v1, _ = run(Env, acts, C_PAPER)
            meas = 1 - (1 + rt1) / (1 + rt0)
            rec[label] = {
                'C1 보상열 c=0과 다름': bool(not np.allclose(rw0, rw1, rtol=0, atol=0)),
                'C1 수익열 c=0과 다름': bool(not np.allclose(rt0, rt1, rtol=0, atol=0)),
                'C2 보상=가치(상대오차 최대)': float(np.max(np.abs(rw1 - v1) / v1)),
                'S1 측정/참조 비용 비율': float(meas.sum() / ref_cost.sum()),
                '측정 비용 첫 3스텝(bp)': [round(x * 1e4, 3) for x in meas[:3]],
                '참조 비용 첫 3스텝(bp)': [round(x * 1e4, 3) for x in ref_cost[:3]],
                'u1_returns와 최대 차이': float(np.max(np.abs(rt1 - ref_net[1:]))) if label == 'U1 env' else None}
        rec['주입 가중치 오차(최대)'] = inj_err
        rec['참조 회전율 첫 3스텝'] = [round(float(t), 4) for t in taus[1:4]]
        out[name] = rec
    e = SPE(df=trade.copy(), **kw); e.reset()
    out['C3'] = {'reset 직후 actions_memory[0]': '1/n 등가중(비용·수익 계산에 쓰이지 않음)',
                 '관측 shape': list(np.asarray(e.state).shape), '관측에 직전 보유 포함': False}
    (D / 'o2').mkdir(parents=True, exist_ok=True)
    (D / 'o2' / 'o5_result.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_judge():
    import numpy as np, pandas as pd
    b = pd.read_csv(D / 'o1' / 'baselines_W0.csv', index_col='date')
    dji, mv = ann_return(b.dji_return) * 100, ann_return(b.minvar_return) * 100
    rows, grades = [], {}
    for algo in PARAMS:
        ar, sr = [], []
        for s in SEEDS:
            r = pd.read_csv(D / 'o1' / f'{algo}_W0_a_s{s}.csv', index_col='date')
            assert list(r.index) == list(b.index)
            ar.append(ann_return(r.daily_return) * 100); sr.append(sharpe(r.daily_return))
        med = float(np.median(ar))
        r1 = abs(med - REPORTED[algo]) <= TOL[algo]
        beat = sum(a > dji and a > mv for a in ar)
        r2 = beat >= 4
        g = '재현' if r1 and r2 else ('부분 재현' if r1 or r2 else '미재현')
        grades[algo] = g
        rows.append({'algo': algo, 'seed별 연수익(%)': [round(a, 2) for a in ar], '중앙값': round(med, 2),
                     '보고값': REPORTED[algo], '허용폭': TOL[algo], 'R1': r1, 'DJIA·MinVar 모두 이긴 시드': beat,
                     'R2': r2, '등급': g, 'seed별 샤프': [round(x, 2) for x in sr]})
    n_rep = sum(g == '재현' for g in grades.values())
    lineage = '재현' if n_rep >= 3 else ('부분 재현' if n_rep >= 1 else '미재현')
    out = {'DJIA 연수익(%)': round(dji, 2), 'DJIA 샤프': round(sharpe(b.dji_return), 2),
           'Min-Var 연수익(%)': round(mv, 2), 'Min-Var 샤프': round(sharpe(b.minvar_return), 2),
           '알고리즘': rows, '계보 판정': lineage, '재현 알고리즘 수': n_rep,
           'O2 대상(재현·부분 재현)': [a for a, g in grades.items() if g != '미재현']}
    (D / 'o1' / 'judge_W0.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


def block_boot_ci(x, B=2000, L=20, seed=0):
    import numpy as np
    rng = np.random.default_rng(seed); T = len(x); nb = int(np.ceil(T / L)); stats = np.empty(B)
    for b in range(B):
        st = rng.integers(0, T, nb)
        idx = (st[:, None] + np.arange(L)[None, :]).ravel()[:T] % T
        stats[b] = x[idx].mean() * 252
    return [float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))]


def sharpe_diff_p(r1, r2):
    # Ledoit–Wolf(2008) HAC 델타법(Bartlett 커널로 단순화)
    import numpy as np
    from scipy.stats import norm
    T = len(r1)
    m1, m2 = r1.mean(), r2.mean(); g1, g2 = (r1 ** 2).mean(), (r2 ** 2).mean()
    d = m1 / np.sqrt(g1 - m1 ** 2) - m2 / np.sqrt(g2 - m2 ** 2)
    V = np.column_stack([r1 - m1, r2 - m2, r1 ** 2 - g1, r2 ** 2 - g2])
    lag = int(np.floor(4 * (T / 100) ** (2 / 9)))
    Psi = V.T @ V / T
    for k in range(1, lag + 1):
        G = V[k:].T @ V[:-k] / T; Psi += (1 - k / (lag + 1)) * (G + G.T)
    grad = np.array([g1 / (g1 - m1 ** 2) ** 1.5, -g2 / (g2 - m2 ** 2) ** 1.5,
                     -0.5 * m1 / (g1 - m1 ** 2) ** 1.5, 0.5 * m2 / (g2 - m2 ** 2) ** 1.5])
    se = np.sqrt(grad @ Psi @ grad / T)
    return float(2 * (1 - norm.cdf(abs(d) / se)))


def cmd_judge2():
    import numpy as np, pandas as pd
    from scipy.stats import t as tdist
    RW = {w: window_returns(w) for w in WINDOWS}
    tics = list(RW['W0'].columns)
    base = {}
    for w, R in RW.items():
        Rn = R.to_numpy()
        for c in (C_PAPER, 0.002):
            for kind in ('daily', 'monthly', 'bh'):
                base[(w, c, kind)], _ = u1_returns(baseline_weights(Rn, kind), Rn, c)

    def load_w(algo, s, w, cond):
        r = pd.read_csv(out_path(algo, s, w, cond), index_col='date')
        assert list(r.index) == list(RW[w].index)
        Wm = r[[f'w_{t}' for t in tics]].to_numpy()
        return r, Wm

    def classify(deltas):
        pos, neg = sum(x > 0 for x in deltas), sum(x < 0 for x in deltas)
        return '우위' if pos >= 4 else ('열위' if neg >= 4 else '불확정')

    def target_class(cls):
        if cls['W0'] == '우위' and sum(v == '우위' for v in cls.values()) >= 2:
            return '유지'
        if cls['W0'] == '열위' or sum(v == '열위' for v in cls.values()) >= 2:
            return '소실'
        return '불확정'

    mult = (tdist.ppf(0.975, 4) + tdist.ppf(0.8, 4)) / np.sqrt(5)
    res = {'주 판정(조건 b, c=0.001, 매일 등가중)': {}, '2차': {}}
    for algo in PARAMS:
        per = {}
        for cond in ('a', 'b', 'c'):
            for c_eval in ((C_PAPER,) if cond != 'c' else (C_PAPER, 0.002)):
                key = f'{cond}@{c_eval}'
                per[key] = {}
                for w in WINDOWS:
                    Rn = RW[w].to_numpy(); ds, sens, ci, pv, o4 = [], [], [], [], []
                    for s in SEEDS:
                        r, Wm = load_w(algo, s, w, cond)
                        net, taus = u1_returns(Wm, Rn, c_eval)
                        ds.append((ann_log(net) - ann_log(base[(w, c_eval, 'daily')])) * 100)
                        sens.append({k: round((ann_log(net) - ann_log(base[(w, c_eval, k)])) * 100, 3) for k in ('monthly', 'bh')})
                        best = max(ann_log(base[(w, c_eval, k)]) for k in ('daily', 'monthly', 'bh'))
                        sens[-1]['최댓값 기준선'] = round((ann_log(net) - best) * 100, 3)
                        x = np.log1p(net[1:]) - np.log1p(base[(w, c_eval, 'daily')][1:])
                        ci.append([round(v * 100, 2) for v in block_boot_ci(x)])
                        pv.append(round(sharpe_diff_p(net[1:], base[(w, c_eval, 'daily')][1:]), 4))
                        if cond == 'a':
                            o4.append(round((ann_log(r.daily_return.values) - ann_log(net)) * 100, 3))
                        sens[-1]['평균 회전율'] = round(float(taus[2:].mean()), 4)
                    per[key][w] = {'Δ(%p/년)': [round(x, 3) for x in ds], '분류': classify(ds),
                                   '시드 중앙값': round(float(np.median(ds)), 3), 'MDE80': round(float(mult * np.std(ds, ddof=1)), 3),
                                   '민감도': sens, '부트스트랩 95% CI(%p/년)': ci,
                                   'Sharpe 차이 p': pv, 'p<0.05 시드 수': int(sum(p < 0.05 for p in pv))}
                    if cond == 'a':
                        per[key][w]['O4 원래env−U1(%p/년)'] = o4
                cls = {w: per[key][w]['분류'] for w in WINDOWS}
                per[key]['대상 분류'] = target_class(cls)
                per[key]['차이 작음'] = all(abs(per[key][w]['시드 중앙값']) < 2 for w in WINDOWS)
        main = per[f'b@{C_PAPER}']
        res['주 판정(조건 b, c=0.001, 매일 등가중)'][algo] = {
            '창별': {w: {k: main[w][k] for k in ('Δ(%p/년)', '분류', '시드 중앙값')} for w in WINDOWS},
            '판정': main['대상 분류'], '차이 작음': main['차이 작음']}
        res['2차'][algo] = per
    summ = {a: v['판정'] for a, v in res['주 판정(조건 b, c=0.001, 매일 등가중)'].items()}
    res['집계'] = {'O2 대상 수': len(summ), '유지': sum(v == '유지' for v in summ.values()),
                 '소실': sum(v == '소실' for v in summ.values()), '불확정': sum(v == '불확정' for v in summ.values())}
    res['기준선 연율 로그 성장(%/년, c=0.001)'] = {w: {k: round(ann_log(base[(w, C_PAPER, k)]) * 100, 3)
                                               for k in ('daily', 'monthly', 'bh')} for w in WINDOWS}
    (D / 'o2' / 'judge_o2.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: res[k] for k in ('주 판정(조건 b, c=0.001, 매일 등가중)', '집계', '기준선 연율 로그 성장(%/년, c=0.001)')},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fm')
    ap.add_argument('cmd'); ap.add_argument('args', nargs='*')
    a = ap.parse_args()
    if a.cmd not in ('judge', 'judge2'):
        setup_fm(a.fm)
    {'train': lambda: cmd_train(a.args[0], int(a.args[1]), *a.args[2:4]), 'baselines': cmd_baselines,
     'returns': cmd_prepare_returns, 'o5': cmd_o5, 'judge': cmd_judge, 'judge2': cmd_judge2}[a.cmd]()
