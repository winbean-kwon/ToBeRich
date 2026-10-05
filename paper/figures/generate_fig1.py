"""Figure 1 — Table 1 (Section 5) as a bar chart.

Values are the post-accounting-correction test-period net returns (2026-10-04 rerun,
crypto/notebooks/rerun_fix1004/results/). Row 6 is pre-cost, as in Table 1.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

BLUE = "#2a78d6"
ORANGE = "#eb6834"
GRAY_FILL = "#b3b1a8"
BG = "#fcfcfb"
GRID = "#e4e2da"
TEXT_DARK = "#1a1a1a"
TEXT_GRAY = "#5a5a58"
FLOOR = -40.0  # axis floor; bars below are truncated

rows = [
    ("Equal-\nweight", -0.81),
    ("Single\nPPO", -75.84),
    ("v1: direct\nport", -25.53),
    ("v1 +\nsmoothing", 11.14),
    ("v2: baked-in\nsmoothing", -2.11),
    ("v3: paper-\nfaithful", -0.02),
    ("v4 raw\n(pre-cost)", -0.62),
    ("v4 +\nsmoothing", 9.37),
    ("v4 matched\nrouter", 8.03),
    ("β=-30 solo\n(deployed)", 6.66),
]
DEPLOYED = 9

fig, ax = plt.subplots(figsize=(2776 / 200, 1082 / 200), dpi=200)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

for i, (label, v) in enumerate(rows):
    color = GRAY_FILL if i == 0 else (BLUE if v > 0 else ORANGE)
    h = max(v, FLOOR + 3) if v < FLOOR else v
    lw = 4 if i == DEPLOYED else 1.0
    ax.bar(i, h, width=0.62, color=color, edgecolor=TEXT_DARK, linewidth=lw, zorder=3)
    text = f"{v:+.2f}%"
    weight = "bold" if i == DEPLOYED else "normal"
    if v < FLOOR:
        ax.text(i, h + 2.0, text, ha="center", va="bottom", fontsize=11, fontweight="bold",
                color="white", zorder=5)
        ax.plot([i - 0.25, i - 0.1], [h - 1.4, h - 0.6], color=TEXT_DARK, lw=1.5, zorder=6)
        ax.plot([i + 0.1, i + 0.25], [h - 1.4, h - 0.6], color=TEXT_DARK, lw=1.5, zorder=6)
    elif v >= 0:
        ax.text(i, v + 0.8, text, ha="center", va="bottom", fontsize=13, fontweight=weight, color=TEXT_DARK)
    else:
        ax.text(i, v - 0.8, text, ha="center", va="top", fontsize=13, fontweight=weight, color=TEXT_DARK)

ax.axhline(0, color="#52514e", lw=1.2, zorder=4)
ax.set_ylim(FLOOR, 18)
ax.set_xlim(-0.7, len(rows) - 0.3)
ax.set_yticks([-40, -20, 0])
ax.set_yticklabels(["-40%", "-20%", "+0%"])
ax.set_xticks(range(len(rows)))
ax.set_xticklabels([f"{i}\n{lab}" for i, (lab, _) in enumerate(rows)], fontsize=12, color=TEXT_GRAY)
ax.tick_params(axis="y", labelsize=14, colors=TEXT_GRAY, length=0)
ax.tick_params(axis="x", length=0)
ax.grid(axis="y", color=GRID, lw=1.0, zorder=0)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.spines["bottom"].set_color("#52514e")
ax.set_ylabel("Test-period net return", fontsize=15, color=TEXT_DARK)

fig.suptitle("The architecture cascade: net test-period return by configuration",
             x=0.01, y=0.97, ha="left", fontsize=17, fontweight="bold", color=TEXT_DARK)
fig.text(0.085, 0.80, "Bar 1 (single PPO, −75.84%) is truncated for scale — see break marks. "
         "Bar 6 is pre-cost. Accounting: drifted holdings, rebalancing costs included.",
         fontsize=11.5, color=TEXT_GRAY, ha="left")

handles = [Patch(facecolor=BLUE, edgecolor=TEXT_DARK, label="Net positive"),
           Patch(facecolor=ORANGE, edgecolor=TEXT_DARK, label="Net negative"),
           Patch(facecolor=GRAY_FILL, edgecolor=TEXT_DARK, label="Equal-weight benchmark"),
           Line2D([0], [0], color=TEXT_DARK, lw=4, label="Final deployed configuration")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=4,
          frameon=False, fontsize=12)

fig.subplots_adjust(left=0.08, right=0.99, top=0.76, bottom=0.27)
out = "/Users/seungbin/school/4-1/졸업프로젝트/paper/figures/fig1_architecture_cascade"
fig.savefig(out + ".png", facecolor=BG)
fig.savefig(out + ".pdf", facecolor=BG)
print("saved", out)
