import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
GRAY_FILL = "#bfbfb8"
GRAY_EDGE = "#8f8f86"
LINE_COLOR = "#52514e"
BAND_COLOR = "#e8edf7"
GRID_COLOR = "#e4e2da"
BG = "#fcfcfb"
TEXT_DARK = "#1a1a1a"
TEXT_GRAY = "#5a5a58"

# Policies retrained with the corrected reward (2026-10-06~08, crypto/notebooks/retrain1006/,
# paper/RETRAIN_1006.md).
# ---- labeled (highlighted) points: (valid, test, label, color, marker, label_offset) ----
labeled = [
    (0.653, 2.602, "β=30 (deployed)", BLUE, "o", (0.14, 0.24)),
    (-0.986, 2.893, "Seed 121 (raw Sharpe max)", AQUA, "o", (0.14, 0.24)),
    (-0.251, 2.240, "Momentum", ORANGE, "s", (0.14, -0.02)),
    (-1.155, 0.448, "β=−30 (old pick)", ORANGE, "o", (0.16, -0.02)),
    (-0.971, -1.065, "β=90 (smallest gap, both negative)", GRAY_EDGE, "^", (0.14, 0.0)),
]

# ---- other configurations (valid Sharpe, test Sharpe, source) ----
others = [
    (-0.451, 0.263, "Equal-weight benchmark"),
    (-0.443, 0.854, "Buy & Hold"),
    (-1.078, -0.032, "MVO (Ledoit-Wolf)"),
    (-1.060, -0.497, "Risk parity (inverse-vol)"),
    (-0.991, 0.148, "EIIE"),
    (-0.975, 0.193, "LSRE-CAAN"),
    (0.693, 2.665, "TC=5bp"),
    (0.573, 2.477, "TC=20bp"),
    (-0.111, 0.743, "β=-90"),
    (-1.322, 0.106, "K=5"), (-1.122, 0.672, "K=7"), (-0.916, 0.760, "K=15"),
    (-0.548, 1.054, "6-seed ensemble"),
    (0.939, 1.907, "clean retrain"),
    (-0.797, 1.165, "5-seed ensemble (no seed 11)"),
    (-0.811, 1.028, "16-seed ensemble"),
    (-0.877, 0.968, "15-seed ensemble (no seed 42)"),
    (0.601, 0.383, "seed=11"), (0.732, 1.916, "seed=22"), (-1.313, 1.205, "seed=33"),
    (-0.788, -0.187, "seed=44"), (-1.365, 1.465, "seed=55"), (-1.067, -0.349, "seed=66"),
    (-1.108, 0.247, "seed=77"), (-1.761, -0.292, "seed=88"), (-0.464, 1.997, "seed=99"),
    (-0.238, 0.271, "seed=110"), (-0.771, 1.773, "seed=132"), (-1.225, 0.399, "seed=143"),
    (-0.526, 1.642, "seed=154"), (-0.788, 1.212, "seed=165"),
]

fig, ax = plt.subplots(figsize=(2069/300, 1759/300), dpi=300)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

lo, hi = -2.0, 3.4

# consistency band |test - valid| < 0.3
xx = np.linspace(lo, hi, 100)
ax.fill_between(xx, xx - 0.3, xx + 0.3, color=BAND_COLOR, zorder=1, linewidth=0)
ax.plot([lo, hi], [lo, hi], linestyle=(0, (7, 5)), color=LINE_COLOR, linewidth=1.8, zorder=2)
ax.text(1.55, 1.2, "valid = test", color=TEXT_GRAY, fontsize=12,
        rotation=37, ha="left", va="center", style="italic")

# other points
ox = [p[0] for p in others]
oy = [p[1] for p in others]
ax.scatter(ox, oy, s=90, facecolor=GRAY_FILL, edgecolor=GRAY_EDGE, linewidth=0.8,
           zorder=3, alpha=0.95, label=f"Seeds, ensembles, baselines, TC and top-K sweeps (n={len(others)})")

# labeled points
marker_size = {"o": 260, "s": 230, "^": 260}
for vx, vy, label, color, marker, (dx, dy) in labeled:
    ax.scatter([vx], [vy], s=marker_size[marker], facecolor=color, edgecolor="#1a1a1a",
               linewidth=1.6, marker=marker, zorder=5)
    ax.text(vx + dx, vy + dy, label, fontsize=12.5, fontweight="bold", color=TEXT_DARK,
            ha="left" if dx >= 0 else "right", va="center", zorder=6)

ax.set_xlim(lo, hi)
ax.set_ylim(lo, hi)
ax.set_xticks([-2, -1, 0, 1, 2, 3])
ax.set_yticks([-2, -1, 0, 1, 2, 3])
ax.tick_params(labelsize=15, colors=TEXT_DARK, length=0)
ax.grid(True, color=GRID_COLOR, linewidth=1.1, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("#1a1a1a")
    ax.spines[spine].set_linewidth(1.6)

ax.set_xlabel("Validation-period Sharpe", fontsize=16, color=TEXT_DARK, labelpad=10)
ax.set_ylabel("Test-period Sharpe", fontsize=16, color=TEXT_DARK, labelpad=12)

fig.suptitle("Validation vs. test Sharpe (retrained policies)",
             x=0.02, y=0.975, ha="left", fontsize=14, fontweight="bold", color=TEXT_DARK)
fig.text(0.02, 0.928,
          "Most lose in validation, gain in test; only β=30 seeds 42, 11, 22 and its clean retrain are positive in both",
          fontsize=8.6, color=TEXT_GRAY, ha="left")

leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), frameon=False,
                 fontsize=13, markerscale=1.0, handletextpad=0.6)
for text in leg.get_texts():
    text.set_color(TEXT_DARK)

fig.subplots_adjust(left=0.135, right=0.97, top=0.87, bottom=0.17)

fig.savefig("/Users/seungbin/school/4-1/졸업프로젝트/paper/figures/fig2_valid_test_consistency.png",
            facecolor=BG)
fig.savefig("/Users/seungbin/school/4-1/졸업프로젝트/paper/figures/fig2_valid_test_consistency.pdf",
            facecolor=BG)
print("saved to paper/figures")
