"""자산 수 절제 실험 노트북 생성기.

사용: python crypto/notebooks/retrain1006/_build_asset_scaling.py
원본 노트북 셀은 rt1006 재학습과 같은 커밋(0e86a41)에서 불러온다 — 환경·하이퍼파라미터가 재학습과 동일.
"""
import json
from pathlib import Path

SHA = '0e86a41a701841d9a17398a8cebf240cd0c40218'
OUT = Path('crypto/notebooks/retrain1006/crypto_asset_scaling_rt1006.ipynb')
MAIN = 'crypto/notebooks/crypto_hrl_earnhft_colab.ipynb'


def code(s): return {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': s}
def md(s): return {'cell_type': 'markdown', 'metadata': {}, 'source': s}


# 거래대금 순위(universe.csv, 수집 시점) — 'BTC/USDT' → 'BTCUSDT'
VOLUME_ORDER = [l.strip().replace('/', '') for l in
                open('crypto/data/universe.csv').read().splitlines()[1:] if l.strip()]

MOUNT = "from google.colab import drive\ndrive.mount('/content/drive')\n!pip install -q stable-baselines3[extra] gymnasium h5py pyarrow\n"

RUNNER = f'''# 실행기 — GitHub의 원본 노트북(커밋 {SHA[:7]} 고정, rt1006 재학습과 같은 코드)에서 셀을 불러와 실행한다.
import json, urllib.request
from pathlib import Path
COMMIT = '{SHA}'
RAW = f'https://raw.githubusercontent.com/winbean-kwon/ToBeRich/{{COMMIT}}/'
TAG = 'rt1006'
_ip = get_ipython()

def fetch_cells(path):
    nb = json.loads(urllib.request.urlopen(RAW + path).read().decode('utf-8'))
    return {{i: (c['source'] if isinstance(c['source'], str) else ''.join(c['source']))
            for i, c in enumerate(nb['cells']) if c['cell_type'] == 'code'}}

PATCH = r"""
MODEL_DIR = DRIVE_ROOT / 'models' / TAG
CRYPTO_DIR = DATA_DIR / 'crypto' / TAG
print(f'[경로] 모델 → {{MODEL_DIR}} | 결과 CSV → {{CRYPTO_DIR}}')
"""

def run_cells(path, ids, patch_after):
    cells = fetch_cells(path)
    for i in ids:
        print(f'\\n########## {{Path(path).name}} 셀 {{i}} ##########')
        if not _ip.run_cell(cells[i]).success:
            raise RuntimeError(f'{{path}} 셀 {{i}}에서 오류 — 위 오류 메시지를 확인하세요')
        if i == patch_after and not _ip.run_cell(PATCH).success:
            raise RuntimeError('경로 변경 실패')
print('실행기 준비 완료')
'''

SETUP = f'''# 준비: 데이터·환경·레짐 분할 함수·v4 환경 클래스·valid 구간 (학습 없음)
run_cells('{MAIN}', [2, 4, 6, 8, 9, 11, 12, 44, 46, 50, 72], patch_after=2)
_s25 = fetch_cells('{MAIN}')[25]
exec(_s25[_s25.index('def smooth_perf_row'):_s25.index('smooth_results, smooth_curves = {{}}')], globals())
print('준비 완료')
'''

CONFIG = f'''# 실험 설정 — 자산 수 N만 바꾸고 나머지(30분 주기, 연속 비중, top-K+게이트, Q-teacher 없음, 임베딩, β, 예산)는 v4와 같다.
from stable_baselines3 import PPO as SB3_PPO, DQN as SB3_DQN   # 캐시 래퍼 없는 원본 클래스

N_GRID       = [1, 5, 10, 20, 44]   # 세션을 나눠 돌릴 때는 여기서 일부만 남긴다(예: [1, 5] / [10, 20, 44])
ROUTER_SEEDS = [42, 7, 123]         # 라우터 붕괴가 시드 우연인지 보기 위해 N마다 3개
ALPHA        = 0.01                 # 배포 정책과 같은 추론 시점 스무딩
SCALE_DIR    = MODEL_DIR / 'asset_scaling'
SCALE_DIR.mkdir(parents=True, exist_ok=True)

# N<44 부분집합: 거래대금 상위 순(universe.csv), 스테이블·금 연동 자산 제외, 작은 N이 큰 N에 포함되는 중첩 구조.
# N=44는 기존 rt1006 유니버스·풀·매칭 라우터(시드 42)를 그대로 써서 논문 수치와 일치시킨다.
VOLUME_ORDER = {VOLUME_ORDER!r}
PEGGED = {{'USD1USDT', 'UUSDT', 'RLUSDUSDT', 'PAXGUSDT', 'XAUTUSDT'}}
ALL_SYMBOLS = list(symbols)
RANKED = [s for s in VOLUME_ORDER if s in ALL_SYMBOLS and s not in PEGGED]
RANKED += sorted(s for s in ALL_SYMBOLS if s not in RANKED and s not in PEGGED)

def symbols_for(n):
    return ALL_SYMBOLS if n == len(ALL_SYMBOLS) else RANKED[:n]

for n in N_GRID:
    print(f'N={{n:>2d}}:', symbols_for(n) if n <= 20 else f'전체 {{len(ALL_SYMBOLS)}}종목')
'''

HELPERS = '''def kwargs_for(syms):
    return dict(symbols=syms, emb_index=emb_index, embs_all=embs_all,
                ret_index=ret_index, emb_dim=EMB_DIM, tc=TC)


def segment_for(syms):
    """원본 셀 12와 같은 Stage A 레짐 분할 — 부분집합의 등가중 NAV 기준."""
    eq = np.array([np.mean([ret_index.get((s, b), 0.0) for s in syms]) for b in train_buckets])
    nav = pd.Series(np.cumprod(1 + eq), index=range(len(train_buckets)))
    return segment_and_label(nav, n_labels=N_LABELS, risk_threshold=RISK_THRESHOLD,
                             lowpass_window=LOWPASS_WINDOW)


def perf(net):
    """smooth_perf_row와 같은 정의의 숫자형 지표."""
    net = np.asarray(net, dtype=np.float64)
    r = np.diff(net) / net[:-1]
    return {'ret': net[-1] / net[0] - 1,
            'sharpe': r.mean() / (r.std() + 1e-8) * np.sqrt(48 * 365),
            'mdd': ((net / np.maximum.accumulate(net)) - 1).min()}


def run_ew(kw, buckets):
    env = CryptoPortfolioEnv(buckets, **kw)
    env.reset()
    done, zero = False, np.zeros(env.n_assets, dtype=np.float32)
    while not done:
        _, _, done, _, _ = env.step(zero)   # softmax(0) = 거래 가능 종목 등가중
    return np.array(env.value_history)


def run_solo(model, kw, buckets):
    """전문가 하나를 라우터 없이 α=ALPHA 스무딩으로 실행 (원본 셀 80과 같은 로직)."""
    env = SparseGatedCryptoPortfolioEnv(buckets=buckets, top_k=TOP_K, **kw)
    obs, _ = env.reset()
    done = False
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        target_w, rho, top_idx = env.action_to_weights(a)
        w = (1 - ALPHA) * env.weights + ALPHA * target_w
        obs, _, done, _, _ = env.step_with_weights(w, extra_info={'rho': rho, 'selected': top_idx.tolist()})
    return np.array(env.value_history), float(np.mean(env.rho_history))


def run_router(router, pool, kw, buckets):
    """매칭 라우터(+풀)를 α=ALPHA 스무딩으로 실행 (원본 셀 66·76과 같은 로직). 블록별 선택도 반환."""
    env = MacroRouterEnvV4(buckets=buckets, pool_models=pool, route_buckets=ROUTE_BUCKETS,
                           macro_window=MACRO_WINDOW, top_k=TOP_K, episode_progress_mode='constant', **kw)
    obs, _ = env.reset()
    inner, done, chosen = env.inner, False, []
    while not done:
        k, _ = router.predict(obs, deterministic=True)
        chosen.append(int(k))
        done_inner = False
        for _ in range(env.route_buckets):
            a, _ = env.pool_models[int(k)].predict(inner._get_obs(), deterministic=True)
            target_w, rho, top_idx = inner.action_to_weights(a)
            w = (1 - ALPHA) * inner.weights + ALPHA * target_w
            _, _, done_inner, _, info = inner.step_with_weights(w, extra_info={'rho': rho, 'selected': top_idx.tolist()})
            env._nav_history.append(info['portfolio_value'])
            if done_inner:
                break
        obs = env._macro_obs()
        done = done_inner or inner.t >= len(inner.buckets) - 1
    return np.array(inner.value_history), chosen


def oracle(solo_navs):
    """사후 최적 라우터: 라우팅 블록(1일)마다 그날 수익이 가장 큰 전문가의 단독 경로 수익을 이어 붙인다.
    전문가 간 전환 비용·비중 이어받기를 무시하므로 '라우팅으로 얻을 수 있는 몫'의 상한이다."""
    rets = np.stack([np.diff(v) / v[:-1] for v in solo_navs])          # (전문가, 스텝)
    out = []
    for s in range(0, rets.shape[1], ROUTE_BUCKETS):
        blk = rets[:, s:s + ROUTE_BUCKETS]
        out.append(blk[np.argmax(np.prod(1 + blk, axis=1))])
    return np.concatenate([[1.0], np.cumprod(1 + np.concatenate(out))])


def daily_corr(solo_navs):
    """전문가 쌍별 일간 수익률 상관의 평균 — 전문가가 서로 다른 행동을 하는지(상보성의 필요조건)."""
    d = [np.diff(v[::ROUTE_BUCKETS]) / v[::ROUTE_BUCKETS][:-1] for v in solo_navs]
    c = np.corrcoef(np.stack(d))
    return float(c[np.triu_indices_from(c, 1)].mean())
print('함수 정의 완료')
'''

TRAIN = '''%%time
# N별: 레짐 분할 → 4개 β 전문가 학습(각 10만 스텝) → 매칭 라우터 학습(시드 3개).
# 이미 저장된 모델은 불러오고 건너뛴다 — 끊기면 `모두 실행`을 다시 누르면 된다.
POOL_KW = dict(learning_rate=3e-4, n_steps=1024, batch_size=64, n_epochs=10, gamma=0.99, gae_lambda=0.95,
               clip_range=0.2, ent_coef=0.01, vf_coef=0.5, max_grad_norm=0.5,
               policy_kwargs=dict(net_arch=[512, 256]), verbose=0, device='cpu', seed=42)
ROUTER_KW = dict(learning_rate=1e-3, buffer_size=20_000, learning_starts=500, batch_size=64, gamma=0.95,
                 train_freq=1, target_update_interval=200, exploration_fraction=0.3,
                 exploration_final_eps=0.05, policy_kwargs=dict(net_arch=[128, 64]), verbose=0, device='cpu')

POOLS, ROUTERS, KW = {}, {}, {}
for n in N_GRID:
    syms = symbols_for(n)
    kw = KW[n] = kwargs_for(syms)
    d = SCALE_DIR / f'N{n}'
    d.mkdir(exist_ok=True)
    is_full = n == len(ALL_SYMBOLS)
    seg_n = seg if is_full else segment_for(syms)
    print(f'\\n===== N={n} | 레짐 구간 {len(seg_n.chunks)}개 =====')

    pool_dir = MODEL_DIR / 'crypto_hrl_pool_v4' if is_full else d
    POOLS[n] = {}
    for pool_i, beta in enumerate(POOL_BETAS):
        p = pool_dir / f'agent_beta_{beta}.zip'
        if p.exists():
            POOLS[n][beta] = SB3_PPO.load(str(p), device='cpu')
            print(f'  β={beta}: 로드')
            continue
        env = Monitor(ChunkedSparseGatedEnv(all_buckets=train_buckets, chunks=seg_n.chunks, beta=beta,
                                            risk_threshold=RISK_THRESHOLD, rng=np.random.default_rng(2000 + pool_i),
                                            top_k=TOP_K, **kw))
        m = SB3_PPO('MlpPolicy', env, **POOL_KW)
        m.learn(total_timesteps=POOL_TIMESTEPS_EACH, progress_bar=True)
        m.save(str(p))
        POOLS[n][beta] = m
        print(f'  β={beta}: 학습·저장')

    pool = [POOLS[n][b] for b in POOL_BETAS]
    ROUTERS[n] = {}
    for seed in ROUTER_SEEDS:
        p = (MODEL_DIR / 'crypto_hrl_router_v4_matched.zip') if (is_full and seed == 42) else d / f'router_matched_seed{seed}.zip'
        if p.exists():
            ROUTERS[n][seed] = SB3_DQN.load(str(p), device='cpu')
            print(f'  라우터 시드 {seed}: 로드')
            continue
        env = Monitor(MacroRouterEnvV4(buckets=train_buckets, pool_models=pool, route_buckets=ROUTE_BUCKETS,
                                       macro_window=MACRO_WINDOW, top_k=TOP_K, episode_progress_mode='constant', **kw))
        r = SB3_DQN('MlpPolicy', env, seed=seed, **ROUTER_KW)
        r.learn(total_timesteps=ROUTER_TOTAL_TIMESTEPS, progress_bar=True)
        r.save(str(p))
        ROUTERS[n][seed] = r
        print(f'  라우터 시드 {seed}: 학습·저장')
print('\\n학습 완료')
'''

EVAL = '''%%time
# 평가: valid(2025 Q4)·test(2026 상반기)에서 등가중 / 전문가 단독 4개 / 라우터(시드별) / 사후 최적 라우터
solo_rows, router_rows, summary_rows = [], [], []
for n in N_GRID:
    kw, pool = KW[n], [POOLS[n][b] for b in POOL_BETAS]
    for split, buckets in (('valid', valid_buckets), ('test', test_buckets)):
        ew = perf(run_ew(kw, buckets))
        navs, solo = {}, {}
        for beta in POOL_BETAS:
            navs[beta], rho = run_solo(POOLS[n][beta], kw, buckets)
            solo[beta] = perf(navs[beta])
            solo_rows.append(dict(N=n, split=split, beta=beta, mean_rho=rho, **solo[beta]))
        orc = perf(oracle([navs[b] for b in POOL_BETAS]))
        best_fixed = max(POOL_BETAS, key=lambda b: solo[b]['ret'])
        for seed, router in ROUTERS[n].items():
            nav, chosen = run_router(router, pool, kw, buckets)
            cnt = pd.Series(chosen).value_counts(normalize=True)
            router_rows.append(dict(
                N=n, split=split, seed=seed, **perf(nav),
                n_used=int((cnt > 0).sum()), top_share=float(cnt.max()),
                switches=int(np.sum(np.diff(chosen) != 0)),
                dist={POOL_BETAS[k]: round(v, 3) for k, v in cnt.items()}))
        summary_rows.append(dict(
            N=n, split=split, ew_ret=ew['ret'], ew_sharpe=ew['sharpe'],
            best_fixed_beta=best_fixed, best_fixed_ret=solo[best_fixed]['ret'],
            best_fixed_sharpe=solo[best_fixed]['sharpe'],
            oracle_ret=orc['ret'], oracle_sharpe=orc['sharpe'],
            oracle_gain=orc['ret'] - solo[best_fixed]['ret'],
            solo_rho_spread=float(np.ptp([r['mean_rho'] for r in solo_rows[-len(POOL_BETAS):]])),
            mean_daily_corr=daily_corr([navs[b] for b in POOL_BETAS])))
        print(f'N={n:>2d} {split:5s} | 등가중 {ew["ret"]*100:+.2f}% | 최고 고정 β={best_fixed} {solo[best_fixed]["ret"]*100:+.2f}% '
              f'| 사후 최적 {orc["ret"]*100:+.2f}%')

solo_df, router_df, summary_df = map(pd.DataFrame, (solo_rows, router_rows, summary_rows))
# valid 샤프로 고른 β(배포 규칙)의 test 성과를 요약에 추가
sel = solo_df[solo_df.split == 'valid'].loc[lambda d: d.groupby('N')['sharpe'].idxmax(), ['N', 'beta']]
sel = sel.merge(solo_df[solo_df.split == 'test'], on=['N', 'beta'])[['N', 'beta', 'ret', 'sharpe']]
summary_df = summary_df.merge(sel.rename(columns={'beta': 'valid_sel_beta', 'ret': 'valid_sel_test_ret',
                                                  'sharpe': 'valid_sel_test_sharpe'}), on='N')
rsum = (router_df.groupby(['N', 'split'])
        .agg(router_sharpe_mean=('sharpe', 'mean'), router_ret_mean=('ret', 'mean'),
             collapsed_seeds=('n_used', lambda s: int((s == 1).sum())), seeds=('seed', 'count'),
             mean_top_share=('top_share', 'mean'))
        .reset_index())
summary_df = summary_df.merge(rsum, on=['N', 'split'])

for name, df in (('solo', solo_df), ('router', router_df), ('summary', summary_df)):
    df.to_csv(CRYPTO_DIR / f'crypto_asset_scaling_{name}.csv', index=False, encoding='utf-8-sig')
print('저장 완료: crypto_asset_scaling_{solo,router,summary}.csv')
pd.set_option('display.width', 250)
print(summary_df.round(4).to_string(index=False))
print()
print(router_df[router_df.split == 'test'][['N', 'seed', 'ret', 'sharpe', 'n_used', 'top_share', 'switches', 'dist']]
      .round(4).to_string(index=False))
'''

CHECK = '''# 정합성 확인: N=44 시드 42 라우터의 test 수익률은 논문 표 1 행 8(+8.73%, 샤프 2.602)과 같아야 한다.
if len(ALL_SYMBOLS) in N_GRID and 42 in ROUTER_SEEDS:
    r = router_df[(router_df.N == len(ALL_SYMBOLS)) & (router_df.split == 'test') & (router_df.seed == 42)].iloc[0]
    print(f"N=44 시드 42 test: {r['ret']*100:+.2f}% / 샤프 {r['sharpe']:.3f}  (기대값 +8.73% / 2.602)")
'''

INTRO = md(f'''# [2026-10-23] 자산 수 절제 실험 — 실패가 "다자산 확장" 때문인가?

논문 제목은 실패를 **단일 자산 → 다자산 확장**에 돌리지만, v1→v4 연쇄는 자산 수 외에도 이산→연속 행동, 초→30분 주기, Q-teacher 제거, 임베딩 상태를 **한꺼번에** 바꿨다.
이 노트북은 **자산 수 N만** 1·5·10·20·44로 바꾸고 나머지는 v4 배포 구성(30분, 연속 비중, top-10+게이트, Q-teacher 없음, Chronos–MTGNN 임베딩, β∈{{−90,−30,30,90}}, 같은 학습 예산, α=0.01)과 똑같이 둔다.

N마다 측정하는 것:
1. **라우터 붕괴** — 매칭 DQN 라우터(시드 3개)가 test에서 쓰는 전문가 수, 최다 전문가 비중, 전환 횟수
2. **라우팅의 상한** — 사후 최적 라우터(매일 그날 가장 좋았던 전문가) 대 최고 고정 전문가의 차이
3. **전문가 다양성** — β별 평균 노출(ρ) 폭, 전문가 간 일간 수익률 상관
4. **valid 선택 규칙의 test 성과**와 등가중 대비

**판정**
- 붕괴가 N=1에서도 일어나고 N에 따라 변하지 않으면 → 원인은 다자산이 아니다. 제목·주장을 "다자산 확장 때문"에서 "이 구조(교사 없는 β 풀 + 라우터)의 실패"로 바꾼다.
- N=1에서는 라우터가 전환하고 고정 전문가를 넘지만 N이 커질수록 붕괴하면 → "다자산 확장이 원인"이라는 제목을 실험으로 뒷받침할 수 있다.
- 사후 최적 라우터조차 최고 고정 전문가와 차이가 작으면 → 라우터가 아니라 **전문가들이 서로 보완하지 않는 것**이 문제다.

**실행**
- **`런타임 > 모두 실행`만 누르면 된다.** 끊기면 다시 `모두 실행` — 저장된 모델은 불러와 건너뛴다.
- 새로 학습: PPO 16개(N=1·5·10·20 × β 4개) + DQN 라우터 14개. 12시간을 넘을 수 있으니, 두 Colab 세션에서 `N_GRID`를 `[1, 5]`·`[10, 20, 44]`로 나눠 동시에 돌려도 된다(평가 셀은 각 세션의 N만 저장하므로, 그때는 CSV 이름을 바꾸거나 마지막에 한 세션에서 전체 N으로 다시 `모두 실행`).
- 모델은 `models/rt1006/asset_scaling/N*/`, 결과는 `data/crypto/rt1006/crypto_asset_scaling_*.csv`. N=44는 기존 rt1006 풀과 매칭 라우터(시드 42)를 그대로 불러온다(재학습 없음).
- 드라이브 연결 창에서 **ksbdaniel7@gmail.com** 계정을 고른다.

**한계(결과 해석 시 명시)**: 부분집합은 거래대금 상위 순이라 N과 자산 성격(대형 우량 코인 비중)이 함께 바뀐다. top-K=10은 N≤10에서 사실상 제약이 없다(min(10, N)). 전문가 풀은 N마다 시드 1개다.
''')

nb = {'cells': [INTRO, code(MOUNT), code(RUNNER), code(SETUP), code(CONFIG), code(HELPERS),
                code(TRAIN), code(EVAL), code(CHECK)],
      'metadata': {'kernelspec': {'display_name': 'Python 3', 'name': 'python3'}, 'language_info': {'name': 'python'}},
      'nbformat': 4, 'nbformat_minor': 5}
OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'생성: {OUT}')
