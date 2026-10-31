"""
[운용 결정용 · 2026-10-31] 실계좌 β=30 정책의 위험자산 노출을 k배로 키우면 어떻게 되는가.

연구 판정이 아니다. 검증(2025 Q4)·테스트(2026 H1) 구간은 이미 여러 번 본 구간이고, 미지 구간(2026-07-14~10-26)은
규칙상 다시 쓰지 않는다. 결과는 실계좌 운용 선택의 참고 자료로만 쓰고 논문 주장에 쓰지 않는다.

입력: attribution_apply와 같은 Drive data/crypto/rt1006/policy_paths/ 폴더
      (meta.json, {valid,test}_market.npz, {valid,test}_beta30_{warmup,orig}.npz).

사전 고정(실행 전 커밋, 경로 파일을 받기 전):
  변환: 스텝 t의 정책 비중 W_t(스무딩 후, 합 x_t)를 W_t · min(k, 1/x_t)로 바꾼다. 종목 간 비율은 그대로, 합 ≤ 1.
        k ∈ {1, 1.5, 2, 3, 5}. 정책이 자기 보유를 입력으로 받는 되먹임은 무시한다(사후 배수).
  회계: attribution_apply.value_path 그대로(meta TC, Σ|w − 드리프트 보유|, 비용 후 30분 가치 경로).
  주 경로: 워밍업 경로(실계좌는 저장된 정책 상태로 이어 돌기 때문). 원본 경로(orig)는 2차로만 보고.
  지표: 비용 후 누적 수익, 로그 성장, MDD(30분 가치 경로), 평균 노출, 평균 회전율.
  선택 규칙(사용자 지정 MDD 한도 −25%):
    1. 검증 워밍업에서 MDD ≥ −25% 이고 로그 성장 ≥ k=1의 로그 성장인 k 중 가장 큰 k를 고른다. 없으면 k=1.
    2. 고른 k > 1이면 테스트 워밍업에서도 같은 두 조건을 확인한다. 하나라도 어기면 권고는 k=1(현행 유지).
    3. 권고는 "운용 선택 참고"다. 실계좌 반영은 사용자가 따로 결정한다.
  실행 전 예측(기록용): 기록된 검증 워밍업 수익이 −0.08%로 0에 가까워, k를 키워도 검증 로그 성장이 k=1 이상일
  가능성은 낮다(비용이 k배로 늘기 때문). 그러면 규칙상 권고는 k=1이다.

실행: python -m crypto.experiments.exposure_scale <policy_paths 폴더>
      → crypto/experiments/results/exposure_scale.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from crypto.experiments.attribution_apply import mdd, value_path

OUT = Path(__file__).resolve().parent / "results"
KS = (1, 1.5, 2, 3, 5)
MDD_LIMIT = -0.25
BETA = 30


def scale(W: np.ndarray, k: float) -> np.ndarray:
    x = W.sum(1, keepdims=True)
    return W * np.minimum(k, np.where(x > 0, 1 / np.maximum(x, 1e-12), k))


def turnover(W: np.ndarray, R: np.ndarray, init: np.ndarray | None) -> float:
    w_prev = np.zeros(W.shape[1]) if init is None else np.asarray(init, np.float64)
    tot = []
    for w, r in zip(W, R):
        tot.append(float(np.abs(w - w_prev).sum()))
        g = 1 + float(w @ r)
        w_prev = w * (1 + r) / g if g > 1e-12 else w
    return float(np.mean(tot))


def main(folder: str) -> None:
    d = Path(folder)
    tc = json.loads((d / "meta.json").read_text())["TC"]
    rows = []
    for split in ("valid", "test"):
        m = np.load(d / f"{split}_market.npz")
        R = m["R"].astype(np.float64)
        for kind in ("warmup", "orig"):
            z = np.load(d / f"{split}_beta{BETA}_{kind}.npz")
            W = z["W"].astype(np.float64)
            init = z["init"].astype(np.float64) if "init" in z else None
            for k in KS:
                Wk = scale(W, k)
                ik = None if init is None else scale(init[None], k)[0]
                v = value_path(Wk, R, tc, ik)
                rows.append({"구간": split, "경로": kind, "k": k, "평균 노출": Wk.sum(1).mean(),
                             "누적 수익": v[-1] - 1, "로그 성장": float(np.log(v[-1])), "MDD": mdd(v),
                             "평균 회전율": turnover(Wk, R, ik)})
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "exposure_scale.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 200)
    print(df.round(4).to_string(index=False))

    def ok(split: str, k: float) -> bool:
        t = df[(df.구간 == split) & (df.경로 == "warmup")].set_index("k")
        return bool(t.loc[k, "MDD"] >= MDD_LIMIT and t.loc[k, "로그 성장"] >= t.loc[1, "로그 성장"])

    sel = max([k for k in KS if ok("valid", k)], default=1)
    rec = sel if sel == 1 or ok("test", sel) else 1
    print(f"\n[사전 고정 규칙] 검증 선택 k = {sel}, 테스트 확인 후 권고 k = {rec}")


if __name__ == "__main__":
    main(sys.argv[1])
