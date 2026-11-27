"""MARS 보상 항 크기 측정 (탐색적, 기술적 측정; 실행 전 커밋)

목적
  MARS 학습 보상 reward = return_component − total_monetary_transaction_cost_for_step
  − risk_penalty (출판판 L @2561606 main.py 348행, 저자 수정본 N @6ca2051 main.py 363행)에서
  return_component는 비율, 비용 항은 달러(초기 자본 1e6)다. 학습 데이터·환경에서
  두 항의 상대 크기를 실제 행동 하에서 잰다. 성과(수익·샤프)에 대해서는 아무것도 말하지 않는다.

측정 규칙 (결과를 본 뒤 바꾸지 않는다)
  1. 환경: .marswork/L, .marswork/N의 수정하지 않은 main.run_episode를 그대로 호출한다.
     데이터는 각 저장소의 data/training_data.csv(번들, 2018-01-02~2022-12-30, 50종목),
     config 그대로(TRANSACTION_COST = 0.001, INITIAL_BALANCE = 1e6, MAX_TRADE_SIZE = 150).
     바꾸는 것: config.RESULT_DIR을 임시 폴더로, utils.log_trade·utils.log_daily_performance를
     메모리 기록 함수로 바꾼다(파일 쓰기 대신; 거래비용 값을 읽는 데 씀). N은 학습 모드에서
     log_trade를 부르지 않으므로 저자가 둔 getattr 플래그 config.LOG_TRAINING_DETAIL = True로 켠다.
     보상 계산 경로는 건드리지 않는다. 보상은 run_episode(train=True, batch_size=0,
     populate_meta_buffer=False)가 replay_buffer.add에 넣는 값을 가로채 읽는다(갱신 없음).
  2. 행동 정책 (MARS 행동 = 종목별 [-1,1], 150주 곱해 반올림한 주식 수 거래):
     (a) 매 스텝 동일가중 목표: 목표 주식 수 = (1/50)·PV/가격, 행동 = clip((목표 − 보유)/150, −1, 1).
     (b) 매 스텝 Dirichlet(1) 목표 비중(시드 20261127), 같은 변환.
     (c) data/mars_t4/L/seed_*/ 아래 우리 O1 실행의 학습된 체크포인트(.pth)가 있으면 그 결정적 행동.
         없으면 "없음"으로 기록하고 실행하지 않는다(학습하지 않는다).
     (d) [추가, 사전 고정] 원시 행동 U(−1,1) 종목별 독립(시드 20261128) — 탐색 초기 행동 대용.
     (e) [추가, 사전 고정] N에 들어 있는 저자 공개 체크포인트 checkpoints/dji2024_seed123_ep130의
         결정적 행동(explore=False), N 환경에서만. 실제 MultiAgentSystem을 쓰므로 안전 벌점
         (unsafe → −SAFETY_WEIGHTS[0] = −20)이 생길 수 있다; 별도로 기록한다.
     (a)(b)(d)는 is_action_unsafe = False인 대체 행동 공급자를 쓴다(안전 벌점 0).
  3. 스텝별 기록: return_component = PV_t/PV_{t−1} − 1(run_episode가 돌려준 portfolio_values),
     cost = 그 스텝 log_trade 기록의 (balance_before − balance_after − 주식수·가격) 합(달러),
     risk_penalty = 가로챈 reward로부터 잔차 return − cost − 안전벌점 − reward, 그리고
     같은 식(0.5·변동성 + 2·최대낙폭, 31개 값 창)을 독립 재계산해 둘이 맞는지 확인,
     reward = 가로챈 값. 검사: |reward − (ret − cost − risk − 20·unsafe)| ≤ 1e−6·max(1, |reward|).
  4. 보고(L, N 각각, 정책별): |cost|/|return|의 중앙값·90분위, |cost| > |return| 스텝 비율,
     |cost| > |return| + risk 스텝 비율, cost > 0 스텝 비율, |return|·cost·risk·|reward| 중앙값,
     비교용으로 단위를 맞춘 cost/PV_{t−1} 의 |return| 대비 중앙값(탐색적 반사실, MARS 코드가 아님).
     return = 0인 스텝의 비율은 inf로 두고 중앙값·분위에 그대로 넣는다.
  5. 실행: CPU, torch.set_num_threads(2), OMP_NUM_THREADS=2. 임시 파일은 스크래치 폴더.
     결과 요약은 replication/mars_reward_scale.json.
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = "/private/tmp/claude-501/-Users-seungbin-school-4-1-------/e9f6f6e8-2d56-4c96-a326-738b6cf12ec5/scratchpad/mars_scale"
OUT_JSON = os.path.join(ROOT, "replication", "mars_reward_scale.json")
SEED_DIRICHLET = 20261127
SEED_UNIFORM = 20261128


def find_o1_checkpoints():
    base = os.path.join(ROOT, "data", "mars_t4", "L")
    found = []
    if os.path.isdir(base):
        for d in sorted(os.listdir(base)):
            if not d.startswith("seed_"):
                continue
            for dp, _, fns in os.walk(os.path.join(base, d)):
                for fn in fns:
                    if fn.endswith(".pth") or fn.endswith(".pt"):
                        found.append(os.path.relpath(os.path.join(dp, fn), ROOT))
    return found


def summarize(ret, cost, risk, reward, unsafe, pv_prev):
    import numpy as np
    ret = np.asarray(ret, float); cost = np.asarray(cost, float)
    risk = np.asarray(risk, float); reward = np.asarray(reward, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(np.abs(ret) > 0, np.abs(cost) / np.abs(ret),
                         np.where(np.abs(cost) > 0, np.inf, np.nan))
        ratio_frac = np.where(np.abs(ret) > 0, (np.abs(cost) / pv_prev) / np.abs(ret), np.nan)
    pos = cost > 0
    r_valid = ratio[~np.isnan(ratio)]

    def q(x, p):
        x = x[~np.isnan(x)]
        return float(np.quantile(x, p)) if len(x) else None

    return {
        "n_steps": int(len(ret)),
        "ratio_cost_over_return_median": q(r_valid, 0.5),
        "ratio_cost_over_return_p90": q(r_valid, 0.9),
        "ratio_cost_over_return_median_costpos_steps": q(ratio[pos], 0.5),
        "share_cost_gt_return": float(np.mean(np.abs(cost) > np.abs(ret))),
        "share_cost_gt_return_plus_risk": float(np.mean(np.abs(cost) > np.abs(ret) + np.abs(risk))),
        "share_cost_positive": float(np.mean(pos)),
        "median_abs_return": float(np.median(np.abs(ret))),
        "median_cost_dollars": float(np.median(cost)),
        "median_cost_dollars_costpos_steps": float(np.median(cost[pos])) if pos.any() else None,
        "median_risk_penalty": float(np.median(risk)),
        "median_abs_reward": float(np.median(np.abs(reward))),
        "share_unsafe": float(np.mean(unsafe)),
        "unit_consistent_counterfactual_ratio_median": q(ratio_frac, 0.5),
        "unit_consistent_counterfactual_ratio_p90": q(ratio_frac, 0.9),
    }


def worker(version, policy):
    os.environ.setdefault("MPLBACKEND", "Agg")
    import numpy as np
    import torch
    torch.set_num_threads(2)
    repo = os.path.join(ROOT, ".marswork", version)
    os.chdir(repo)
    sys.path.insert(0, repo)
    import config
    import utils
    import main as marsmain

    resdir = os.path.join(SCRATCH, f"res_{version}_{policy}")
    os.makedirs(resdir, exist_ok=True)
    config.RESULT_DIR = resdir
    config.LOG_TRAINING_DETAIL = True  # N only reads it via getattr; L ignores it
    np.random.seed(config.SEED)
    torch.manual_seed(config.SEED)

    data = utils.load_stock_data(config.TRAINING_DATA_PATH)
    pcols = [c for c in data.columns if c.endswith('_Adj Close')]
    prices_df = data[pcols]
    tick2i = {c.split('_')[0]: i for i, c in enumerate(pcols)}
    returns_history = utils.calculate_returns(prices_df)
    n = config.NUM_STOCKS

    st = {"holdings": np.zeros(n), "balance": float(config.INITIAL_BALANCE), "cost_by_date": {}}

    def log_trade(log_dir, timestamp, ticker, action, price, cost, holdings_before,
                  holdings_after, balance_before, balance_after, portfolio_value):
        st["holdings"][tick2i[ticker]] = holdings_after
        st["balance"] = balance_after
        c = balance_before - balance_after - action * price
        st["cost_by_date"][timestamp] = st["cost_by_date"].get(timestamp, 0.0) + c

    utils.log_trade = log_trade
    utils.log_daily_performance = lambda *a, **k: None

    captured = {"reward": [], "unsafe": []}

    class Buf:
        def add(self, **kw):
            captured["reward"].append(float(kw["reward"]))
            captured["unsafe"].append(bool(kw["unsafe"]))

    class CapAgent:
        def __init__(self):
            self.replay_buffer = Buf()

    rng_d = np.random.default_rng(SEED_DIRICHLET)
    rng_u = np.random.default_rng(SEED_UNIFORM)

    class StubPolicy:
        def __init__(self, kind):
            self.kind = kind
            self.k = 0
            self.agents = [CapAgent()]
            self.agent_weights = np.ones(config.NUM_AGENTS) / config.NUM_AGENTS

        def update_agent_weights(self, state=None):
            pass

        def is_action_unsafe(self, state, action, returns_history=None):
            return False

        def select_action(self, state, explore=True, returns_history=None):
            t = self.k + 1
            self.k += 1
            if self.kind == "uniform":
                return rng_u.uniform(-1, 1, size=n)
            p = prices_df.iloc[t - 1].values.astype(float)
            pv = st["balance"] + float(np.sum(st["holdings"] * p))
            w = np.ones(n) / n if self.kind == "equal" else rng_d.dirichlet(np.ones(n))
            target = w * pv / p
            return np.clip((target - st["holdings"]) / config.MAX_TRADE_SIZE, -1, 1)

    class CkptPolicy:
        def __init__(self, path):
            from multi_agent import MultiAgentSystem
            state_dim = 1 + n * 6
            self.mas = MultiAgentSystem(state_dim, n, device="cpu")
            self.mas.load_models(path)
            self.agents = [CapAgent()]

        @property
        def agent_weights(self):
            return self.mas.agent_weights

        def update_agent_weights(self, state=None):
            self.mas.update_agent_weights(state)

        def is_action_unsafe(self, state, action, returns_history=None):
            return self.mas.is_action_unsafe(state, action, returns_history)

        def select_action(self, state, explore=True, returns_history=None):
            return self.mas.select_action(state, explore=False, returns_history=returns_history)

    if policy == "checkpoint_author_N":
        ma = CkptPolicy(config.RELEASED_CHECKPOINT_PATH)
    else:
        ma = StubPolicy(policy)

    t0 = time.time()
    out = marsmain.run_episode(multi_agent=ma, data=data, returns_history=returns_history,
                               train=True, batch_size=0, populate_meta_buffer=False)
    elapsed = time.time() - t0

    pv = np.asarray(out["portfolio_values"], float)
    T = len(data)
    assert len(pv) == T and len(captured["reward"]) == T - 1, (len(pv), len(captured["reward"]))
    ret = pv[1:] / pv[:-1] - 1
    cost = np.array([st["cost_by_date"].get(prices_df.index[t].strftime('%Y-%m-%d'), 0.0)
                     for t in range(1, T)])
    reward = np.array(captured["reward"])
    unsafe = np.array(captured["unsafe"], float)
    sw = config.SAFETY_WEIGHTS[0]
    risk_resid = ret - cost - sw * unsafe - reward
    vw = getattr(config, "REWARD_VOL_WEIGHT", 0.5)
    dw = getattr(config, "REWARD_DD_WEIGHT", 2.0)
    risk_re = np.zeros(T - 1)
    for t in range(1, T):
        k = t + 1  # len(portfolio_values) after append
        if k > 30:
            vals = pv[k - 31:k]
            rr = np.diff(vals) / vals[:-1]
            vol = np.std(rr) * np.sqrt(252)
            peak = np.maximum.accumulate(vals)
            risk_re[t - 1] = vw * vol + dw * np.max((peak - vals) / peak)
    chk = np.abs(risk_resid - risk_re) / np.maximum(1.0, np.abs(reward))
    res = {
        "version": version, "policy": policy, "seconds": elapsed,
        "check_max_rel_err": float(np.max(chk)),
        "check_pass": bool(np.max(chk) <= 1e-6),
        "final_pv": float(pv[-1]),
        "summary": summarize(ret, cost, risk_re, reward, unsafe, pv[:-1]),
    }
    np.savez_compressed(os.path.join(SCRATCH, f"steps_{version}_{policy}.npz"),
                        ret=ret, cost=cost, risk=risk_re, reward=reward, unsafe=unsafe, pv=pv)
    print("RESULT_JSON " + json.dumps(res))


def run_all():
    os.makedirs(SCRATCH, exist_ok=True)
    ckpts = find_o1_checkpoints()
    env = dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", MPLBACKEND="Agg")
    jobs = [(v, p) for v in ("L", "N") for p in ("equal", "dirichlet", "uniform")]
    jobs.append(("N", "checkpoint_author_N"))
    results = []
    for v, p in jobs:
        print(f"[run] {v} {p}", flush=True)
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--worker", v, p],
                           env=env, capture_output=True, text=True)
        line = [x for x in r.stdout.splitlines() if x.startswith("RESULT_JSON ")]
        if r.returncode != 0 or not line:
            results.append({"version": v, "policy": p, "error": r.stderr[-3000:]})
            print(r.stderr[-3000:], flush=True)
        else:
            results.append(json.loads(line[0][len("RESULT_JSON "):]))
            print(json.dumps(results[-1]["summary"], indent=1), flush=True)

    def head(path):
        try:
            return subprocess.run(["git", "-C", path, "rev-parse", "HEAD"], capture_output=True,
                                  text=True).stdout.strip()
        except Exception:
            return None

    def dirty(path):
        return subprocess.run(["git", "-C", path, "status", "--porcelain", "--untracked-files=no"],
                              capture_output=True, text=True).stdout.strip()

    meta = {
        "label": "exploratory, descriptive; says nothing about performance",
        "mars_L_head": head(os.path.join(ROOT, ".marswork", "L")),
        "mars_N_head": head(os.path.join(ROOT, ".marswork", "N")),
        "mars_L_tracked_changes": dirty(os.path.join(ROOT, ".marswork", "L")),
        "mars_N_tracked_changes": dirty(os.path.join(ROOT, ".marswork", "N")),
        "o1_checkpoints_found": ckpts,
        "policy_c_status": "found; not run by this script (checked absent before commit)" if ckpts else "not run: no checkpoint files under data/mars_t4/L/seed_*/",
        "seeds": {"dirichlet": SEED_DIRICHLET, "uniform": SEED_UNIFORM},
        "data": "training_data.csv bundled in each repo, 2018-01-02..2022-12-30, 50 stocks",
    }
    with open(OUT_JSON, "w") as f:
        json.dump({"meta": meta, "results": results}, f, indent=1)
    print("wrote", OUT_JSON)


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--worker":
        worker(sys.argv[2], sys.argv[3])
    else:
        run_all()
