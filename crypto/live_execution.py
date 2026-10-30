"""
정책 목표 비중 → 최소주문금액 아래에서도 실제로 주문 가능한 목표 금액(실행 목표).

소액 운용(약 330 USDT, 목표 위험자산 비중 약 10%)에서는 정책이 44종목에 2~3 USDT씩 나눠 담으라고 하는데,
바이낸스 최소주문금액(5 USDT) 때문에 신규 매수는 하나도 나가지 못하고, 목표가 줄어든 보유 종목은
더스트 방지 전량 매도로 팔리기만 했다 — 매도만 체결되는 래칫으로 실제 비중이 목표 아래로 계속 떨어졌다
(2026-10-26~30 실측 21% → 4.5%, notes/live_min_lot_rule.md).

여기서는 총 노출(Σ목표 비중)을 맞추는 것을 우선한다: 정책 목표 비중 상위 n종목만 종목당 하한
이상으로 보유하고, 나머지는 0으로 둔다. 종목별 비중은 정책 목표와 달라진다(이 운용금에서는 원리상
맞출 수 없음). 경계 근처에서 n이나 선택 종목이 사이클마다 뒤집혀 교체 매매가 나지 않도록
n에는 띠 형태의 히스테리시스를, 선택 종목에는 보유 우선 규칙을 둔다. 순수 함수라 브로커 없이 시험할 수 있다.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# 종목당 보유 하한 = 최소주문금액 × 이 배수 — 하한에 딱 맞춰 사면 조금만 내려도 최소주문금액 아래로
# 떨어져 팔 수 없는 더스트가 되므로 여유를 둔다
HOLD_FLOOR_MULTIPLE = 1.5
N_UP_MARGIN = 1.10  # 예산이 (n+1)·하한의 이 배수 이상일 때만 종목 수를 늘린다
N_DOWN_MARGIN = 0.95  # 예산이 n·하한의 이 배수 미만일 때만 종목 수를 줄인다
KEEP_RATIO = 0.5  # 이미 선택된 종목은 정책 비중이 n번째 후보 비중의 이 비율 이상이면 계속 유지


def choose_n(budget: float, floor: float, n_prev: int, n_max: int) -> int:
    """보유 종목 수 — 직전 값에서 예산이 띠를 벗어날 때만 움직인다."""
    if floor <= 0:
        return n_max
    n = min(n_prev, n_max)
    while n < n_max and budget >= (n + 1) * floor * N_UP_MARGIN:
        n += 1
    while n > 0 and budget < n * floor * N_DOWN_MARGIN:
        n -= 1
    return n


def allocate(budget: float, weights: dict[str, float], floors: dict[str, float], cap: float) -> dict[str, float]:
    """선택 종목에 예산을 정책 비중 비례로 나누되, 종목당 하한 floors·상한 cap(금액)을 지킨다."""
    fixed: dict[str, float] = {}
    while True:
        free = [s for s in weights if s not in fixed]
        if not free:
            return fixed
        rest = budget - sum(fixed.values())
        total_w = sum(weights[s] for s in free)
        prop = {s: rest * (weights[s] / total_w if total_w > 0 else 1 / len(free)) for s in free}
        newly = {s: floors[s] for s in free if prop[s] < floors[s]}
        if not newly:
            newly = {s: cap for s in free if prop[s] > cap}
        if not newly:
            return {**fixed, **prop}
        fixed.update(newly)


def executable_targets(
    weights: dict[str, float],
    equity: float,
    values: dict[str, float],
    candidates: list[str],
    min_notional: dict[str, float],
    max_weight: float,
    prev_selected: list[str] | None,
    prev_n: int | None,
    sell_min: dict[str, float],
) -> tuple[dict[str, float], list[str], int]:
    """(후보 종목별 실행 목표 금액, 선택 종목, n).

    weights: 정책 목표 비중(상한 적용 후, 전 종목). values: 종목별 현재 평가액.
    candidates: 이번 사이클에 주문 가능한 종목(거래 가능·시세 조회·스프레드 통과).
    sell_min: 종목별 매도 가능한 최소 평가액 — 이보다 작은 미선택 보유분은 팔 수 없어 그대로 남는다.
    후보가 아닌 종목은 결과에 넣지 않는다(이번 사이클 손대지 않음).
    """
    cand = sorted(candidates, key=lambda s: weights.get(s, 0.0), reverse=True)
    # 손댈 수 없는 보유분(거래불가·시세 실패·스프레드 보류 종목)은 이미 노출의 일부이므로 예산에서 뺀다
    locked = sum(v for s, v in values.items() if s not in set(cand))
    budget = max(0.0, sum(weights.values()) * equity - locked)
    floors = {s: max(1.0, min_notional[s] * HOLD_FLOOR_MULTIPLE) for s in cand}
    floor = max(floors.values(), default=0.0)
    cap = max_weight * equity

    if prev_n is None:
        prev_n = sum(1 for s in cand if values.get(s, 0.0) >= sell_min[s])
    n = choose_n(budget, floor, prev_n, len(cand))

    def select(n: int) -> list[str]:
        if n == 0:
            return []
        bar = KEEP_RATIO * weights.get(cand[n - 1], 0.0)
        prev = prev_selected if prev_selected is not None else [s for s in cand if values.get(s, 0.0) >= sell_min[s]]
        keep = sorted((s for s in prev if s in floors and weights.get(s, 0.0) >= bar),
                      key=lambda s: weights.get(s, 0.0), reverse=True)[:n]
        return keep + [s for s in cand if s not in keep][: n - len(keep)]

    selected = select(n)
    # 선택에서 빠졌지만 너무 작아 팔 수 없는 보유분도 노출로 남으므로 예산에서 빼고, 모자라면 n을 줄인다
    dust = sum(values.get(s, 0.0) for s in cand if s not in selected and values.get(s, 0.0) < sell_min[s])
    if dust > 0:
        budget = max(0.0, budget - dust)
        n2 = choose_n(budget, floor, n, len(cand))
        if n2 < n:
            n, selected = n2, select(n2)

    alloc = allocate(budget, {s: weights.get(s, 0.0) for s in selected}, floors, cap) if selected else {}
    return {s: alloc.get(s, 0.0) for s in cand}, selected, n


class ExecutionState:
    """직전 사이클의 선택 종목·n — 재시작해도 히스테리시스가 이어지도록 저장(path=None이면 메모리만)."""

    def __init__(self, path: Path | None):
        self.path = path
        self.selected: list[str] | None = None
        self.n: int | None = None
        if path is not None and path.exists():
            try:
                d = json.loads(path.read_text())
                self.selected, self.n = list(d["selected"]), int(d["n"])
            except (OSError, ValueError, KeyError, TypeError):
                log.warning("실행 상태 파일 %s 읽기 실패 — 현재 보유 종목에서 다시 시작", path)

    def save(self, selected: list[str], n: int) -> None:
        self.selected, self.n = selected, n
        if self.path is not None:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"selected": selected, "n": n}))
            tmp.replace(self.path)
