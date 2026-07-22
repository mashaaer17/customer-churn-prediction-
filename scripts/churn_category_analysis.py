#churn_category_analysis

# ── 1. LOAD DATA ───────────────────────────────────────────

# ── 2. ISOLATE CHURNERS & BUILD CATEGORY SUMMARY ──────────────────────────────
churners = df[df["Churn Label"] == "Yes"].copy()

total_churners = len(churners)
total_customers = len(df)
overall_churn_rate = total_churners / total_customers * 100

# Count and percentage per Churn Category
category_counts = (
    churners["Churn Category"]
    .value_counts()
    .reset_index()
)
category_counts.columns = ["Churn Category", "Count"]
category_counts["% of Churners"] = (category_counts["Count"] / total_churners * 100).round(1)
category_counts["% of All Customers"] = (category_counts["Count"] / total_customers * 100).round(1)
category_counts = category_counts.sort_values("Count", ascending=True)   # for horizontal bar

print("=" * 55)
print(f"  DATABEL TELECOM — CHURN CATEGORY BREAKDOWN")
print("=" * 55)
print(f"  Total Customers : {total_customers:,}")
print(f"  Total Churners  : {total_churners:,}")
print(f"  Overall Rate    : {overall_churn_rate:.1f}%")
print("=" * 55)
print(category_counts[["Churn Category","Count","% of Churners"]].to_string(index=False))
print("=" * 55)

# ── 3. COLOUR PALETTE ─────────────────────────────────────────────────────────
# Telecom-style: deep navy base, coral accent, muted secondaries
COLORS = {
    "bg"       : "#0F1B2D",
    "panel"    : "#162236",
    "accent"   : "#E8533F",
    "highlight": "#F5A623",
    "text"     : "#EAEEF4",
    "subtext"  : "#7A8FA6",
    "grid"     : "#1E3048",
    "bars"     : ["#E8533F","#F5A623","#4A90D9","#7BC67E","#B07FD4","#56CCF2","#F2994A"],
}

n = len(category_counts)
bar_colors = COLORS["bars"][:n]

# ── 4. FIGURE LAYOUT ──────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 9), facecolor=COLORS["bg"])

# Grid: left = horizontal bar chart | right-top = donut | right-bottom = table
gs = fig.add_gridspec(2, 2, width_ratios=[1.6, 1],
                      height_ratios=[1.2, 0.8],
                      hspace=0.35, wspace=0.3,
                      left=0.06, right=0.97, top=0.88, bottom=0.07)

ax_bar   = fig.add_subplot(gs[:, 0])    # full left column
ax_donut = fig.add_subplot(gs[0, 1])    # top-right
ax_table = fig.add_subplot(gs[1, 1])    # bottom-right

# ── 5. HEADER ─────────────────────────────────────────────────────────────────
fig.text(0.10, 0.940, "Churn Category Breakdown",
         color=COLORS["text"], fontsize=20, fontweight="bold", va="top")
fig.text(0.72, 0.95,
         f"Overall Churn Rate   {overall_churn_rate:.1f}%   |   "
         f"{total_churners:,} of {total_customers:,} customers",
         color=COLORS["highlight"], fontsize=10, fontweight="bold", va="top", ha="center")

# ── 6. HORIZONTAL BAR CHART ───────────────────────────────────────────────────
ax_bar.set_facecolor(COLORS["panel"])
for spine in ax_bar.spines.values():
    spine.set_visible(False)

bars = ax_bar.barh(
    category_counts["Churn Category"],
    category_counts["Count"],
    color=bar_colors,
    height=0.55,
    zorder=3
)

# subtle grid
ax_bar.xaxis.set_tick_params(labelcolor=COLORS["subtext"], labelsize=9)
ax_bar.yaxis.set_tick_params(labelcolor=COLORS["text"], labelsize=11)
ax_bar.set_xlabel("Number of Customers", color=COLORS["subtext"], fontsize=9, labelpad=8)
ax_bar.tick_params(axis="x", colors=COLORS["subtext"])
ax_bar.tick_params(axis="y", colors=COLORS["text"])
ax_bar.xaxis.set_minor_locator(plt.NullLocator())
ax_bar.grid(axis="x", color=COLORS["grid"], linewidth=0.7, zorder=0)
ax_bar.set_axisbelow(True)

# value labels on bars
for bar, (_, row) in zip(bars, category_counts.iterrows()):
    w = bar.get_width()
    ax_bar.text(w + max(category_counts["Count"]) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{int(w):,}  ({row['% of Churners']}%)",
                va="center", ha="left",
                color=COLORS["text"], fontsize=10, fontweight="bold")

ax_bar.set_xlim(0, max(category_counts["Count"]) * 1.22)
ax_bar.set_title("Churners by Category", color=COLORS["text"],
                 fontsize=13, fontweight="bold", pad=12, loc="left")

# ── 7. DONUT CHART ────────────────────────────────────────────────────────────
ax_donut.set_facecolor(COLORS["panel"])
wedges, _ = ax_donut.pie(
    category_counts["Count"],
    colors=bar_colors,
    startangle=90,
    wedgeprops=dict(width=0.45, edgecolor=COLORS["panel"], linewidth=2),
    counterclock=False
)
ax_donut.text(0, 0, f"{overall_churn_rate:.1f}%\nchurn",
              ha="center", va="center",
              color=COLORS["text"], fontsize=14, fontweight="bold", linespacing=1.5)
ax_donut.set_title("Share of Churners", color=COLORS["text"],
                   fontsize=12, fontweight="bold", pad=10)

legend_labels = [f"{row['Churn Category']} ({row['% of Churners']}%)"
                 for _, row in category_counts.sort_values("Count", ascending=False).iterrows()]
legend_colors = list(reversed(bar_colors))
patches = [mpatches.Patch(color=c, label=l) for c, l in zip(legend_colors, legend_labels)]
ax_donut.legend(handles=patches, loc="lower center",
                bbox_to_anchor=(0.5, -0.28), ncol=1,
                fontsize=8, frameon=False,
                labelcolor=COLORS["text"])

# ── 8. SUMMARY TABLE ──────────────────────────────────────────────────────────
ax_table.set_facecolor(COLORS["panel"])
ax_table.axis("off")

table_df = category_counts.sort_values("Count", ascending=False)[
    ["Churn Category", "Count", "% of Churners", "% of All Customers"]
].reset_index(drop=True)

col_labels = ["Category", "Churners", "% of\nChurners", "% of All\nCustomers"]
table_data = table_df.values.tolist()

tbl = ax_table.table(
    cellText=table_data,
    colLabels=col_labels,
    cellLoc="center",
    loc="center"
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.scale(1, 1.6)

for (row, col), cell in tbl.get_celld().items():
    cell.set_edgecolor(COLORS["grid"])
    if row == 0:
        cell.set_facecolor(COLORS["accent"])
        cell.set_text_props(color="white", fontweight="bold")
    elif row % 2 == 0:
        cell.set_facecolor("#1A2B40")
        cell.set_text_props(color=COLORS["text"])
    else:
        cell.set_facecolor(COLORS["panel"])
        cell.set_text_props(color=COLORS["text"])

ax_table.set_title("Detailed Breakdown", color=COLORS["text"],
                   fontsize=12, fontweight="bold", pad=0.20)

# ── 9. SAVE ───────────────────────────────────────────────────────────────────
output_dir = "/mnt/user-data/outputs/"
os.makedirs(output_dir, exist_ok=True)
plt.savefig(os.path.join(output_dir, "churn_category_analysis.png"),
            dpi=180, bbox_inches="tight", facecolor=COLORS["bg"])
print("\n✓ Chart saved to churn_category_analysis.png")
plt.show()