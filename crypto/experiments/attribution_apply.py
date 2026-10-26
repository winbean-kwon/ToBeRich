"""
[방법론 1 적용 · 2026-10-26] 내보낸 β 정책 경로에 층별 추론을 적용하고, 같은 노출 비교·MDD를 재현한다.

입력: Colab 노트북 crypto_policy_paths_export_rt1006 이 Drive data/crypto/rt1006/policy_paths/ 에 저장한 npz
      ({valid,test}_beta{β}_{orig,warmup}.npz, {valid,test}_market.npz, meta.json)를 내려받은 폴더.

사전 등록(실행 전 커밋, 경로 파일을 받기 전에 고정):
  대상: 워밍업 경로(평가 시작 상태 편향을 뺀 것). β 4개 × 검증·테스트 = 8개.
  층: attribution_inference.layers — 정적 노출, 노출 타이밍, 종목 선택(+ 선택 먼저 순서, Shapley, 상호작용).
  추론: 위약 999개 단측 p, 같은 (구간, β) 안의 두 층(타이밍·선택)에 Holm 보정. 1주 블록 bootstrap 2,000회 95% 구간.
  주 검정은 하나: 테스트 β=30(배포 정책)의 종목 선택 층과 노출 타이밍 층. 나머지 7개는 기술 통계로만 보고.
  판정: Holm 보정 p < 0.05 이면 그 층을 '위약과 구분됨', 아니면 '위약과 구분되지 않음'.
  같은 노출 비교(감사에서 재현 불가였던 수치): 정책(비용 후) vs BTC를 정책 노출 경로 x_t로 보유 vs 거래 가능 등가중을
  x_t로 보유. 두 비교 대상 모두 같은 수수료(meta TC)와 같은 회전율 계산. 누적 수익과 MDD(30분 가치 경로)를 보고.

실행: python -m crypto.experiments.attribution_apply <policy_paths 폴더>
      → crypto/experiments/results/attribution_apply.csv, attribution_exposure_matched.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from crypto.experiments.attribution import basket_weights
from crypto.experiments.attribution_inference import block_bootstrap_ci, holm, layers, placebo_null, placebo_p

OUT = Path(__file__).resolve().parent / "results"
N_PLACEBO, N_BOOT = 999, 2000


def value_path(W: np.ndarray, R: np.ndarray, tc: float, init: np.ndarray | None = None) -> np.ndarray:
    """비용 후 가치 경로(시작 1). attribution.portfolio_log_growth 와 같은 회계."""
    w_prev = np.zeros(W.shape[1]) if init is None else np.asarray(init, np.float64)
    v, out = 1.0, [1.0]
    for w, r in zip(W, R):
        pr = float(w @ r)
        v *= 1 + pr - tc * float(np.abs(w - w_prev).sum())
        out.append(v)
        g = 1 + pr
        w_prev = w * (1 + r) / g if g > 1e-12 else w
    return np.asarray(out)


def mdd(v: np.ndarray) -> float:
    return float((v / np.maximum.accumulate(v) - 1).min())


def main(folder: str) -> None:
    d = Path(folder)
    meta = json.loads((d / "meta.json").read_text())
    tc, syms = meta["TC"], meta["symbols"]
    btc = next(i for i, s in enumerate(syms) if s.replace("/", "").upper() in ("BTC", "BTCUSDT"))
    rows, exp_rows = [], []
    for split in ("valid", "test"):
        m = np.load(d / f"{split}_market.npz")
        R, T = m["R"].astype(np.float64), m["T"].astype(bool)
        for beta in meta["BETAS"]:
            z = np.load(d / f"{split}_beta{beta}_warmup.npz")
            W, init = z["W"].astype(np.float64), z["init"].astype(np.float64)
            L = layers(W, R, T)
            null = placebo_null(W, R, T, n=N_PLACEBO, seed=0)
            p = {k: placebo_p(L[k], null[k]) for k in ("노출 타이밍", "종목 선택")}
            ph = holm(p)
            ci = block_bootstrap_ci(W, R, T, n=N_BOOT)
            primary = split == "test" and beta == 30
            for k, v in L.items():
                row = {"구간": split, "β": beta, "층": k, "로그%p": v * 100, "주 검정": primary}
                if k in p:
                    row.update({"위약 p": p[k], "Holm p": ph[k], "위약 평균 로그%p": null[k].mean() * 100,
                                "위약 95% 상단 로그%p": np.quantile(null[k], 0.95) * 100,
                                "판정": "위약과 구분됨" if ph[k] < 0.05 else "위약과 구분되지 않음"})
                if k in ci:
                    row.update({"bootstrap 하한": ci[k][0] * 100, "bootstrap 상한": ci[k][1] * 100})
                rows.append(row)

            x = W.sum(1)
            Wb = np.zeros_like(W)
            Wb[:, btc] = x * T[:, btc]
            vp = value_path(W, R, tc, init)
            vb = value_path(Wb, R, tc)
            ve = value_path(basket_weights(R, T, x), R, tc)
            exp_rows.append({"구간": split, "β": beta, "평균 노출": x.mean(),
                             "정책 수익": vp[-1] - 1, "같은 노출 BTC": vb[-1] - 1, "같은 노출 등가중": ve[-1] - 1,
                             "정책 − BTC %p": (vp[-1] - vb[-1]) * 100, "정책 − 등가중 %p": (vp[-1] - ve[-1]) * 100,
                             "정책 MDD": mdd(vp), "BTC MDD": mdd(vb), "등가중 MDD": mdd(ve),
                             "기록된 워밍업 수익": float(z["ret"])})
            print(f"{split} β={beta}: 타이밍 {L['노출 타이밍']*100:+.2f} (p {p['노출 타이밍']:.3f}) | "
                  f"선택 {L['종목 선택']*100:+.2f} (p {p['종목 선택']:.3f}) | 정책 {vp[-1]-1:+.2%} "
                  f"BTC {vb[-1]-1:+.2%} 등가중 {ve[-1]-1:+.2%}", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    res, ex = pd.DataFrame(rows), pd.DataFrame(exp_rows)
    res.to_csv(OUT / "attribution_apply.csv", index=False, encoding="utf-8-sig")
    ex.to_csv(OUT / "attribution_exposure_matched.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 240)
    print(ex.round(4).to_string(index=False))
    prim = res[res["주 검정"] & res["층"].isin(["노출 타이밍", "종목 선택"])]
    print("\n[사전 등록 주 검정 — 테스트 β=30]")
    print(prim[["층", "로그%p", "위약 p", "Holm p", "bootstrap 하한", "bootstrap 상한", "판정"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1])
