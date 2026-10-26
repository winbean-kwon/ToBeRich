"""
[방법론 2 · 통제 실험 · 2026-10-26] 라우터 붕괴를 학습 전에 예측할 수 있는가 — 전문가 구성을 체계적으로 바꾼 전향적 검증.

배경: 기존 진단(router_diagnostic.py)의 D1 분리도는 이미 관측된 8개 사례에서 붕괴를 구분하지 못했다(사전 가설 기각).
그 8개는 모두 '라우터가 쓸모없는' 쪽에 몰려 있어 어떤 지표도 검증하기 어렵다. 그래서 전문가 구성을 통제해 새 사례를 만들고,
아래 지표와 판정 기준을 실행 전에 고정한 뒤 검증한다(결과를 본 뒤 지표를 바꾸지 않는다).

사전 등록:
  사례: CONFIGS 16개 × 라우터 입력 2종(가치 이력 = 기존 방식 / 정보) × 시드 3개. 하이퍼파라미터는 factor_router_pit와 동일.
  붕괴: 검증·테스트 평균 '한 전문가 선택 비율' ≥ 0.9.
  지표(학습 구간 일간 전문가 수익만으로 계산, 라우터 학습 없음)와 예상 방향:
    P1 D1 분리도(상대)            — 낮을수록 붕괴
    P2 전문가 간 평균 상관(현금은 0) — 높을수록 붕괴
    P3 절대 분산 = 평균_t std_e r   — 낮을수록 붕괴
    P4 최고 전문가 우위 t값          — 높을수록 붕괴(한 전문가가 꾸준히 최고면 고정 선택이 합리적)
  검증 기준: 붕괴·비붕괴 각각 4개 이상일 때 예상 방향의 AUC ≥ 0.8.

실행: python -m crypto.experiments.router_collapse_study  (저장소 루트)
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from stable_baselines3 import DQN

from crypto.experiments import factor_router_pit as F
from crypto.experiments.router_diagnostic import separation

SEEDS = [0, 1, 2]
CONFIGS = {
    "S01 등가중 노출 10/20/50/100": ["EW10", "EW20", "EW50", "EW100"],
    "S02 등가중 85/90/95/100 (거의 동일)": ["EW85", "EW90", "EW95", "EW100"],
    "S03 BTC 85/90/95/100 (거의 동일)": ["BTC85", "BTC90", "BTC95", "BTC100"],
    "S04 저노출 혼합(β 풀 유사)": ["EW10", "LV30", "BTC30", "EW20"],
    "S05 저노출 + 현금": ["EW10", "LV30", "BTC30", "CASH"],
    "S06 저변동성/등가중/BTC/모멘텀": ["LV100", "EW100", "BTC100", "MOM100"],
    "S07 팩터 + 현금(기존 실험)": ["MOM100", "LV100", "EW100", "CASH"],
    "S08 모멘텀/반전/저변동성/등가중": ["MOM100", "REV100", "LV100", "EW100"],
    "S09 모멘텀/반전/현금/등가중10": ["MOM100", "REV100", "CASH", "EW10"],
    "S10 BTC/ETH/등가중/저변동성": ["BTC100", "ETH100", "EW100", "LV100"],
    "S11 등가중100/50 + 현금 + 저변동성": ["EW100", "EW50", "CASH", "LV100"],
    "S12 모멘텀·반전 각 100/50": ["MOM100", "MOM50", "REV100", "REV50"],
    "S13 BTC/BTC30/등가중/현금": ["BTC100", "BTC30", "EW100", "CASH"],
    "S14 BTC/ETH 각 100/50": ["BTC100", "BTC50", "ETH100", "ETH50"],
    "S15 저변동성 100/70/40/10": ["LV100", "LV70", "LV40", "LV10"],
    "S16 반전/저변동성/BTC/현금": ["REV100", "LV100", "BTC100", "CASH"],
}


def library(C, V):
    """전문가 이름 → (T, N) 목표 비중. 매일 UTC 0시, t까지의 정보만 사용."""
    W3, Rn = F.expert_weights(C, V)          # 0: 7일 모멘텀, 1: 저변동성, 2: 등가중
    R = C.shift(-1) / C - 1
    rev = -(C / C.shift(1) - 1)
    T, N = W3.shape[1], W3.shape[2]
    rev_w = np.zeros((T, N))
    for i, t in enumerate(C.index):
        ok = (R.loc[t].notna() & C.loc[t].notna())
        sc = rev.loc[t].where(ok).dropna()
        if len(sc) >= F.K:
            rev_w[i, [F.SYMS.index(s) for s in sc.sort_values().index[-F.K:]]] = 1 / F.K

    def single(sym):
        w = np.zeros((T, N)); j = F.SYMS.index(sym)
        w[:, j] = R[sym].notna().to_numpy().astype(float)
        return w

    base = {"EW": W3[2], "LV": W3[1], "MOM": W3[0], "REV": rev_w, "BTC": single("BTCUSDT"), "ETH": single("ETHUSDT")}
    lib = {"CASH": np.zeros((T, N))}
    for name, w in base.items():
        for k in (10, 20, 30, 40, 50, 70, 85, 90, 95, 100):
            lib[f"{name}{k}"] = w * k / 100
    return lib, Rn


def predictors(Rtr: np.ndarray) -> dict:
    """학습 구간 일간 전문가 수익 (T, E) → 사전 등록 지표 4개."""
    E = Rtr.shape[1]
    sd = Rtr.std(axis=0)
    cs = []
    for i in range(E):
        for j in range(i + 1, E):
            cs.append(0.0 if sd[i] < 1e-12 or sd[j] < 1e-12 else float(np.corrcoef(Rtr[:, i], Rtr[:, j])[0, 1]))
    best = int(Rtr.mean(axis=0).argmax())
    adv = Rtr[:, best] - np.delete(Rtr, best, axis=1).mean(axis=1)
    return {"P1 D1 분리도": separation(Rtr), "P2 평균 상관": float(np.mean(cs)),
            "P3 절대 분산": float(Rtr.std(axis=1).mean()), "P4 최고 우위 t": float(adv.mean() / (adv.std() / np.sqrt(len(adv)) + 1e-12))}


def auc(score: np.ndarray, label: np.ndarray) -> float:
    pos, neg = score[label == 1], score[label == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    return float(np.mean([(p > n) + 0.5 * (p == n) for p in pos for n in neg]))


def main():
    C, V = F.load_daily()
    lib, Rn = library(C, V)
    days = np.arange(len(C) - 1)
    idx = {k: np.array([i for i in days if a <= str(C.index[i].date()) <= b]) for k, (a, b) in F.SPLITS.items()}
    rows = []
    for cname, members in CONFIGS.items():
        W = np.stack([lib[m] for m in members])
        alone = np.stack([F.simulate(W, Rn, np.full(len(days), j), days) for j in range(len(members))], axis=1)
        Xdf = F.features(C, np.vstack([alone, np.zeros((1, len(members)))]))
        ok = Xdf.notna().all(axis=1).to_numpy()
        sp = {k: v[ok[v]] for k, v in idx.items()}
        mu, sd = Xdf.iloc[sp["train"]].mean(), Xdf.iloc[sp["train"]].std() + 1e-9
        X = ((Xdf - mu) / sd).fillna(0.0).to_numpy(np.float32)
        pred = predictors(alone[sp["train"]])
        for mode in ("nav", "info"):
            shares = []
            for seed in SEEDS:
                env = F.RouterEnv(W, Rn, X, sp["train"], mode, np.random.default_rng(seed))
                model = DQN("MlpPolicy", env, learning_rate=1e-3, buffer_size=50_000, learning_starts=1_000, batch_size=64,
                            gamma=0.9, train_freq=1, target_update_interval=500, exploration_fraction=0.3,
                            exploration_final_eps=0.05, policy_kwargs=dict(net_arch=[64, 64]), seed=seed, verbose=0, device="cpu")
                model.learn(F.TOTAL_STEPS)
                for split in ("valid", "test"):
                    ch = F.run_router(model, W, Rn, X, sp[split], mode)
                    shares.append(np.bincount(ch, minlength=len(members)).max() / len(ch))
            rows.append({"설정": cname, "라우터 입력": mode, **pred, "최빈 선택 비율": float(np.mean(shares)),
                         "붕괴": int(np.mean(shares) >= 0.9)})
            print(f"{cname} [{mode}] 최빈 {np.mean(shares):.2f} | " + ", ".join(f"{k} {v:+.3f}" for k, v in pred.items()), flush=True)

    res = pd.DataFrame(rows)
    out = F.OUT / "router_collapse_study.csv"
    res.to_csv(out, index=False, encoding="utf-8-sig")
    direction = {"P1 D1 분리도": -1, "P2 평균 상관": 1, "P3 절대 분산": -1, "P4 최고 우위 t": 1}
    print(f"\n붕괴 {int(res['붕괴'].sum())}건 / 비붕괴 {int((1 - res['붕괴']).sum())}건 (총 {len(res)})")
    for mode in ("nav", "info", "all"):
        d = res if mode == "all" else res[res["라우터 입력"] == mode]
        y = d["붕괴"].to_numpy()
        msg = [f"{k}: AUC {auc(s * d[k].to_numpy(), y):.2f}, 순위상관 {pd.Series(s * d[k]).corr(d['최빈 선택 비율'], method='spearman'):+.2f}"
               for k, s in direction.items()]
        valid = (y.sum() >= 4) and ((1 - y).sum() >= 4)
        print(f"[{mode}] 붕괴 {y.sum()}/{len(y)} {'(판정 가능)' if valid else '(사례 불균형 — 판정 불가)'} | " + " | ".join(msg))
    print("저장:", out)


if __name__ == "__main__":
    sys.exit(main())
