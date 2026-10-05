"""
crypto_pit_walkforward_colab.ipynb에 강건성 후속 진단 셀을 추가한다.
기존 실행 결과(§A/§B, outputs 포함)는 건드리지 않고 뒤에 새 셀만 이어붙인다.

추가하는 것:
  §C-1 로더 — 세션이 끊겨도 저장된 4β 풀만 다시 불러오면 이어서 실행 가능
  §C-2 롤링 검증/테스트 재분할 — 재학습 없이 2024~2026을 6개월 블록으로 나눠
       인접 블록 쌍(valid=B_i, test=B_{i+1})마다 동일한 절차(valid 스윕→선택→test 1회)를
       반복해, "2024강세장→2025급락"이 유난히 가혹한 한 조합이었는지 아니면 반복되는
       패턴인지 확인한다.
  §C-3 다양성 진단 — 이 13종목·2021-2023 학습에서 4개 β가 v3처럼 사실상 균등가중
       클론으로 수렴했는지, 비중 궤적 페어와이즈 상관으로 확인한다.
"""
import json
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent
NB_PATH = NB_DIR / "crypto_pit_walkforward_colab.ipynb"

nb = json.load(open(NB_PATH))


def code_cell(source: str):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": source.splitlines(keepends=True)}


def md_cell(source: str):
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


new_cells = []

# ============================================================
# §C 도입부
# ============================================================
new_cells.append(md_cell(
    "## §C. 후속 강건성 진단 — 재학습 없이 이미 학습된 4β 풀 재사용\n\n"
    "§B의 결과(검증 2024 강세장 → 테스트 2025-2026 급락, 격차 1.73)가 유난히 가혹한 "
    "한 번의 국면 전환이었는지, 이 방법론 자체의 반복되는 패턴인지 §B에서는 구분할 수 "
    "없었다. 아래는 **재학습 없이** 이미 학습된(2021-2023) 4개 β 고정 정책만 재사용해 "
    "두 가지를 확인한다: (C-2) 검증/테스트 경계를 여러 지점으로 밀어가며 반복 평가, "
    "(C-3) 4개 β가 실제로 서로 다른 정책이었는지(v3식 다양성 붕괴 재발 여부)."
))

# ============================================================
# §C-1 로더
# ============================================================
loader_src = (
    "# 세션이 끊겨 pool_models가 메모리에 없어도 저장된 4β 풀만 다시 불러오면\n"
    "# 재학습 없이 아래 진단을 이어서 실행할 수 있다.\n"
    "if 'pool_models' not in globals() or not pool_models:\n"
    "    pool_models = {b: PPO.load(str(POOL_DIR / f'agent_beta_{b}.zip')) for b in POOL_BETAS}\n"
    "    print('4β 풀 로드 완료:', list(pool_models.keys()))\n"
    "else:\n"
    "    print('pool_models 이미 메모리에 있음 — 재사용')\n\n"
    "assert 'env_kwargs' in globals(), 'env_kwargs 없음 — §B의 데이터 로드 셀(1~4)을 먼저 실행할 것'\n"
    "assert 'run_standalone_smoothed' in globals(), '헬퍼 함수 없음 — §B-6 셀을 먼저 실행할 것'"
)
new_cells.append(md_cell("### C-1. 로더 (세션 재시작 대비)"))
new_cells.append(code_cell(loader_src))

# ============================================================
# §C-2 롤링 검증/테스트 재분할
# ============================================================
rolling_src = (
    "# 2024-01-01 ~ 2026-06-30를 6개월 블록 5개로 나누고(2026-07~08은 데이터가 2개월뿐이라 제외),\n"
    "# 인접한 블록 쌍마다 (valid=B_i, test=B_{i+1})로 §B-8/B-9와 동일한 절차를 반복한다:\n"
    "#   1) 4β × 7α = 28개 조합을 valid 블록에서만 스윕해 검증 샤프 최고 (β,α) 선택\n"
    "#   2) 그 (β,α)를 test 블록에서 1회 평가\n"
    "# 재학습은 전혀 없다 — pool_models는 2021-2023으로 이미 고정 학습된 4개 정책.\n\n"
    "BLOCK_BOUNDARIES = [\n"
    "    ('2024-01-01', '2024-06-30'),\n"
    "    ('2024-07-01', '2024-12-31'),\n"
    "    ('2025-01-01', '2025-06-30'),\n"
    "    ('2025-07-01', '2025-12-31'),\n"
    "    ('2026-01-01', '2026-06-30'),\n"
    "]\n\n"
    "def block_buckets(start, end):\n"
    "    return [b for b in all_buckets if start <= bucket_to_date(b) <= end]\n\n"
    "blocks = [block_buckets(s, e) for s, e in BLOCK_BOUNDARIES]\n"
    "for (s, e), blk in zip(BLOCK_BOUNDARIES, blocks):\n"
    "    print(f'{s} ~ {e}: {len(blk):,}스텝' + ('' if blk else '  (데이터 없음 — 스킵됨)'))\n\n"
    "rolling_rows = []\n"
    "for i in range(len(blocks) - 1):\n"
    "    v_buckets, t_buckets = blocks[i], blocks[i + 1]\n"
    "    if not v_buckets or not t_buckets:\n"
    "        continue\n"
    "    v_label = f'{BLOCK_BOUNDARIES[i][0]}~{BLOCK_BOUNDARIES[i][1]}'\n"
    "    t_label = f'{BLOCK_BOUNDARIES[i+1][0]}~{BLOCK_BOUNDARIES[i+1][1]}'\n\n"
    "    # 1) 이 fold의 valid 블록에서 28개 조합 스윕\n"
    "    fold_sweep = {}\n"
    "    for beta in POOL_BETAS:\n"
    "        model = pool_models[beta]\n"
    "        for alpha in SMOOTH_ALPHAS:\n"
    "            net, _, _ = run_standalone_smoothed(model, v_buckets, alpha)\n"
    "            fold_sweep[(beta, alpha)] = compute_perf(net)['Sharpe']\n"
    "    best_beta, best_alpha = max(fold_sweep, key=fold_sweep.get)\n\n"
    "    # 2) 그 (β,α)로 이 fold의 test 블록을 1회 평가\n"
    "    v_net, _, _ = run_standalone_smoothed(pool_models[best_beta], v_buckets, best_alpha)\n"
    "    t_net, _, _ = run_standalone_smoothed(pool_models[best_beta], t_buckets, best_alpha)\n"
    "    v_perf, t_perf = compute_perf(v_net), compute_perf(t_net)\n\n"
    "    # 참조용 등가중\n"
    "    ew_v, _ = equal_weight_backtest(CryptoPortfolioEnv(v_buckets, **env_kwargs))\n"
    "    ew_t, _ = equal_weight_backtest(CryptoPortfolioEnv(t_buckets, **env_kwargs))\n\n"
    "    rolling_rows.append({\n"
    "        'valid_block': v_label, 'test_block': t_label,\n"
    "        'selected_beta': best_beta, 'selected_alpha': best_alpha,\n"
    "        'valid_sharpe': v_perf['Sharpe'], 'test_sharpe': t_perf['Sharpe'],\n"
    "        'gap': abs(v_perf['Sharpe'] - t_perf['Sharpe']),\n"
    "        'valid_ret': v_perf['총 수익률'], 'test_ret': t_perf['총 수익률'],\n"
    "        'ew_valid_sharpe': compute_perf(ew_v)['Sharpe'], 'ew_test_sharpe': compute_perf(ew_t)['Sharpe'],\n"
    "    })\n"
    "    print(f'[{v_label} → {t_label}] 선택 β={best_beta},α={best_alpha} | '\n"
    "          f'valid Sharpe {v_perf[\"Sharpe\"]:.3f} → test Sharpe {t_perf[\"Sharpe\"]:.3f} '\n"
    "          f'(격차 {abs(v_perf[\"Sharpe\"]-t_perf[\"Sharpe\"]):.3f})')\n\n"
    "rolling_df = pd.DataFrame(rolling_rows)\n"
    "print()\n"
    "print(rolling_df.to_string(index=False))\n"
    "print()\n"
    "print(f'평균 격차: {rolling_df[\"gap\"].mean():.3f} | 중앙값 격차: {rolling_df[\"gap\"].median():.3f} | '\n"
    "      f'격차<0.3인 fold 수: {(rolling_df[\"gap\"] < 0.3).sum()}/{len(rolling_df)}')\n"
    "rolling_df.to_csv(CRYPTO_DIR / 'crypto_pit_rolling_folds.csv', index=False, encoding='utf-8-sig')\n"
    "print('저장 완료: crypto_pit_rolling_folds.csv')"
)
new_cells.append(md_cell(
    "### C-2. 롤링 검증/테스트 재분할 (재학습 없음, 6개월 블록 4개 fold)\n\n"
    "§B-9의 1개 관측치(valid=2024 전체, test=2025-2026 전체, 격차 1.73)를 6개월 단위로 "
    "잘게 쪼갠 4개의 독립적인 (valid,test) fold로 확장한다. 각 fold는 여전히 "
    "\"valid에서만 선택 → test 1회 평가\" 원칙을 지킨다."
))
new_cells.append(code_cell(rolling_src))

# ============================================================
# §C-3 다양성 진단
# ============================================================
diversity_src = (
    "# v3(§4.3)에서 확인된 패턴 — Q-teacher 없이 우선순위 샘플링만으로는 45차원(여기선 13차원)\n"
    "# 연속 행동공간에서 다양성이 만들어지지 않고 4개 β가 사실상 클론으로 수렴할 수 있음 —\n"
    "# 이게 이 축소 유니버스에서도 재발했는지 비중 궤적 페어와이즈 상관으로 확인한다.\n"
    "# 평가 구간은 테스트 블록 전체(2025-01~2026-08) — 실패가 관측된 바로 그 구간에서\n"
    "# 정책들이 실제로 서로 달랐는지를 본다.\n\n"
    "def collect_weight_trajectory(model, buckets):\n"
    "    env = CryptoPortfolioEnv(buckets, **env_kwargs)\n"
    "    obs, _ = env.reset()\n"
    "    weights = [env.weights.copy()]\n"
    "    done = False\n"
    "    while not done:\n"
    "        action, _ = model.predict(obs, deterministic=True)\n"
    "        obs, _, done, _, info = env.step(action)\n"
    "        weights.append(env.weights.copy())\n"
    "    return np.array(weights)  # (T, n_assets)\n\n"
    "traj = {beta: collect_weight_trajectory(pool_models[beta], test_buckets) for beta in POOL_BETAS}\n\n"
    "corr_rows = []\n"
    "for i, b1 in enumerate(POOL_BETAS):\n"
    "    for b2 in POOL_BETAS[i + 1:]:\n"
    "        flat1, flat2 = traj[b1].ravel(), traj[b2].ravel()\n"
    "        corr = float(np.corrcoef(flat1, flat2)[0, 1])\n"
    "        corr_rows.append({'beta_pair': f'{b1} vs {b2}', 'weight_trajectory_corr': corr})\n\n"
    "corr_df = pd.DataFrame(corr_rows)\n"
    "print('4β 비중 궤적 페어와이즈 상관 (테스트구간 2025-2026, 1.0=완전 동일 정책)')\n"
    "print(corr_df.to_string(index=False))\n"
    "print()\n"
    "print(f'평균 상관: {corr_df[\"weight_trajectory_corr\"].mean():.3f}')\n"
    "print('참고 — v3(44종목, §4.3): 사실상 전면 붕괴(거의 클론)')\n"
    "print('참고 — v4(44종목, §4.4, 구조 개선 후): ρ 표준편차 0.068, β별 평균 ρ 0.109~0.545로 분리')\n"
    "print('참고 — KOSPI 축소판(§7): 0.22~0.51(β=30만 구별) / 극단쌍 0.955(거의 동일)')\n\n"
    "top10_by_beta = {\n"
    "    beta: set(\n"
    "        pd.Series(traj[beta].mean(axis=0)).nlargest(min(5, traj[beta].shape[1])).index\n"
    "    )\n"
    "    for beta in POOL_BETAS\n"
    "}\n"
    "print()\n"
    "print('β별 평균비중 상위 5종목(13종목 중 — 44종목 top-10과 스케일 다르므로 축소 비교):')\n"
    "# 주의: 비중 벡터의 인덱스 순서는 PIT_SYMBOLS(§A 정의 순서)가 아니라 §B에서\n"
    "# h5 임베딩 파일 기준으로 재정렬된 `symbols`(알파벳순)를 따른다 — 반드시 이걸로 매핑.\n"
    "for beta, top in top10_by_beta.items():\n"
    "    names = [symbols[idx] for idx in top]\n"
    "    print(f'  β={beta}: {names}')\n\n"
    "corr_df.to_csv(CRYPTO_DIR / 'crypto_pit_diversity_diag.csv', index=False, encoding='utf-8-sig')\n"
    "print('\\n저장 완료: crypto_pit_diversity_diag.csv')"
)
new_cells.append(md_cell(
    "### C-3. 다양성 진단 — 4β가 실제로 서로 다른 정책이었나 (v3 재발 여부 확인)"
))
new_cells.append(code_cell(diversity_src))

# ============================================================
# §C-4 판정 기준 메모
# ============================================================
new_cells.append(md_cell(
    "### C-4. 해석 가이드 (실행 후 이 기준으로 판단)\n\n"
    "**C-2(롤링 재분할) 결과 읽는 법**:\n"
    "- 4개 fold의 격차가 전부 크다(예: 대부분 >0.5) → §B의 실패가 2024→2025 특정 조합의 "
    "우연이 아니라 이 방법론(Q-teacher 없는 β-풀+valid 선택)의 일반적 취약성이라는 근거 강화.\n"
    "- 일부 fold는 격차가 작다(<0.3) → 어떤 국면 전환은 견디고 어떤 전환(특히 강세→급락 "
    "같은 극단적 반전)은 못 견딘다는, 더 세밀한 조건부 결론으로 좁혀짐 — 이 경우 어떤 "
    "fold가 실패했는지(전환 방향·낙폭 등)를 §7 새 절에 구체적으로 적어야 함.\n\n"
    "**C-3(다양성 진단) 결과 읽는 법**:\n"
    "- 페어와이즈 상관이 v3처럼 사실상 1에 가깝다 → 애초에 4개가 클론이었으니 §B의 "
    "\"β 선택\"은 사실상 무의미한 절차였다는 뜻 — 실패 원인이 \"walk-forward가 어려워서\"가 "
    "아니라 \"이번에도 다양성이 안 생겨서\"로 재해석돼야 함(§4.3 원인의 재확인).\n"
    "- 상관이 v4/KOSPI 수준으로 분리돼 있다(예: 평균 <0.7, β별로 다른 상위종목) → 4개는 "
    "진짜 서로 다른 정책이었는데도 전부 무너진 것 — 이러면 \"다양성 부재\" 가설로는 이번 "
    "실패를 설명할 수 없고, 순수하게 규제-없는 다년 일반화 실패로 봐야 함(더 근본적인 문제).\n\n"
    "두 결과를 종합해 §7 새 절과 8장 한계#5의 정확한 문구를 다시 정하는 게 다음 단계."
))

nb["cells"].extend(new_cells)

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"추가 완료: 신규 셀 {len(new_cells)}개, 전체 {len(nb['cells'])}개")
