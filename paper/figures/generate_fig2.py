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

# Post-accounting-correction values (2026-10-04 rerun, crypto/notebooks/rerun_fix1004/results/).
# Pre-correction experiments (top-K sweep, KOSPI HRL candidate) are deliberately excluded.
# ---- labeled (highlighted) points: (valid, test, label, color, marker, label_offset) ----
labeled = [
    (0.189, 3.033, "β=30", ORANGE, "o", (0.14, 0.05)),
    (-0.251, 2.240, "Momentum top-10", ORANGE, "s", (0.16, -0.05)),
    (-0.427, 2.577, "Seed 11 (raw Sharpe max)", AQUA, "o", (0.14, 0.1)),
    (0.914, 1.310, "β=−30 (deployed)", BLUE, "o", (0.14, -0.05)),
    (-1.284, -1.175, "β=90 (smallest gap, both negative)", GRAY_EDGE, "^", (0.14, 0.0)),
]

# ---- other configurations (valid Sharpe, test Sharpe, source) ----
others = [
    (-0.451, 0.263, "Equal-weight benchmark"),
    (-0.443, 0.854, "Buy & Hold"),
    (-1.078, -0.032, "MVO (Ledoit-Wolf)"),
    (-1.060, -0.497, "Risk parity (inverse-vol)"),
    (-0.990, 0.176, "EIIE"),
    (-0.976, 0.214, "LSRE-CAAN"),
    (0.974, 1.409, "TC=5bp"),
    (0.794, 1.113, "TC=20bp"),
    (-0.373, 0.471, "β=-90"),
    (-0.464, 1.644, "6-seed ensemble"),
    (-0.460, 0.957, "5-seed ensemble (no seed 11)"),
    (-0.573, 1.110, "clean retrain"),
    (0.253, 0.902, "seed=22"), (-0.347, -0.008, "seed=33"), (-1.355, 1.142, "seed=44"),
    (-0.880, 1.107, "seed=55"), (-1.152, -0.579, "seed=66"), (-0.801, 0.112, "seed=77"),
    (-0.458, 2.207, "seed=88"), (-0.633, 0.142, "seed=99"), (-1.143, 0.973, "seed=110"),
    (-0.992, 0.167, "seed=121"), (-0.649, 1.152, "seed=132"), (-1.070, 0.390, "seed=143"),
    (-0.206, 0.443, "seed=154"), (0.215, 1.610, "seed=165"),
]

fig, ax = plt.subplots(figsize=(2069/300, 1759/300), dpi=300)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

lo, hi = -1.6, 3.4

# consistency band |test - valid| < 0.3
xx = np.linspace(lo, hi, 100)
ax.fill_between(xx, xx - 0.3, xx + 0.3, color=BAND_COLOR, zorder=1, linewidth=0)
ax.plot([lo, hi], [lo, hi], linestyle=(0, (7, 5)), color=LINE_COLOR, linewidth=1.8, zorder=2)
ax.text(hi - 0.75, hi - 0.98, "valid = test", color=TEXT_GRAY, fontsize=12,
        rotation=45, ha="left", va="center", style="italic")

# other points
ox = [p[0] for p in others]
oy = [p[1] for p in others]
ax.scatter(ox, oy, s=90, facecolor=GRAY_FILL, edgecolor=GRAY_EDGE, linewidth=0.8,
           zorder=3, alpha=0.95, label=f"Seeds, ensembles, baselines, TC sweep (n={len(others)})")

# labeled points
marker_size = {"o": 260, "s": 230, "^": 260}
for vx, vy, label, color, marker, (dx, dy) in labeled:
    ax.scatter([vx], [vy], s=marker_size[marker], facecolor=color, edgecolor="#1a1a1a",
               linewidth=1.6, marker=marker, zorder=5)
    ax.text(vx + dx, vy + dy, label, fontsize=12.5, fontweight="bold", color=TEXT_DARK,
            ha="left" if dx >= 0 else "right", va="center", zorder=6)

ax.set_xlim(-1.6, hi)
ax.set_ylim(lo, hi)
ax.set_xticks([-1, 0, 1, 2, 3])
ax.set_yticks([-1, 0, 1, 2, 3])
ax.tick_params(labelsize=15, colors=TEXT_DARK, length=0)
ax.grid(True, color=GRID_COLOR, linewidth=1.1, zorder=0)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("#1a1a1a")
    ax.spines[spine].set_linewidth(1.6)

ax.set_xlabel("Validation-period Sharpe", fontsize=16, color=TEXT_DARK, labelpad=10)
ax.set_ylabel("Test-period Sharpe", fontsize=16, color=TEXT_DARK, labelpad=12)

fig.suptitle("Validation vs. test Sharpe (corrected accounting)",
             x=0.02, y=0.975, ha="left", fontsize=14, fontweight="bold", color=TEXT_DARK)
fig.text(0.02, 0.928,
          "Most configurations lose in validation and gain in test; only the deployed seed is positive in both",
          fontsize=9.5, color=TEXT_GRAY, ha="left")

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
