#churn_reason_by_category

# ── 2. FILTER CHURNERS & BUILD SUMMARY ────────────────────────────────────────
churners = df[df["Churn Label"] == "Yes"].copy()
total_churners = len(churners)

churn_reasons_df = (
    churners.groupby(["Churn Category", "Churn Reason"])
    .size()
    .reset_index(name="Count")
)
churn_reasons_df["% of Churners"] = (churn_reasons_df["Count"] / total_churners * 100).round(1)

# Category order by total volume
cat_totals = churn_reasons_df.groupby("Churn Category")["Count"].sum().sort_values(ascending=False)
categories = cat_totals.index.tolist()

# ── 3. PALETTE ────────────────────────────────────────────────────────────────
COLORS = {
    "bg":       "#0F1B2D",
    "panel":    "#162236",
    "text":     "#EAEEF4",
    "subtext":  "#7A8FA6",
    "grid":     "#1E3048",
}
CAT_COLORS = {
    "Competitor":      "#E8533F",
    "Dissatisfaction": "#4A90D9",
    "Price":           "#F5A623",
    "Attitude":        "#7BC67E",
    "Other":           "#B07FD4",
}
# If your data has categories not listed above, auto-assign colors
extra_colors = ["#56CCF2","#F2994A","#EB5757"]
for i, cat in enumerate([c for c in categories if c not in CAT_COLORS]):
    CAT_COLORS[cat] = extra_colors[i % len(extra_colors)]

# ── 4. FIGURE ─────────────────────────────────────────────────────────────────
n_cats = len(categories)
fig = plt.figure(figsize=(18, 13), facecolor=COLORS["bg"])

fig.text(0.04, 0.945, "Churn Reasons within Each Category",
         color=COLORS["text"], fontsize=22, fontweight="bold", va="top")
fig.text(0.04, 0.915,
         f"Based on {total_churners:,} churned customers  ·  Sorted by volume within each category",
         color=COLORS["subtext"], fontsize=10, va="top")

axes = fig.subplots(1, n_cats,
                    gridspec_kw={"left":0.04,"right":0.98,
                                 "top":0.87,"bottom":0.06,
                                 "wspace":0.45})

if n_cats == 1:
    axes = [axes]

for ax, cat in zip(axes, categories):
    cat_df = churn_reasons_df[churn_reasons_df["Churn Category"] == cat].sort_values("Count", ascending=True)
    color  = CAT_COLORS.get(cat, "#56CCF2")
    cat_total = cat_df["Count"].sum()
    cat_pct   = cat_total / total_churners * 100

    ax.set_facecolor(COLORS["panel"])
    for sp in ax.spines.values():
        sp.set_visible(False)

    y_pos = np.arange(len(cat_df))
    bars  = ax.barh(y_pos, cat_df["Count"].values,
                    color=color, height=0.55, alpha=0.9, zorder=3)

    ax.set_yticks(y_pos)

    # Wrap long reason labels
    wrapped = []
    for label in cat_df["Churn Reason"].values:
        words = label.split()
        lines, line = [], []
        for w in words:
            line.append(w)
            if len(" ".join(line)) > 22:
                lines.append(" ".join(line[:-1]))
                line = [w]
        lines.append(" ".join(line))
        wrapped.append("\n".join(lines))
    ax.set_yticklabels(wrapped, fontsize=7.5)

    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", colors=COLORS["subtext"], labelsize=7)
    ax.tick_params(axis="y", colors=COLORS["text"],    labelsize=8.5)

    max_val = cat_df["Count"].max()
    for bar, (_, row) in zip(bars, cat_df.iterrows()):
        w = bar.get_width()
        ax.text(w + max_val * 0.04,
                bar.get_y() + bar.get_height() / 2,
                f"{int(w)} ({row['% of Churners']}%)",
                va="center", ha="left",
                color=COLORS["text"], fontsize=7.5, fontweight="bold")

    ax.set_xlim(0, max_val * 1.55)
    ax.set_title(f"{cat}\n{cat_total:,} churners  ·  {cat_pct:.1f}% of total",
                 color=color, fontsize=10, fontweight="bold", pad=10, loc="left")
    ax.axhline(y=-0.5, color=color, linewidth=2, xmin=0, xmax=1, clip_on=False)

# ── 5. SAVE ───────────────────────────────────────────────────────────────────
plt.savefig("churn_reason_by_category.png",
            dpi=180, bbox_inches="tight", facecolor=COLORS["bg"])
print("✓ Saved: churn_reason_by_category.png")
plt.show()