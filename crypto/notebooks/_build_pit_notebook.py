"""
crypto_pit_walkforward_colab.ipynb 조립 스크립트.

기존 두 노트북(crypto_hybrid_model_colab.ipynb, crypto_hrl_earnhft_colab.ipynb)의
검증된 셀을 그대로 재사용하고, point-in-time 13종목 유니버스·2021-2023 학습/2024 검증/
2025-2026 테스트 분할에 맞게 상수만 치환한다. 새 로직(밸리드 기반 β/α 선택, 단독 스무딩
평가, 최종 1회 테스트, 4β 일관성 표, PIT 유니버스 감사 기록)은 새 셀로 추가한다.

실행 후 산출물: crypto_pit_walkforward_colab.ipynb (같은 디렉토리)
"""
import json
import copy
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent
hybrid = json.load(open(NB_DIR / "crypto_hybrid_model_colab.ipynb"))
hrl = json.load(open(NB_DIR / "crypto_hrl_earnhft_colab.ipynb"))


def code_cell(source: str):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": source.splitlines(keepends=True)}


def md_cell(source: str):
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def get_src(nb, i):
    return "".join(nb["cells"][i]["source"])


def replace(src, old, new):
    assert old in src, f"패턴을 못 찾음:\n{old[:200]}"
    return src.replace(old, new, 1)


cells = []

# ============================================================
# 0. 타이틀
# ============================================================
cells.append(md_cell(
    "# Point-in-Time 유니버스 다년 Walk-Forward (크립토, 2021-2023 학습 / 2024 검증 / 2025-2026 테스트)\n\n"
    "**목적**: 배포 정책(β=-30 + 추론시점 스무딩)이 확립된 것과 동일한 '최종 레시피'"
    "(Q-teacher 없는 β-조건부 전문가 풀 + 추론 시점 지수 스무딩, 라우터 없음)를 "
    "**진짜 다년 walk-forward 분할**에서 재검증한다. 기존 44종목 트랙(2025-2026 상반기, "
    "~18개월)은 6장의 모든 강건성 검증(16시드·클린재학습·앙상블·top-K/TC 스윕)이 전부 "
    "같은 캘린더 구간 안에서의 재표본이라는 한계가 있었다 — 이 노트북은 시간축 자체를 "
    "바꿔 재현되는지를 본다.\n\n"
    "**유니버스 — point-in-time 선정 절차**: 44종목 동적 유니버스(오늘 기준 거래대금 상위)를 "
    "그대로 축소하는 대신, CoinMarketCap의 2021-01-01 히스토리컬 스냅샷(top-20 시가총액, "
    "https://coinmarketcap.com/historical/20210101/ )을 확인해 스테이블코인(USDT·USDC)·"
    "래핑 자산(WBTC)을 제외한 '진짜' 자산 17개를 추린 뒤, 2026-08-18 기준 바이낸스 현물에서"
    " 실제로 active 상태인지 ccxt로 직접 검증했다. 결과: **13개는 지금도 거래 가능**(BTC· "
    "ETH·XRP·LTC·BCH·ADA·BNB·LINK·XLM·TRX·DOT·THETA·XTZ), **4개는 확인상 비활성/거래중단**"
    "(BSV·EOS·XMR·XEM — 이 4개가 이 실험이 해소하지 못하는 잔존 생존편향이다). DOT·THETA·"
    "XTZ는 기존 44/50종목 백필 풀에 없어서(오늘 기준 관련성 기준으로 뽑혔기 때문) 이번에"
    " 추가로 2021-01-01부터 백필했다 — `backfill_pit_extra.py` 참고.\n\n"
    "**분할**: 학습 2021-01-01~2023-12-31(3년) / 검증 2024-01-01~2024-12-31(1년, 완전 "
    "미노출) / 테스트 2025-01-01~데이터 끝(~2026-07, 1.5년) — KOSPI 트랙(2021-2023 학습/"
    "2024-2025 테스트)과 구조가 같아 직접 비교도 가능하다.\n\n"
    "**§A는 임베딩 백본(Chronos+MTGNN) 재학습**(13종목·2021~ 전체 구간 임베딩 생성), "
    "**§B는 RL 최종 레시피 재현**(Stage A 레짐분할 → Stage B 4β 풀 학습 → valid에서 β·α "
    "선택 → test 1회 평가 → 4β 전체 valid/test 일관성 표)이다."
))

# ============================================================
# §A. 백본 (crypto_hybrid_model_colab.ipynb 이식)
# ============================================================
cells.append(md_cell("## §A. 임베딩 백본 재학습 (Chronos+MTGNN, 13종목·2021-01~ 전체 구간)"))

cells.append(code_cell(get_src(hybrid, 1)))  # drive mount + installs

setup_src = get_src(hybrid, 2)
setup_src = replace(
    setup_src,
    "DRIVE_ROOT = Path('/content/drive/MyDrive/졸업프로젝트')",
    "DRIVE_ROOT = Path('/content/drive/MyDrive/졸업프로젝트')\n\n"
    "PIT_SYMBOLS = [  # point-in-time 유니버스 13종목 (§0 타이틀 셀 참고)\n"
    "    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'LTCUSDT', 'BCHUSDT', 'ADAUSDT', 'BNBUSDT',\n"
    "    'LINKUSDT', 'XLMUSDT', 'TRXUSDT', 'DOTUSDT', 'THETAUSDT', 'XTZUSDT',\n"
    "]"
)
setup_src = replace(
    setup_src,
    "EMB_CACHE  = CRYPTO_DIR / 'crypto_chronos_embs.npz'\n"
    "RL_EMB_H5  = CRYPTO_DIR / 'crypto_rl_embeddings.h5'\n"
    "RESULT_JSON= CRYPTO_DIR / 'crypto_hybrid_result.json'",
    "EMB_CACHE  = CRYPTO_DIR / 'crypto_pit_chronos_embs.npz'\n"
    "RL_EMB_H5  = CRYPTO_DIR / 'crypto_pit_rl_embeddings.h5'\n"
    "RESULT_JSON= CRYPTO_DIR / 'crypto_pit_hybrid_result.json'"
)
setup_src = replace(
    setup_src,
    "TRAIN_END  = pd.Timestamp('2025-07-01', tz='UTC')   # train: ~2025-06\n"
    "VAL_END    = pd.Timestamp('2026-01-01', tz='UTC')   # val: 2025-07~12, test: 2026-01~",
    "# 백본 자체의 예측(방향성) 학습/검증/테스트 분할 — 아래 §B의 RL walk-forward 분할과\n"
    "# 경계를 통일해(2021-2023/2024/2025-2026) 두 단계 사이에 별도의 숨은 데이터 누출\n"
    "# 경로가 생기지 않도록 함\n"
    "TRAIN_END  = pd.Timestamp('2024-01-01', tz='UTC')   # 백본 예측 학습: 2021-01~2023-12\n"
    "VAL_END    = pd.Timestamp('2025-01-01', tz='UTC')   # 백본 예측 검증: 2024, 테스트: 2025-01~"
)
setup_src = replace(
    setup_src,
    "files = sorted(glob.glob(str(FEAT_DIR / '*.parquet')))\n"
    "assert files, f'피처 parquet 없음: {FEAT_DIR} — 로컬 features_5m 폴더를 Drive에 업로드했는지 확인'\n"
    "print(f'심볼 parquet {len(files)}개')",
    "files_all = sorted(glob.glob(str(FEAT_DIR / '*.parquet')))\n"
    "assert files_all, f'피처 parquet 없음: {FEAT_DIR} — 로컬 features_5m 폴더를 Drive에 업로드했는지 확인'\n"
    "files = [f for f in files_all if Path(f).stem in PIT_SYMBOLS]\n"
    "missing = set(PIT_SYMBOLS) - {Path(f).stem for f in files}\n"
    "_missing_msg = (\n"
    "    f'PIT 유니버스 중 로컬에 없는 심볼: {missing} — DOT/THETA/XTZ는 '\n"
    "    'backfill_pit_extra.py + preprocess_features.py 재실행 후 features_5m 폴더를 '\n"
    "    'Drive에 다시 업로드했는지 확인'\n"
    ")\n"
    "assert not missing, _missing_msg\n"
    "print(f'PIT 심볼 parquet {len(files)}/{len(PIT_SYMBOLS)}개 확인됨')"
)
cells.append(code_cell(setup_src))

cells.append(code_cell(get_src(hybrid, 3)))   # markdown "## 1. 데이터 로드..." -- actually cell 3 is markdown
# NOTE: cell 3 is markdown in source notebook; fix below by using md_cell appropriately.
cells[-1] = md_cell(get_src(hybrid, 3))

cells.append(code_cell(get_src(hybrid, 4)))   # window sampling loop (파일 필터링은 이미 반영됨)
cells.append(code_cell(get_src(hybrid, 5)))

for i in range(6, 19):  # Chronos 추출, 모델 정의, 데이터셋/로더, 학습/평가 함수, 학습 실행, 결과 평가
    src = get_src(hybrid, i)
    ctype = hybrid["cells"][i]["cell_type"]
    cells.append(md_cell(src) if ctype == "markdown" else code_cell(src))

cells.append(md_cell(get_src(hybrid, 19)))    # "## 8. RL용 임베딩 추출" 마크다운

emb_src = get_src(hybrid, 20)
emb_src = replace(
    emb_src,
    "RL_START = pd.Timestamp('2025-01-01', tz='UTC')   # RL train: 2025년 / RL test: 2026년~",
    "RL_START = pd.Timestamp('2021-01-01', tz='UTC')   # PIT walk-forward: 전체 구간(2021~) 임베딩 필요"
)
cells.append(code_cell(emb_src))
cells.append(code_cell(get_src(hybrid, 21)))  # h5 저장 (경로는 §A 상수 셀에서 이미 pit 파일명으로 교체됨)

# ============================================================
# §B. RL 최종 레시피 — walk-forward 재현
# ============================================================
cells.append(md_cell(
    "## §B. RL 최종 레시피 재현 (Stage A/B + valid 기반 β·α 선택, 라우터 없음)\n\n"
    "라우터(Stage C)는 배포 레시피에서 이미 기여 0으로 확인됐으므로(원 논문 4.5–4.6절) "
    "여기서는 처음부터 제외한다. top-K-플러스-게이트(v4)도 13종목이라는 작은 행동공간에서는 "
    "구조적 필요성이 약해 생략하고, v1 스타일 밀집 softmax + β-조건부 청크 샘플링 + 추론 "
    "시점 스무딩만 이식한다."
))

cells.append(code_cell(get_src(hrl, 1)))  # installs

hrl_setup = get_src(hrl, 2)
hrl_setup = replace(
    hrl_setup,
    "RL_EMB_H5      = CRYPTO_DIR / 'crypto_rl_embeddings.h5'\n"
    "ORIG_PPO_PATH  = MODEL_DIR / 'crypto_ppo_portfolio.zip'   # crypto_rl_trading_colab.ipynb 산출물(있으면 비교에 포함)",
    "RL_EMB_H5      = CRYPTO_DIR / 'crypto_pit_rl_embeddings.h5'\n"
    "POOL_DIR       = MODEL_DIR / 'crypto_pit_hrl_pool'   # §2 상수와 별도 디렉토리(44종목 풀과 섞이지 않도록)"
)
hrl_setup = replace(
    hrl_setup,
    "RL_TRAIN_START = '2025-01-01'\n"
    "RL_TRAIN_END   = '2025-12-31'\n"
    "RL_TEST_START  = '2026-01-01'\n"
    "RL_TEST_END    = '2099-12-31'   # 열린 구간",
    "RL_TRAIN_START = '2021-01-01'\n"
    "RL_TRAIN_END   = '2023-12-31'\n"
    "RL_VALID_START = '2024-01-01'\n"
    "RL_VALID_END   = '2024-12-31'\n"
    "RL_TEST_START  = '2025-01-01'\n"
    "RL_TEST_END    = '2099-12-31'   # 열린 구간 — 실제로는 데이터 끝(~2026-07)까지"
)
hrl_setup = replace(
    hrl_setup,
    "ROUTE_BUCKETS         = 48         # Stage C 라우팅 단위 = 1일\n"
    "MACRO_WINDOW           = 96        # 라우터 상태에 포함할 최근 버킷 수 (=2일)\n"
    "ROUTER_TOTAL_TIMESTEPS = 20_000    # 라우터(=일 단위) 학습 스텝\n\n"
    "assert RL_EMB_H5.exists(), 'crypto_rl_embeddings.h5 없음 — crypto_hybrid_model_colab.ipynb 먼저 실행'",
    "SMOOTH_ALPHAS          = [1.0, 0.3, 0.15, 0.05, 0.03, 0.02, 0.01]  # 라우터 없음 → §9 스타일 스윕만\n\n"
    "assert RL_EMB_H5.exists(), 'crypto_pit_rl_embeddings.h5 없음 — 위 §A를 먼저 실행'"
)
cells.append(code_cell(hrl_setup))

cells.append(md_cell(get_src(hrl, 3)))
cells.append(code_cell(get_src(hrl, 4)))   # 임베딩 로드 (그대로 재사용 가능 — symbols는 h5에서 자동으로 13개)
cells.append(md_cell(get_src(hrl, 5)))

ret_src = get_src(hrl, 6)
ret_src = replace(
    ret_src,
    "rl_start_ts = pd.Timestamp(RL_TRAIN_START, tz='UTC')",
    "rl_start_ts = pd.Timestamp(RL_TRAIN_START, tz='UTC')  # = 2021-01-01, §A와 동일 시작점"
)
cells.append(code_cell(ret_src))

cells.append(md_cell(get_src(hrl, 7)))
cells.append(code_cell(get_src(hrl, 8)))   # CryptoPortfolioEnv — 그대로(N_ASSETS은 symbols 길이로 자동 결정 = 13)

bucket_split_src = (
    "def bucket_to_ts(b):\n"
    "    return pd.Timestamp(b * BUCKET_SEC, unit='s', tz='UTC')\n\n"
    "def bucket_to_date(b):\n"
    "    return bucket_to_ts(b).strftime('%Y-%m-%d')\n\n"
    "train_buckets = [b for b in all_buckets if RL_TRAIN_START <= bucket_to_date(b) <= RL_TRAIN_END]\n"
    "valid_buckets = [b for b in all_buckets if RL_VALID_START <= bucket_to_date(b) <= RL_VALID_END]\n"
    "test_buckets  = [b for b in all_buckets if RL_TEST_START  <= bucket_to_date(b) <= RL_TEST_END]\n"
    "print(f'학습 기간: {bucket_to_ts(train_buckets[0])} ~ {bucket_to_ts(train_buckets[-1])} ({len(train_buckets):,}스텝)')\n"
    "print(f'검증 기간: {bucket_to_ts(valid_buckets[0])} ~ {bucket_to_ts(valid_buckets[-1])} ({len(valid_buckets):,}스텝)')\n"
    "print(f'테스트 기간: {bucket_to_ts(test_buckets[0])} ~ {bucket_to_ts(test_buckets[-1])} ({len(test_buckets):,}스텝)')\n\n"
    "env_kwargs = dict(\n"
    "    symbols=symbols, emb_index=emb_index, embs_all=embs_all,\n"
    "    ret_index=ret_index, emb_dim=EMB_DIM, tc=TC,\n"
    ")\n\n"
    "print('\\n환경 유효성 검사...')\n"
    "check_env(CryptoPortfolioEnv(train_buckets[:100], **env_kwargs), warn=True)\n"
    "print('OK')"
)
cells.append(code_cell(bucket_split_src))

cells.append(md_cell(get_src(hrl, 10)))
cells.append(code_cell(get_src(hrl, 11)))  # market_segmentation 이식 — 그대로

seg_src = get_src(hrl, 12)
seg_src = replace(seg_src, "학습 구간)", "학습 구간, 2021–2023)")
cells.append(code_cell(seg_src))

cells.append(md_cell(get_src(hrl, 13)))
cells.append(code_cell(get_src(hrl, 14)))  # ChunkedCryptoPortfolioEnv — 그대로
cells.append(code_cell(get_src(hrl, 15)))  # Stage B 학습 루프 — 그대로 (POOL_DIR는 이미 pit 경로로 교체됨)

# --- 신규: helper 함수 (라우터 없는 run_backtest류) ---
helpers_src = (
    "def compute_perf(values, steps_per_year=48 * 365):\n"
    "    \"\"\"성과 지표 계산 — 30분봉·24/7 시장 기준 연환산(48스텝/일)\"\"\"\n"
    "    rets       = np.diff(values) / values[:-1]\n"
    "    total_ret  = values[-1] / values[0] - 1\n"
    "    annual_ret = (1 + total_ret) ** (steps_per_year / len(rets)) - 1\n"
    "    sharpe     = rets.mean() / (rets.std() + 1e-8) * np.sqrt(steps_per_year)\n"
    "    max_dd     = ((values / np.maximum.accumulate(values)) - 1).min()\n"
    "    return {'총 수익률': total_ret, '연환산 수익률': annual_ret, 'Sharpe': sharpe, 'MDD': max_dd}\n\n"
    "\n"
    "def run_backtest(env, model, deterministic=True):\n"
    "    obs, _ = env.reset()\n"
    "    done, values = False, [1.0]\n"
    "    while not done:\n"
    "        action, _ = model.predict(obs, deterministic=deterministic)\n"
    "        obs, _, done, _, info = env.step(action)\n"
    "        values.append(info['portfolio_value'])\n"
    "    return np.array(values), list(env.turnover_history)\n\n"
    "\n"
    "def equal_weight_backtest(env):\n"
    "    obs, _ = env.reset()\n"
    "    done, values = False, [1.0]\n"
    "    action = np.ones(env.n_assets, dtype=np.float32) / env.n_assets\n"
    "    while not done:\n"
    "        obs, _, done, _, info = env.step(action)\n"
    "        values.append(info['portfolio_value'])\n"
    "    return np.array(values), list(env.turnover_history)\n\n"
    "\n"
    "def _softmax_np(a):\n"
    "    e = np.exp(a - a.max())\n"
    "    return e / e.sum()\n\n"
    "\n"
    "def run_standalone_smoothed(model, buckets, alpha):\n"
    "    \"\"\"라우터 없이 단일 β 전문가에 추론 시점 관성 스무딩만 적용해 buckets 구간을 실행.\n"
    "    반환: (비용 후 NAV, 비용 전 NAV, 턴오버 리스트) — §7 run_hrl_smoothed의 무라우터 버전.\"\"\"\n"
    "    env = CryptoPortfolioEnv(buckets, **env_kwargs)\n"
    "    obs, _ = env.reset()\n"
    "    gross, g, done = [1.0], 1.0, False\n"
    "    while not done:\n"
    "        a, _ = model.predict(obs, deterministic=True)\n"
    "        w = (1 - alpha) * env.weights + alpha * _softmax_np(a)\n"
    "        obs, _, done, _, info = env.step(np.log(w))\n"
    "        g *= 1 + info['port_ret']\n"
    "        gross.append(g)\n"
    "    return np.array(env.value_history), np.array(gross), list(env.turnover_history)\n\n"
    "\n"
    "print('헬퍼 함수 정의 완료')"
)
cells.append(md_cell("### B-6. 헬퍼 함수 (compute_perf / run_backtest / 단독 스무딩 실행)"))
cells.append(code_cell(helpers_src))

# --- 신규: valid에서 4β 원시(스무딩 없음) 성과 비교 ---
valid_raw_src = (
    "valid_env = CryptoPortfolioEnv(valid_buckets, **env_kwargs)\n"
    "test_env  = CryptoPortfolioEnv(test_buckets,  **env_kwargs)\n\n"
    "raw_rows = {}\n"
    "for beta in POOL_BETAS:\n"
    "    v_values, _ = run_backtest(CryptoPortfolioEnv(valid_buckets, **env_kwargs), pool_models[beta])\n"
    "    raw_rows[f'β={beta}'] = compute_perf(v_values)\n\n"
    "ew_valid_values, _ = equal_weight_backtest(CryptoPortfolioEnv(valid_buckets, **env_kwargs))\n"
    "raw_rows['등가중'] = compute_perf(ew_valid_values)\n\n"
    "raw_df = pd.DataFrame(raw_rows).T\n"
    "print('검증구간(2024) 원시(스무딩 없음) 성과 — β 선택 전 사전 확인용')\n"
    "print(raw_df.to_string())"
)
cells.append(md_cell("### B-7. 검증구간(2024)에서 4β 원시 성과 확인"))
cells.append(code_cell(valid_raw_src))

# --- 신규: valid에서 β×α 스윕 → best 선택 (4.6/6.3 방법론과 동일하게 test는 안 봄) ---
alpha_sweep_src = (
    "# 4개 β 전부에 대해 검증구간(2024)에서 α 스윕 → 검증 샤프가 가장 높은 (β, α) 조합을 선택.\n"
    "# 원 논문 4.6절 방법론(테스트를 전혀 보지 않고 검증만으로 선택)을 그대로 따른다.\n"
    "valid_sweep = {}\n"
    "for beta in POOL_BETAS:\n"
    "    model = pool_models[beta]\n"
    "    for alpha in SMOOTH_ALPHAS:\n"
    "        net, gross, turns = run_standalone_smoothed(model, valid_buckets, alpha)\n"
    "        perf = compute_perf(net)\n"
    "        valid_sweep[(beta, alpha)] = perf\n"
    "    print(f'β={beta} valid 스윕 완료')\n\n"
    "sweep_df = pd.DataFrame(valid_sweep).T\n"
    "sweep_df.index.names = ['beta', 'alpha']\n"
    "BEST_BETA, BEST_ALPHA = sweep_df['Sharpe'].idxmax()\n"
    "print(f'\\n검증 샤프 최고: β={BEST_BETA}, α={BEST_ALPHA} (검증 샤프 {sweep_df[\"Sharpe\"].max():.3f})')\n"
    "print()\n"
    "print(sweep_df.sort_values('Sharpe', ascending=False).head(10).to_string())\n"
    "sweep_df.to_csv(CRYPTO_DIR / 'crypto_pit_valid_sweep.csv', encoding='utf-8-sig')"
)
cells.append(md_cell(
    "### B-8. 검증구간(2024)에서 β×α 스윕 — 테스트는 아직 보지 않음\n\n"
    "4개 β × 7개 α = 28개 조합을 전부 **검증구간에서만** 평가해 최고 검증 샤프 조합을 고른다. "
    "이 시점까지 테스트구간(2025-2026)은 코드 어디에서도 실행되지 않는다 — 원 논문 4.6/6.3절과 "
    "동일한 선택 편향 방지 절차."
))
cells.append(code_cell(alpha_sweep_src))

# --- 신규: 최종 test 1회 평가 ---
final_test_src = (
    "print(f'[최종 검증] 검증구간에서 고른 (β={BEST_BETA}, α={BEST_ALPHA})로 테스트구간을 \"1회만\" 실행')\n\n"
    "final_model = pool_models[BEST_BETA]\n"
    "net, gross, turns = run_standalone_smoothed(final_model, test_buckets, BEST_ALPHA)\n"
    "final_perf = compute_perf(net)\n"
    "gross_perf = compute_perf(gross)\n\n"
    "ew_test_values, ew_test_turns = equal_weight_backtest(CryptoPortfolioEnv(test_buckets, **env_kwargs))\n"
    "ew_perf = compute_perf(ew_test_values)\n\n"
    "final_df = pd.DataFrame({\n"
    "    f'PIT 최종(β={BEST_BETA}, α={BEST_ALPHA}) — 비용 후': final_perf,\n"
    "    f'PIT 최종 — 비용 전': gross_perf,\n"
    "    '등가중 벤치마크(2025-2026 테스트)': ew_perf,\n"
    "}).T\n"
    "print()\n"
    "print(final_df.to_string())\n"
    "final_df.to_csv(CRYPTO_DIR / 'crypto_pit_final_test.csv', encoding='utf-8-sig')\n\n"
    "fig, ax = plt.subplots(figsize=(14, 5))\n"
    "ax.plot(net, label=f'PIT 최종(β={BEST_BETA}, α={BEST_ALPHA})', lw=1.8)\n"
    "ax.plot(ew_test_values, label='등가중 벤치마크', lw=1.5, ls='--')\n"
    "ax.axhline(1, color='gray', lw=0.8, ls=':')\n"
    "ax.set_title(f'Point-in-Time 13종목 walk-forward — 테스트구간({RL_TEST_START}~) 누적가치')\n"
    "ax.set_xlabel('30분 스텝')\n"
    "ax.set_ylabel('포트폴리오 가치 (초기=1.0)')\n"
    "ax.legend()\n"
    "ax.grid(alpha=0.3)\n"
    "plt.tight_layout()\n"
    "plt.savefig(CRYPTO_DIR / 'crypto_pit_final_test.png', dpi=150, bbox_inches='tight')\n"
    "plt.show()"
)
cells.append(md_cell("### B-9. 최종 (β\\*, α\\*)를 테스트구간(2025-2026)에서 1회 평가"))
cells.append(code_cell(final_test_src))

# --- 신규: 4β 전체 valid/test 일관성 표 (원 논문 4.6절 표와 동일 형식) ---
consistency_src = (
    "# 원 논문 4.6절과 동일한 형식 — 4개 β 전부를 라우터 없이 단독으로, 각 β 자신의 검증-최고\n"
    "# α로(검증 스윕에서 이미 계산됨) 검증구간·테스트구간 양쪽에서 실행해 |검증-테스트| 샤프\n"
    "# 격차를 계산한다. 이 표가 §B-8에서 β=BEST_BETA를 고른 근거를 다른 β와 나란히 보여준다.\n"
    "rows = []\n"
    "for beta in POOL_BETAS:\n"
    "    beta_sweep = {a: valid_sweep[(beta, a)]['Sharpe'] for a in SMOOTH_ALPHAS}\n"
    "    best_alpha_for_beta = max(beta_sweep, key=beta_sweep.get)\n"
    "    model = pool_models[beta]\n\n"
    "    v_net, _, _ = run_standalone_smoothed(model, valid_buckets, best_alpha_for_beta)\n"
    "    t_net, _, _ = run_standalone_smoothed(model, test_buckets,  best_alpha_for_beta)\n"
    "    v_perf, t_perf = compute_perf(v_net), compute_perf(t_net)\n\n"
    "    rows.append({\n"
    "        'beta': beta, 'best_alpha(valid)': best_alpha_for_beta,\n"
    "        'valid_sharpe': v_perf['Sharpe'], 'test_sharpe': t_perf['Sharpe'],\n"
    "        'valid_ret': v_perf['총 수익률'], 'test_ret': t_perf['총 수익률'],\n"
    "        'valid_test_gap': abs(v_perf['Sharpe'] - t_perf['Sharpe']),\n"
    "    })\n\n"
    "consistency_df = pd.DataFrame(rows).set_index('beta')\n"
    "print('4β 전체 검증/테스트 일관성 표 (원 논문 4.6절 형식)')\n"
    "print(consistency_df.to_string())\n"
    "consistency_df.to_csv(CRYPTO_DIR / 'crypto_pit_consistency_table.csv', encoding='utf-8-sig')"
)
cells.append(md_cell(
    "### B-10. 4β 전체 검증/테스트 일관성 표\n\n"
    "원 논문 4.6절 표와 같은 형식 — β=-30이 44종목 트랙에서처럼 여기서도 격차가 가장 작은지, "
    "혹은 이 point-in-time 세팅에서는 다른 β가 더 견조한지를 직접 비교한다."
))
cells.append(code_cell(consistency_src))

# --- 신규: PIT 유니버스 감사 기록 (논문 인용용) ---
audit_src = (
    "pit_audit = {\n"
    "    'snapshot_source': 'https://coinmarketcap.com/historical/20210101/',\n"
    "    'snapshot_date': '2021-01-01',\n"
    "    'verification_date': '2026-08-18',\n"
    "    'verification_method': 'ccxt.binance().load_markets() — 실시간 조회',\n"
    "    'cmc_top20_ex_stable_wrapped': [\n"
    "        'BTC', 'ETH', 'XRP', 'LTC', 'DOT', 'BCH', 'ADA', 'BNB', 'LINK', 'BSV',\n"
    "        'XLM', 'EOS', 'XMR', 'XEM', 'THETA', 'TRX', 'XTZ',\n"
    "    ],  # USDT·USDC(스테이블코인), WBTC(래핑) 제외\n"
    "    'included_13': PIT_SYMBOLS,\n"
    "    'excluded_confirmed_inactive_4': {\n"
    "        'BSVUSDT':  'active=False (ccxt 확인, 2026-08-18)',\n"
    "        'EOSUSDT':  'active=False (ccxt 확인, 2026-08-18)',\n"
    "        'XMRUSDT':  'active=False (ccxt 확인, 2026-08-18)',\n"
    "        'XEMUSDT':  'active=False (ccxt 확인, 2026-08-18)',\n"
    "    },\n"
    "    'scope_limitation': (\n"
    "        'top-20까지만 CMC 히스토리컬 스냅샷을 확인함(21~50위는 JS 렌더링 페이지네이션 때문에 '\n"
    "        '스크래핑 불가) — 이 유니버스는 \"2021년 1월 시총 top-20 중 바이낸스에서 지금도 '\n"
    "        '거래 가능한 것\"으로 엄격히 한정되며, 44종목 원 트랙과 같은 폭을 주장하지 않는다.'\n"
    "    ),\n"
    "}\n"
    "with open(CRYPTO_DIR / 'crypto_pit_universe_audit.json', 'w', encoding='utf-8') as f:\n"
    "    json.dump(pit_audit, f, ensure_ascii=False, indent=2)\n"
    "print(json.dumps(pit_audit, ensure_ascii=False, indent=2))"
)
cells.append(md_cell(
    "### B-11. Point-in-Time 유니버스 감사 기록 (논문 인용용, 재실행 시 항상 저장)\n\n"
    "이 셀은 백테스트와 무관하며, 유니버스 선정 근거를 논문에 그대로 인용할 수 있게 "
    "JSON으로 남긴다."
))
cells.append(code_cell(audit_src))

# ============================================================
# 조립 & 저장
# ============================================================
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"},
        "colab": {"provenance": [], "gpuType": "T4"},
        "accelerator": "GPU",
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out_path = NB_DIR / "crypto_pit_walkforward_colab.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"작성 완료: {out_path} ({len(cells)}개 셀)")
