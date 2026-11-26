# 목적 함수 수준 비용 감사 — 대조군 (notes/objective_cost_audit_prereg.md 3.0)
# 실행: PYTHONPATH=.t3env/pylib python3 replication/objective_audit/controls.py
# 손실 양성(μ를 정책 출력에서 그래프 안에서 계산) / 손실 결함(μ를 detach한 상수) / 보상 양성·결함.
import json, os
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
N, T, C = 5, 32, 0.01   # c_test 고정(사전 등록 3.2)


def synth_prices(n, t, seed=0):
    """자산 n개의 가격 상대(y_t = p_t / p_{t-1}), 로그정규, 고정 시드. 현금은 첫 칸 1."""
    rng = np.random.default_rng(seed)
    y = np.exp(rng.normal(0.0, 0.02, size=(t, n)))
    return np.concatenate([np.ones((t, 1)), y], axis=1)


class Policy(torch.nn.Module):
    def __init__(self, n, seed=0):
        super().__init__()
        torch.manual_seed(seed)
        self.net = torch.nn.Sequential(torch.nn.Linear(n + 1, 16), torch.nn.Tanh(), torch.nn.Linear(16, n + 1))

    def forward(self, x):
        return torch.softmax(self.net(x), dim=-1)


def mu_of(w_new, w_prev_drift, c):
    """PGPortfolio pure_pc의 선형 근사: μ = 1 − c·Σ|w_new − w'_prev| (현금 제외)."""
    return 1 - c * torch.sum(torch.abs(w_new[:, 1:] - w_prev_drift[:, 1:]), dim=1)


def loss(policy, y, c, detach_mu):
    """배치 = 연속 T 스텝. 입력은 직전 가격 상대, 출력 w_t. w'_{t-1} = 직전 출력이 y_{t-1}로 표류한 것."""
    x = torch.tensor(np.vstack([np.ones((1, y.shape[1])), y[:-1]]), dtype=torch.float32)
    yy = torch.tensor(y, dtype=torch.float32)
    w = policy(x)
    drift = w[:-1] * yy[:-1] / torch.sum(w[:-1] * yy[:-1], dim=1, keepdim=True)
    mu = mu_of(w[1:], drift, c)
    if detach_mu:
        mu = mu.detach()
    pv = torch.sum(w[1:] * yy[1:], dim=1) * mu
    return -torch.mean(torch.log(pv))


def grad_rel_diff(detach_mu):
    y = synth_prices(N, T, seed=1)
    gs = []
    for c in (C, 0.0):
        p = Policy(N, seed=0)
        p.zero_grad()
        loss(p, y, c, detach_mu).backward()
        gs.append(torch.cat([q.grad.flatten() for q in p.parameters()]))
    return float(torch.norm(gs[0] - gs[1]) / torch.norm(gs[1]))


def reward_seq(charge_in_reward, c):
    """S1 행동열: 등가중 → 1종목 집중 → 다른 1종목 집중 → 유지. 보상 = 학습 루프가 받는 값."""
    y = synth_prices(N, 5, seed=2)
    eq = np.r_[0.0, np.full(N, 1.0 / N)]
    a1 = np.zeros(N + 1); a1[1] = 1.0
    a2 = np.zeros(N + 1); a2[2] = 1.0
    acts = [eq, a1, a2, a2]
    w_prev, v, out = eq.copy(), 1.0, []
    for t, w in enumerate(acts):
        drift = w_prev * y[t] / np.dot(w_prev, y[t])
        turn = np.abs(w[1:] - drift[1:]).sum()
        gross = float(np.dot(w, y[t + 1]))
        cost = c * turn
        v *= gross * (1 - cost)
        r = np.log(gross * (1 - cost)) if charge_in_reward else np.log(gross)
        out.append((r, turn))
        w_prev = w
    return out


def reward_diff(charge_in_reward):
    a, b = reward_seq(charge_in_reward, C), reward_seq(charge_in_reward, 0.0)
    return max(abs(ra - rb) for (ra, ta), (rb, tb) in zip(a, b) if ta > 0)


res = {
    "loss_positive_rel_diff": grad_rel_diff(detach_mu=False),
    "loss_defect_rel_diff": grad_rel_diff(detach_mu=True),
    "reward_positive_max_diff": reward_diff(True),
    "reward_defect_max_diff": reward_diff(False),
}
res["expected"] = {k: bool(v) for k, v in {
    "loss_positive": res["loss_positive_rel_diff"] > 1e-3,
    "loss_defect": res["loss_defect_rel_diff"] <= 1e-4,
    "reward_positive": res["reward_positive_max_diff"] > 1e-12,
    "reward_defect": res["reward_defect_max_diff"] <= 1e-12,
}.items()}
res["all_ok"] = all(res["expected"].values())
json.dump(res, open(os.path.join(HERE, "controls_result.json"), "w"), indent=2)
print(json.dumps(res, indent=2))
