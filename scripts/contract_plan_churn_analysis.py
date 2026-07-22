#contract_plan_churn_analysis
#--------------------------------
# Define total_customers, total_churners, and overall_rate
total_customers = len(df)
total_churners  = df[df["Churn Label"] == "Yes"].shape[0]
overall_rate    = total_churners / total_customers * 100

def churn_rate_by(col, rename_map=None):
    grp = df.groupby(col).agg(
        Total=("Churn Label", "count"),
        Churned=("Churn Label", lambda x: (x == "Yes").sum())
    ).reset_index()
    grp.columns = ["Group", "Total", "Churned"]
    grp["Churn Rate"] = (grp["Churned"] / grp["Total"] * 100).round(1)
    if rename_map:
        grp["Group"] = grp["Group"].map(rename_map).fillna(grp["Group"])
    return grp

contract_df  = churn_rate_by("Contract Type")
payment_df   = churn_rate_by("Payment Method")
group_df     = churn_rate_by("Group",
                   {"Yes": "In Group Contract", "No": "No Group Contract"})
intl_plan_df = churn_rate_by("Intl Plan",
                   {"Yes": "Intl Plan: Yes",   "No": "Intl Plan: No"})
intl_act_df  = churn_rate_by("Intl Active",
                   {"Yes": "Intl Active: Yes",  "No": "Intl Active: No"})
intl_df      = pd.concat([intl_plan_df, intl_act_df], ignore_index=True)
unlimited_df = churn_rate_by("Unlimited Data Plan",
                   {"Yes": "Unlimited Plan: Yes", "No": "Unlimited Plan: No"})

# ── 2. PALETTE ────────────────────────────────────────────────────────────────
C = {
    "bg":       "#0F1B2D", "panel":    "#162236",
    "text":     "#EAEEF4", "subtext":  "#7A8FA6",
    "grid":     "#1E3048", "churn":    "#E8533F",
    "highlight":"#F5A623", "a1":       "#4A90D9",
    "a2":       "#7BC67E", "a3":       "#B07FD4",
    "a4":       "#56CCF2", "a5":       "#F2994A",
}

# ── 3. HELPERS ────────────────────────────────────────────────────────────────
def style(ax):
    ax.set_facecolor(C["panel"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(axis="x", colors=C["subtext"], labelsize=8)
    ax.tick_params(axis="y", colors=C["subtext"], labelsize=8)
    ax.grid(axis="y", color=C["grid"], linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

def bmark(ax):
    ax.axhline(overall_rate, color=C["highlight"], linewidth=1.3,
               linestyle="--", zorder=4, alpha=0.85)
    xlim = ax.get_xlim()
    ax.text(xlim[1], overall_rate + 0.8,
            f"avg {overall_rate:.1f}%",
            color=C["highlight"], fontsize=7.5, ha="right", va="bottom")

def val_label(ax, bars, vals, totals=None):
    for i, (bar, val) in enumerate(zip(bars, vals)):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 0.6, f"{val:.1f}%",
                ha="center", va="bottom",
                color=C["text"], fontsize=10, fontweight="bold")
        if totals is not None:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() * 0.07, f"n={totals[i]:,}",
                    ha="center", va="bottom",
                    color="white", fontsize=7.5, alpha=0.65)

def auto_colors(rates, palette):
    return [C["churn"] if r > overall_rate else palette[i % len(palette)]
            for i, r in enumerate(rates)]

def callout(ax, text, color):
    ax.text(0.97, 0.97, text, transform=ax.transAxes,
            ha="right", va="top", color=color,
            fontsize=8.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35", facecolor=C["bg"],
                      edgecolor=color, alpha=0.85))

# ── 4. FIGURE ─────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 13), facecolor=C["bg"])

fig.text(0.04, 0.955, "Contract & Plan Churn Rate Analysis",
         color=C["text"], fontsize=22, fontweight="bold", va="top")
fig.text(0.04, 0.925,
         f"Overall churn rate: {overall_rate:.1f}%  ·  Dashed line = overall benchmark",
         color=C["subtext"], fontsize=10, va="top")

gs = fig.add_gridspec(2, 3, left=0.05, right=0.97,
                      top=0.89, bottom=0.07,
                      hspace=0.44, wspace=0.32)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[0, 2])
ax4 = fig.add_subplot(gs[1, 0])
ax5 = fig.add_subplot(gs[1, 1:])

# Chart 1 — Contract Type
style(ax1)
x = np.arange(len(contract_df))
bars1 = ax1.bar(x, contract_df["Churn Rate"], width=0.5,
                color=auto_colors(contract_df["Churn Rate"], [C["a1"],C["a2"],C["a3"]]),
                zorder=3, edgecolor=C["bg"], linewidth=0.5)
bmark(ax1)
val_label(ax1, bars1, contract_df["Churn Rate"], contract_df["Total"].tolist())
ax1.set_xticks(x); ax1.set_xticklabels(contract_df["Group"], color=C["text"], fontsize=9)
ax1.set_ylabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax1.set_ylim(0, contract_df["Churn Rate"].max() * 1.22)
ax1.set_title("Contract Type", color=C["text"], fontsize=12, fontweight="bold", pad=10, loc="left")
m2m = contract_df.iloc[contract_df["Churn Rate"].idxmax()]["Churn Rate"]
low = contract_df.iloc[contract_df["Churn Rate"].idxmin()]["Churn Rate"]
callout(ax1, f"Highest risk contract\n{m2m:.1f}% vs {low:.1f}% lowest", C["churn"])

# Chart 2 — Payment Method
style(ax2)
x = np.arange(len(payment_df))
bars2 = ax2.bar(x, payment_df["Churn Rate"], width=0.5,
                color=auto_colors(payment_df["Churn Rate"], [C["a1"],C["a2"],C["a3"]]),
                zorder=3, edgecolor=C["bg"], linewidth=0.5)
bmark(ax2)
val_label(ax2, bars2, payment_df["Churn Rate"], payment_df["Total"].tolist())
ax2.set_xticks(x); ax2.set_xticklabels(payment_df["Group"], color=C["text"], fontsize=9)
ax2.set_ylabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax2.set_ylim(0, payment_df["Churn Rate"].max() * 1.22)
ax2.set_title("Payment Method", color=C["text"], fontsize=12, fontweight="bold", pad=10, loc="left")
hi = payment_df.iloc[payment_df["Churn Rate"].idxmax()]
lo = payment_df.iloc[payment_df["Churn Rate"].idxmin()]
callout(ax2, f"{hi['Group']}\n{hi['Churn Rate']-lo['Churn Rate']:.1f}pp vs {lo['Group']}", C["churn"])

# Chart 3 — Group Membership
style(ax3)
x = np.arange(len(group_df))
bars3 = ax3.bar(x, group_df["Churn Rate"], width=0.45,
                color=auto_colors(group_df["Churn Rate"], [C["a2"],C["a1"]]),
                zorder=3, edgecolor=C["bg"], linewidth=0.5)
bmark(ax3)
val_label(ax3, bars3, group_df["Churn Rate"], group_df["Total"].tolist())
ax3.set_xticks(x); ax3.set_xticklabels(group_df["Group"], color=C["text"], fontsize=9)
ax3.set_ylabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax3.set_ylim(0, group_df["Churn Rate"].max() * 1.22)
ax3.set_title("Group Contract Membership", color=C["text"], fontsize=12, fontweight="bold", pad=10, loc="left")
g_yes = group_df[group_df["Group"]=="In Group Contract"]["Churn Rate"].values[0]
g_no  = group_df[group_df["Group"]=="No Group Contract"]["Churn Rate"].values[0]
callout(ax3, f"Group members\n{g_no-g_yes:.1f}pp less\nlikely to churn", C["a2"])

# Chart 4 — International Plan & Active
style(ax4)
x = np.arange(len(intl_df))
bars4 = ax4.bar(x, intl_df["Churn Rate"], width=0.5,
                color=auto_colors(intl_df["Churn Rate"], [C["a3"],C["a1"],C["a4"],C["a2"]]),
                zorder=3, edgecolor=C["bg"], linewidth=0.5)
bmark(ax4)
val_label(ax4, bars4, intl_df["Churn Rate"], intl_df["Total"].tolist())
ax4.set_xticks(x); ax4.set_xticklabels(intl_df["Group"], color=C["text"], fontsize=8.5)
ax4.set_ylabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax4.set_ylim(0, intl_df["Churn Rate"].max() * 1.22)
ax4.set_title("International Plan & Activity", color=C["text"], fontsize=12, fontweight="bold", pad=10, loc="left")
ax4.axvline(1.5, color=C["grid"], linewidth=1.2, linestyle=":", zorder=5)
ax4.text(0.75, -0.1, "Has Intl Plan?", transform=ax4.get_xaxis_transform(),
         ha="center", color=C["subtext"], fontsize=7.5)
ax4.text(2.25, -0.1, "Makes Intl Calls?", transform=ax4.get_xaxis_transform(),
         ha="center", color=C["subtext"], fontsize=7.5)

# Chart 5 — Unlimited Data Plan
style(ax5)
x = np.arange(len(unlimited_df))
bars5 = ax5.bar(x, unlimited_df["Churn Rate"], width=0.35,
                color=auto_colors(unlimited_df["Churn Rate"], [C["a2"],C["a1"]]),
                zorder=3, edgecolor=C["bg"], linewidth=0.5)
bmark(ax5)
val_label(ax5, bars5, unlimited_df["Churn Rate"], unlimited_df["Total"].tolist())
ax5.set_xticks(x); ax5.set_xticklabels(unlimited_df["Group"], color=C["text"], fontsize=11)
ax5.set_ylabel("Churn Rate (%)", color=C["subtext"], fontsize=9)
ax5.set_ylim(0, unlimited_df["Churn Rate"].max() * 1.22)
ax5.set_title("Unlimited Data Plan", color=C["text"], fontsize=12, fontweight="bold", pad=10, loc="left")
u_yes = unlimited_df[unlimited_df["Group"]=="Unlimited Plan: Yes"]["Churn Rate"].values[0]
u_no  = unlimited_df[unlimited_df["Group"]=="Unlimited Plan: No"]["Churn Rate"].values[0]
callout(ax5, f"Both groups above avg\n{u_yes:.1f}% (unlimited) vs {u_no:.1f}% (no plan)\nSuggest plan-usage mismatch", C["highlight"])

# Legend
above = mpatches.Patch(color=C["churn"], label=f"Above benchmark ({overall_rate:.1f}%)")
below = mpatches.Patch(color=C["a1"],    label="Below or near benchmark")
fig.legend(handles=[above, below], loc="upper right",
           bbox_to_anchor=(0.97, 0.97), fontsize=8.5,
           frameon=False, labelcolor=C["text"])

plt.savefig("contract_plan_churn_analysis.png",
            dpi=180, bbox_inches="tight", facecolor=C["bg"])
print(f"✓ Saved: contract_plan_churn_analysis.png")
plt.show()