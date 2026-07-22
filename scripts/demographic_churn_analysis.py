# 1. Demographic vs Churn

total_customers = len(df)
total_churners  = df[df["Churn Label"] == "Yes"].shape[0]
overall_rate    = total_churners / total_customers * 100

def churn_rate_by(col, df=df):
    grp = df.groupby(col).agg(
        Total=("Churn Label", "count"),
        Churned=("Churn Label", lambda x: (x == "Yes").sum())
    ).reset_index()
    grp.columns = ["Group", "Total", "Churned"]
    grp["Churn Rate"] = (grp["Churned"] / grp["Total"] * 100).round(1)
    return grp

senior_df = churn_rate_by("Senior")
u30_df    = churn_rate_by("Under 30")
gender_df = churn_rate_by("Gender")

# State: filter to states with at least 30 customers, top 10 by churn rate
state_df = churn_rate_by("State")
state_df = (state_df[state_df["Total"] >= 30]
            .sort_values("Churn Rate", ascending=False)
            .head(10)
            .sort_values("Churn Rate", ascending=True))

# ── 2. PALETTE ────────────────────────────────────────────────────────────────
C = {
    "bg":       "#0F1B2D",
    "panel":    "#162236",
    "text":     "#EAEEF4",
    "subtext":  "#7A8FA6",
    "grid":     "#1E3048",
    "churn":    "#E8533F",
    "retain":   "#2D5F8A",
    "highlight":"#F5A623",
    "accent2":  "#4A90D9",
    "accent3":  "#7BC67E",
    "accent4":  "#B07FD4",
}

# ── 3. HELPERS ────────────────────────────────────────────────────────────────
def style_ax(ax):
    ax.set_facecolor(C["panel"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(axis="x", colors=C["subtext"], labelsize=8)
    ax.tick_params(axis="y", colors=C["text"],    labelsize=9)
    ax.grid(axis="x", color=C["grid"], linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

def benchmark_v(ax):
    ax.axhline(overall_rate, color=C["highlight"], linewidth=1.2,
               linestyle="--", zorder=4, alpha=0.8)

def benchmark_h(ax):
    ax.axvline(overall_rate, color=C["highlight"], linewidth=1.2,
               linestyle="--", zorder=4, alpha=0.8)

def label_v(ax, bars, values):
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.8,
                f"{val:.1f}%",
                ha="center", va="bottom",
                color=C["text"], fontsize=10, fontweight="bold")

def label_h(ax, bars, values, max_val):
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max_val * 0.02,
                bar.get_y() + bar.get_height()/2,
                f"{val:.1f}%",
                va="center", ha="left",
                color=C["text"], fontsize=9, fontweight="bold")

def count_label(ax, bars, totals):
    for bar, n in zip(bars, totals):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() * 0.08,
                f"n={n:,}",
                ha="center", va="bottom",
                color="white", fontsize=8, alpha=0.7)

# ── 4. FIGURE ─────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 12), facecolor=C["bg"])

fig.text(0.04, 0.955, "Demographic Churn Rate Profiling",
         color=C["text"], fontsize=22, fontweight="bold", va="top")
fig.text(0.04, 0.925,
         f"Overall churn rate: {overall_rate:.1f}%  ·  Dashed line = overall benchmark",
         color=C["subtext"], fontsize=10, va="top")

gs = fig.add_gridspec(2, 2, left=0.05, right=0.97,
                      top=0.89, bottom=0.07,
                      hspace=0.42, wspace=0.32)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, 0])
ax4 = fig.add_subplot(gs[1, 1])

# ── CHART 1: SENIOR ───────────────────────────────────────────────────────────
style_ax(ax1)
x = np.arange(len(senior_df))
colors1 = [C["churn"] if r > overall_rate else C["accent2"] for r in senior_df["Churn Rate"]]
bars1 = ax1.bar(x, senior_df["Churn Rate"], width=0.45,
                color=colors1, zorder=3, edgecolor=C["bg"], linewidth=0.5)
benchmark_v(ax1)
label_v(ax1, bars1, senior_df["Churn Rate"])
count_label(ax1, bars1, senior_df["Total"])
ax1.set_xticks(x); ax1.set_xticklabels(senior_df["Group"], color=C["text"], fontsize=10)
ax1.set_ylabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax1.set_ylim(0, senior_df["Churn Rate"].max() * 1.25)
ax1.tick_params(axis="y", colors=C["subtext"])
ax1.set_title("Churn Rate by Age Group  (Senior vs Non-Senior)",
              color=C["text"], fontsize=11, fontweight="bold", pad=10, loc="left")

# ── CHART 2: GENDER ───────────────────────────────────────────────────────────
style_ax(ax2)
x = np.arange(len(gender_df))
colors2 = [C["accent2"], C["accent3"], C["accent4"]][:len(gender_df)]
bars2 = ax2.bar(x, gender_df["Churn Rate"], width=0.45,
                color=colors2, zorder=3, edgecolor=C["bg"], linewidth=0.5)
benchmark_v(ax2)
label_v(ax2, bars2, gender_df["Churn Rate"])
count_label(ax2, bars2, gender_df["Total"])
ax2.set_xticks(x); ax2.set_xticklabels(gender_df["Group"], color=C["text"], fontsize=10)
ax2.set_ylabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax2.set_ylim(0, gender_df["Churn Rate"].max() * 1.25)
ax2.tick_params(axis="y", colors=C["subtext"])
ax2.set_title("Churn Rate by Gender",
              color=C["text"], fontsize=11, fontweight="bold", pad=10, loc="left")

# ── CHART 3: UNDER 30 ─────────────────────────────────────────────────────────
style_ax(ax3)
x = np.arange(len(u30_df))
colors3 = [C["accent3"] if r < overall_rate else C["churn"] for r in u30_df["Churn Rate"]]
bars3 = ax3.bar(x, u30_df["Churn Rate"], width=0.45,
                color=colors3, zorder=3, edgecolor=C["bg"], linewidth=0.5)
benchmark_v(ax3)
label_v(ax3, bars3, u30_df["Churn Rate"])
count_label(ax3, bars3, u30_df["Total"])
ax3.set_xticks(x); ax3.set_xticklabels(u30_df["Group"], color=C["text"], fontsize=10)
ax3.set_ylabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax3.set_ylim(0, u30_df["Churn Rate"].max() * 1.25)
ax3.tick_params(axis="y", colors=C["subtext"])
ax3.set_title("Churn Rate by Age Bracket  (Under 30 vs 30+)",
              color=C["text"], fontsize=11, fontweight="bold", pad=10, loc="left")

# ── CHART 4: STATE ────────────────────────────────────────────────────────────
style_ax(ax4)
y_pos   = np.arange(len(state_df))
colors4 = [C["churn"] if r > overall_rate else C["accent2"] for r in state_df["Churn Rate"]]
bars4   = ax4.barh(y_pos, state_df["Churn Rate"],
                   color=colors4, height=0.55, zorder=3)
benchmark_h(ax4)
label_h(ax4, bars4, state_df["Churn Rate"].values, state_df["Churn Rate"].max())
ax4.set_yticks(y_pos); ax4.set_yticklabels(state_df["Group"].values, fontsize=9)
ax4.tick_params(axis="x", colors=C["subtext"], labelsize=8)
ax4.tick_params(axis="y", colors=C["text"])
ax4.set_xlabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax4.set_xlim(0, state_df["Churn Rate"].max() * 1.3)
ax4.set_title("Churn Rate by State  (Top 10, min 30 customers)",
              color=C["text"], fontsize=11, fontweight="bold", pad=10, loc="left")
above = mpatches.Patch(color=C["churn"],   label=f"Above {overall_rate:.1f}% benchmark")
below = mpatches.Patch(color=C["accent2"], label=f"Below {overall_rate:.1f}% benchmark")
ax4.legend(handles=[above, below], loc="lower right",
           fontsize=7.5, frameon=False, labelcolor=C["text"])

# ── 5. SAVE ───────────────────────────────────────────────────────────────────
plt.savefig("demographic_churn_analysis.png",
            dpi=180, bbox_inches="tight", facecolor=C["bg"])
print(f"✓ Saved: demographic_churn_analysis.png")
plt.show()