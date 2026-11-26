"""Thesis figures (static, print). Run: python3 thesis/en/figures/make_figures.py

Figure 1: reproduction funnel — first stage at which each paper exited, stacked by sample
          (source: notes/lit/f1/funnel_table.csv; matches Table 1).
Figure 2: FinRL under the unified protocol — per-seed Δ (annualized log growth vs daily
          equal weight, 0.1% cost) by window and algorithm
          (source: replication/finrl_t3/o2/judge_o2.json; matches Table 5).
Palette: validated default categorical slots 1–3 (light), checked with the dataviz validator.
"""
import csv
import json
import pathlib
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]

SURFACE = "#ffffff"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.titlesize": 9.5, "axes.titleweight": "semibold",
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "pdf.fonttype": 42,
})


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Figure 1
ROWS = [  # (label, predicate on (stage, result))
    ("F0  Not eligible", lambda st, r: st == "F0"),
    ("F1  No official code found", lambda st, r: st == "F1" and r.startswith("찾지 못함")),
    ("F1  Link dead", lambda st, r: st == "F1" and r.startswith("링크 사망")),
    ("F1  Third-party code only", lambda st, r: st == "F1" and r == "제3자만"),
    ("F1  Full text unavailable", lambda st, r: st == "F1" and r == "원문 미확보"),
    ("Code located at F1 check (exploratory)", lambda st, r: st == "F1재확인"),
    ("F2  Incomplete code", lambda st, r: st == "F2"),
    ("F3  Data not obtainable", lambda st, r: st == "F3"),
    ("F4  Not executable", lambda st, r: st == "F4" and r == "실행 불가"),
    ("F4  Not tested", lambda st, r: st == "F4" and r.startswith("미시험")),
    ("F5  Over compute budget", lambda st, r: st == "F5" and r == "한도 초과"),
    ("Passed F4/F5, no F7 place", lambda st, r: r.endswith("(F7 자리 없음)")),
    ("F7  Verdict reached", lambda st, r: st == "F7"),
]
SAMPLES = [("S56", "S56 (n = 52)", S1), ("S-Q", "S-Q (n = 12)", S2), ("보충", "Supplementary (n = 5)", S3)]


def figure1():
    rows = list(csv.DictReader(open(ROOT / "notes/lit/f1/funnel_table.csv", encoding="utf-8")))
    counts = {g: Counter() for g, _, _ in SAMPLES}
    for r in rows:
        if r["group"] not in counts:
            continue  # T1–T4 are outside the funnel
        hit = [lab for lab, f in ROWS if f(r["stage"], r["result"])]
        assert len(hit) == 1, (r["id"], r["stage"], r["result"], hit)
        counts[r["group"]][hit[0]] += 1
    assert sum(sum(c.values()) for c in counts.values()) == 69

    labels = [lab for lab, _ in ROWS]
    fig, ax = plt.subplots(figsize=(6.3, 4.0))
    y = list(range(len(labels)))[::-1]
    left = [0] * len(labels)
    for g, name, col in SAMPLES:
        vals = [counts[g][lab] for lab in labels]
        ax.barh(y, vals, left=left, height=0.62, color=col, edgecolor=SURFACE, linewidth=1.2, label=name)
        left = [a + b for a, b in zip(left, vals)]
    for yi, tot in zip(y, left):
        ax.text(tot + 0.4, yi, str(tot), va="center", ha="left", color=INK, fontsize=8.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Number of papers (each counted once, at the first stage not passed)")
    ax.set_xlim(0, max(left) + 3)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    save(fig, "fig1_funnel")


# ---------------------------------------------------------------- Figure 2
ALGOS = [("a2c", "A2C"), ("ppo", "PPO"), ("ddpg", "DDPG"), ("td3", "TD3")]
WINDOWS = [("W0", "W0 (paper's test year)\nJul 2020–Jun 2021"), ("W1", "W1\nJul 2018–Jun 2019"), ("W2", "W2\nJul 2019–Jun 2020")]
CLS = {"우위": "adv.", "열위": "disadv.", "불확정": "indet."}


def figure2():
    d = json.load(open(ROOT / "replication/finrl_t3/o2/judge_o2.json", encoding="utf-8"))
    main = d["주 판정(조건 b, c=0.001, 매일 등가중)"]
    allv = [v for a, _ in ALGOS for w, _ in WINDOWS for v in main[a]["창별"][w]["Δ(%p/년)"]]
    lo, hi = min(allv) - 1.5, max(allv) + 6.5
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.8), sharey=True, sharex=True)
    for ax, (w, title) in zip(axes, WINDOWS):
        for i, (a, name) in enumerate(ALGOS):
            yi = len(ALGOS) - 1 - i
            cell = main[a]["창별"][w]
            vals = cell["Δ(%p/년)"]
            ax.scatter(vals, [yi] * len(vals), s=22, color=S1, edgecolor=SURFACE, linewidth=0.8, zorder=3)
            med = cell["시드 중앙값"]
            ax.plot([med, med], [yi - 0.28, yi + 0.28], color=INK, linewidth=1.6, zorder=4)
            ax.text(hi - 0.2, yi, CLS.get(cell["분류"], cell["분류"]), ha="right", va="center",
                    fontsize=7.5, color=INK2)
        ax.axvline(0, color=INK2, linewidth=0.9, zorder=2)
        ax.set_title(title, loc="left", fontsize=8.5)
        ax.set_xlim(lo, hi)
        ax.set_ylim(-0.6, len(ALGOS) - 0.2)
        ax.xaxis.grid(True, color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(range(len(ALGOS)))
    axes[0].set_yticklabels([n for _, n in ALGOS][::-1])
    fig.supxlabel("Δ: annualized log growth minus daily equal weight (percentage points per year)", fontsize=8.5,
                  color=INK2, y=-0.04)
    save(fig, "fig2_finrl_delta")


if __name__ == "__main__":
    figure1()
    figure2()
    print("ok")
