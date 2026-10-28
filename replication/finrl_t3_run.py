# T3 FinRL 포트폴리오 배분(Liu et al., ICAIF 2021) — O1 재현 실행기(로컬 맥 CPU).
# 사전 등록: notes/prereg_reeval_v3.md 3장(R1·R2·등급)과 부록 A1. 판정 기준은 그 문서 그대로이고,
# 이 파일은 그 기준을 계산하는 방법(연수익·샤프·기준선 정의)을 실행 전에 고정한다.
#
# 사용:
#   python3 finrl_t3_run.py --fm <FinRL-Meta@286fef6 경로> train <algo> <seed>   # W0, 조건 (a)
#   python3 finrl_t3_run.py --fm <경로> baselines                                 # DJIA·Min-Var
#   python3 finrl_t3_run.py judge                                                 # 사전 판정
#
# 고정 사항(실행 전 커밋):
# - 데이터: data/snapshot.csv.gz (부록 A1 규칙 적용 28종목, 압축 해제 내용 md5 a4d0b008c5055781f5e518b108fc2532).
#   Colab 시간 측정 노트북이 Drive에 남긴 snapshot.csv는 A1 수정 전(2019-03-20부터 잘린) 데이터라 쓰지 않는다.
# - 기간: 학습 2009-01-01~2020-06-30(실효 2010-01-05부터), 거래 W0 = 2020-07-01~2021-06-30.
# - 하이퍼파라미터·timesteps: 튜토리얼(FinRL_PortfolioAllocation_NeurIPS_2020.py) 그대로.
# - 예측: 공식 DRLAgent.DRL_prediction(model.predict 기본값 deterministic=False). 재현성을 위해 예측 직전
#   np/torch 난수를 시드로 고정한다(결과 기록용, 동작 변경 아님).
# - torch 스레드 2개 고정(병렬 실행). 모델 파일은 디스크 여유가 없어 저장하지 않고, 매일 가중치·가치를 저장한다
#   (정책이 무상태라 O4의 비용 구현 비교는 저장된 가중치로 계산할 수 있다).
# - 연수익 = pyfolio/empyrical annual_return: (V_끝/V_처음)^(252/N) − 1, N = 일간 수익 행 수
#   (튜토리얼처럼 첫 행 0 포함). 샤프 = √252·평균/표준편차(ddof=1), 같은 일간 수익 열.
#   DJIA·Min-Var도 같은 거래일 행에 같은 정의를 쓴다.
# - DJIA: Yahoo ^DJI 종가(data/dji.csv, auto_adjust=False), 거래 창의 첫 거래일~마지막 거래일.
# - Min-Var: 튜토리얼 코드 그대로(직전 252일 수익 공분산, PyPortfolioOpt EfficientFrontier(None, Σ, (0, 0.1)),
#   min_volatility → clean_weights, 매일 재조정, 무비용).
import sys, os, types, json, time, gzip, hashlib, argparse, pathlib

HERE = pathlib.Path(__file__).resolve().parent
D = HERE / 'finrl_t3'
SNAP_MD5 = 'a4d0b008c5055781f5e518b108fc2532'
W0 = ('2020-07-01', '2021-07-01')
TRAIN = ('2009-01-01', '2020-07-01')
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


def ann_return(r):
    import numpy as np
    r = np.asarray(r, dtype=float)
    return float(np.prod(1 + r) ** (252 / len(r)) - 1)


def sharpe(r):
    import numpy as np
    r = np.asarray(r, dtype=float)
    return float(np.sqrt(252) * r.mean() / r.std(ddof=1))


def cmd_train(algo, seed):
    import numpy as np, pandas as pd, torch, random, contextlib, io
    torch.set_num_threads(2)
    from meta import config
    from agents.stablebaselines3_models import DRLAgent
    for d in [config.DATA_SAVE_DIR, config.TRAINED_MODEL_DIR, config.TENSORBOARD_LOG_DIR, config.RESULTS_DIR]:
        os.makedirs(d, exist_ok=True)
    out = D / 'o1' / f'{algo}_W0_a_s{seed}.csv'
    if out.exists():
        print('이미 있음', out); return
    df = load_data(); SPE = make_spe()
    train, trade = split(df, *TRAIN), split(df, *W0)
    n = len(train.tic.unique()); kw = env_kwargs(n)
    assert n == 28 and n == len(trade.tic.unique())
    p, steps = PARAMS[algo]
    env_train, _ = SPE(df=train.copy(), **kw).get_sb_env()
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
    (D / 'o1').mkdir(parents=True, exist_ok=True)
    res.to_csv(out, float_format='%.10g')
    meta = D / 'o1' / 'train_minutes.json'
    m = json.loads(meta.read_text()) if meta.exists() else {}
    m[f'{algo}_s{seed}'] = round(mins, 2); meta.write_text(json.dumps(m, indent=1, sort_keys=True))
    print(f'{algo} seed {seed}: 학습 {mins:.1f}분, 저장 {out.name}')


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


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fm')
    ap.add_argument('cmd'); ap.add_argument('args', nargs='*')
    a = ap.parse_args()
    if a.cmd != 'judge':
        setup_fm(a.fm)
    {'train': lambda: cmd_train(a.args[0], int(a.args[1])), 'baselines': cmd_baselines, 'judge': cmd_judge}[a.cmd]()
