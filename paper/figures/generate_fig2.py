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

# ---- labeled (highlighted) points: (valid, test, label, color, marker, label_offset) ----
labeled = [
    (0.025, 3.046, "β=30", ORANGE, "o", (0.14, 0.0)),
    (-0.298, 2.443, "Momentum top-10", ORANGE, "s", (-0.12, -0.14)),
    (0.706, 2.567, "Seed 11 (raw Sharpe max)", AQUA, "o", (0.14, 0.05)),
    (1.314, 1.156, "β=−30 (deployed)", BLUE, "o", (0.14, -0.05)),
    (1.477, 0.137, "KOSPI HRL candidate", BLUE, "^", (0.14, -0.05)),
]

# ---- other swept / baseline configurations, reconstructed from ABLATION_TABLE.md / FINDINGS_LOG.md ----
# (valid Sharpe, test Sharpe, source)
others = [
    (-0.436, 0.370, "Equal-weight benchmark"),
    (-0.554, 0.848, "Buy & Hold"),
    (-0.437, -0.129, "MVO (Ledoit-Wolf)"),
    (-0.423, -0.419, "Risk parity (inverse-vol)"),   # <-- restored point
    (-0.969, 0.275, "EIIE"),
    (-0.962, 0.332, "LSRE-CAAN"),
    (1.741, 0.541, "top-K=5"),
    (-0.516, 1.593, "top-K=7"),
    (-0.200, 0.734, "top-K=15"),
    (1.375, 1.256, "TC=5bp"),
    (1.191, 0.955, "TC=20bp"),
    (0.416, 0.600, "β=-90"),
    (-0.779, -1.063, "β=90 (own crypto sweep)"),
    (1.024, 0.827, "seed=22"),
    (0.118, 0.134, "seed=33"),
    (0.204, 1.414, "seed=44"),
    (-0.368, 1.045, "seed=55"),
]

fig, ax = plt.subplots(figsize=(2069/300, 1759/300), dpi=300)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

lo, hi = -1.4, 3.4

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
           zorder=3, alpha=0.95, label=f"Other swept / baseline configurations (n={len(others)})")

# labeled points
marker_size = {"o": 260, "s": 230, "^": 260}
for vx, vy, label, color, marker, (dx, dy) in labeled:
    ax.scatter([vx], [vy], s=marker_size[marker], facecolor=color, edgecolor="#1a1a1a",
               linewidth=1.6, marker=marker, zorder=5)
    ax.text(vx + dx, vy + dy, label, fontsize=14, fontweight="bold", color=TEXT_DARK,
            ha="left" if dx >= 0 else "right", va="center", zorder=6)

ax.set_xlim(lo, hi)
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

fig.suptitle("Validation/test consistency across every swept configuration",
             x=0.02, y=0.975, ha="left", fontsize=14, fontweight="bold", color=TEXT_DARK)
fig.text(0.02, 0.928,
          "Points near the diagonal generalize; points far from it do not — regardless of raw return",
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
