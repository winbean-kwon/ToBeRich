# 대조군 env 두 개 — notes/prereg_code_audit.md 2.0
import numpy as np


def softmax(x):
    e = np.exp(x - x.max()); return e / e.sum()


class RefEnv:
    """양성 정상: 현금 칸 포함, 무경계 logits softmax, 참조 명세대로 c·τ(현금 제외)."""
    def __init__(self, c, Y, bounded=False, charge=True):
        self.c, self.Y, self.bounded, self.charge = c, Y, bounded, charge
        self.t, self.V = 0, 1.0
        self.w_d = np.zeros(Y.shape[1] + 1); self.w_d[0] = 1.0   # 현금 시작

    def to_weights(self, a):
        a = np.asarray(a, float)
        return softmax(np.tanh(a)) if self.bounded else softmax(a)

    def step(self, a):
        w = self.to_weights(a)
        tau = np.abs(w[1:] - self.w_d[1:]).sum()
        cost = self.c * tau if self.charge else 0.0
        y = np.concatenate([[1.0], self.Y[self.t]])
        g = (1 - cost) * (w @ y)
        V0, self.V = self.V, self.V * g
        self.w_d = w * y / (w @ y); self.t += 1
        return {'reward': np.log(self.V / V0), 'value': self.V, 'w_exec': w, 'y': y}


def defect_env(c, Y):
    """결함: 비용 인자를 받지만 쓰지 않고, tanh 뒤 softmax."""
    return RefEnv(c, Y, bounded=True, charge=False)


class LagEnv(RefEnv):
    """보조 대조군: 비용을 다음 스텝 가치에서 뗀다(1스텝 지연)."""
    pending = 0.0

    def step(self, a):
        w = self.to_weights(a)
        cost_now, self.pending = self.pending, self.c * np.abs(w[1:] - self.w_d[1:]).sum()
        y = np.concatenate([[1.0], self.Y[self.t]])
        V0, self.V = self.V, self.V * (1 - cost_now) * (w @ y)
        self.w_d = w * y / (w @ y); self.t += 1
        return {'reward': np.log(self.V / V0), 'value': self.V, 'w_exec': w, 'y': y}
