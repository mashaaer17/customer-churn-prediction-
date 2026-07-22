#overcharge_analysis

total_customers = len(df)
total_churners  = (df["Churn Label"] == "Yes").sum()
overall_rate    = total_churners / total_customers * 100

# ── 2. BUILD MISMATCH SEGMENTS ────────────────────────────────────────────────
df = df.copy()

# DATA mismatch: heavy user = above median monthly GB download
median_gb = df["Avg Monthly GB Download"].median()
df["Heavy Data User"] = df["Avg Monthly GB Download"] > median_gb

def segment_label_data(row):
    heavy   = row["Heavy Data User"]
    plan    = row["Unlimited Data Plan"] == "Yes"
    if heavy and plan:     return "Heavy data user\n+ Unlimited Plan\n(no overage)"
    if heavy and not plan: return "Heavy data user\n+ No Unlimited Plan\n(paying overage)"
    if not heavy and plan: return "Light data user\n+ Unlimited Plan\n(overpaying for plan)"
    return                        "Light data user\n+ No Unlimited Plan\n(no overage)"

df["Data Segment"] = df.apply(segment_label_data, axis=1)

data_df = (df.groupby("Data Segment")
             .agg(Total=("Churn Label","count"),
                  Churned=("Churn Label", lambda x: (x=="Yes").sum()))
             .reset_index()
             .rename(columns={"Data Segment":"Segment"}))
data_df["Churn Rate"] = (data_df["Churned"] / data_df["Total"] * 100).round(1)

# INTL mismatch
def segment_label_intl(row):
    active = row["Intl Active"] == "Yes"
    plan   = row["Intl Plan"]   == "Yes"
    if active and plan:     return "Intl Active\n+ Intl Plan\n(no overage)"
    if active and not plan: return "Intl Active\n+ No Intl Plan\n(paying overage)"
    if not active and plan: return "Not Intl Active\n+ Intl Plan\n(overpaying for plan)"
    return                         "Not Intl Active\n+ No Intl Plan\n(no overage)"

df["Intl Segment"] = df.apply(segment_label_intl, axis=1)

intl_df = (df.groupby("Intl Segment")
             .agg(Total=("Churn Label","count"),
                  Churned=("Churn Label", lambda x: (x=="Yes").sum()))
             .reset_index()
             .rename(columns={"Intl Segment":"Segment"}))
intl_df["Churn Rate"] = (intl_df["Churned"] / intl_df["Total"] * 100).round(1)

# Sort segments so mismatch (overage) rows are visually prominent
seg_order_data = [
    "Heavy data user\n+ No Unlimited Plan\n(paying overage)",
    "Heavy data user\n+ Unlimited Plan\n(no overage)",
    "Light data user\n+ Unlimited Plan\n(overpaying for plan)",
    "Light data user\n+ No Unlimited Plan\n(no overage)",
]
seg_order_intl = [
    "Intl Active\n+ No Intl Plan\n(paying overage)",
    "Intl Active\n+ Intl Plan\n(no overage)",
    "Not Intl Active\n+ Intl Plan\n(overpaying for plan)",
    "Not Intl Active\n+ No Intl Plan\n(no overage)",
]
data_df["sort"] = data_df["Segment"].map({s:i for i,s in enumerate(seg_order_data)})
intl_df["sort"] = intl_df["Segment"].map({s:i for i,s in enumerate(seg_order_intl)})
data_df = data_df.sort_values("sort").reset_index(drop=True)
intl_df = intl_df.sort_values("sort").reset_index(drop=True)

# Comparison table
mismatch_data = data_df[data_df["Segment"].str.contains("paying overage")]["Churn Rate"].values[0]
matched_data  = data_df[data_df["Segment"].str.contains("no overage") & data_df["Segment"].str.contains("Heavy")]["Churn Rate"].values[0]
mismatch_intl = intl_df[intl_df["Segment"].str.contains("paying overage")]["Churn Rate"].values[0]
matched_intl  = intl_df[intl_df["Segment"].str.contains("no overage") & intl_df["Segment"].str.contains("Active\n\+")]["Churn Rate"].values[0]

comp_df = pd.DataFrame({
    "Group":      ["Data: Plan\nmatched","Data: Overage\n(mismatch)","Intl: Plan\nmatched","Intl: Overage\n(mismatch)"],
    "Churn Rate": [matched_data, mismatch_data, matched_intl, mismatch_intl],
})

# Revenue at risk
churners_data_mismatch = data_df[data_df["Segment"].str.contains("paying overage")]["Churned"].values[0]
churners_intl_mismatch = intl_df[intl_df["Segment"].str.contains("paying overage")]["Churned"].values[0]
churners_other = total_churners - churners_data_mismatch - churners_intl_mismatch

avg_monthly = df[df["Churn Label"]=="Yes"]["Monthly Charge"].mean()
rev_df = pd.DataFrame({
    "Segment":            ["Data overage churners","Intl overage churners","Other churners"],
    "Churned Customers":  [churners_data_mismatch, churners_intl_mismatch, churners_other],
    "Monthly Avg Charge": [avg_monthly, avg_monthly, avg_monthly],
})
rev_df["Annual Revenue at Risk"] = (rev_df["Monthly Avg Charge"] * 12 * rev_df["Churned Customers"]).astype(int)

# ── 3. PALETTE ────────────────────────────────────────────────────────────────
C = {
    "bg":"#0F1B2D","panel":"#162236","text":"#EAEEF4","subtext":"#7A8FA6",
    "grid":"#1E3048","churn":"#E8533F","highlight":"#F5A623",
    "safe":"#7BC67E","a1":"#4A90D9","a2":"#B07FD4","warn":"#F2994A",
}

# ── 4. HELPERS ────────────────────────────────────────────────────────────────
def style(ax, grid_axis="x"):
    ax.set_facecolor(C["panel"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(axis="x", colors=C["subtext"], labelsize=8)
    ax.tick_params(axis="y", colors=C["text"], labelsize=9)
    ax.grid(axis=grid_axis, color=C["grid"], linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)

def bmark_v(ax):
    ax.axhline(overall_rate,color=C["highlight"],linewidth=1.3,linestyle="--",zorder=4,alpha=0.85)

def bmark_h(ax):
    ax.axvline(overall_rate,color=C["highlight"],linewidth=1.3,linestyle="--",zorder=4,alpha=0.85)

def h_labels(ax, bars, df, max_val):
    for bar, (_, row) in zip(bars, df.iterrows()):
        w = bar.get_width()
        ax.text(w + max_val*0.02, bar.get_y()+bar.get_height()/2,
                f"{w:.1f}%   (n={row['Total']:,}  |  {int(row['Churned'])} churned)",
                va="center",ha="left",color=C["text"],fontsize=9,fontweight="bold")

def v_labels(ax, bars, vals):
    for bar,val in zip(bars,vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.8, f"{val:.1f}%",
                ha="center",va="bottom",color=C["text"],fontsize=9.5,fontweight="bold")

def callout(ax, text, color, x=0.99, y=0.13):
    ax.text(x, y, text, transform=ax.transAxes, ha="right", va="bottom",
            color=color, fontsize=8.5, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4",facecolor=C["bg"],edgecolor=color,alpha=0.9))

# ── 5. FIGURE ─────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 14), facecolor=C["bg"])

fig.text(0.04,0.955,"The Overcharge Analysis  —  Plan-Usage Mismatch",color=C["text"],fontsize=22,fontweight="bold",va="top")
fig.text(0.04,0.925,
         f"Customers paying overage fees without a matching plan  ·  Overall churn rate: {overall_rate:.1f}%  ·  Dashed line = benchmark",
         color=C["subtext"],fontsize=10,va="top")

gs = fig.add_gridspec(2,3,left=0.05,right=0.97,top=0.895,bottom=0.07,hspace=0.48,wspace=0.35)
ax1 = fig.add_subplot(gs[0,:2])
ax2 = fig.add_subplot(gs[0,2])
ax3 = fig.add_subplot(gs[1,:2])
ax4 = fig.add_subplot(gs[1,2])

# Chart 1 — Data mismatch
style(ax1,"x")
COLORS_D = [C["churn"],C["safe"],C["warn"],C["a1"]]
y1 = np.arange(len(data_df))
bars1 = ax1.barh(y1,data_df["Churn Rate"],color=COLORS_D[:len(data_df)],height=0.52,zorder=3)
bmark_h(ax1)
h_labels(ax1,bars1,data_df,data_df["Churn Rate"].max())
ax1.set_yticks(y1); ax1.set_yticklabels(data_df["Segment"],fontsize=9)
ax1.set_xlim(0,data_df["Churn Rate"].max()*1.6)
ax1.set_xlabel("Churn Rate (%)",color=C["subtext"],fontsize=9)
ax1.set_title("DATA Plan Mismatch  —  Churn Rate by Usage vs Plan Combination",
              color=C["text"],fontsize=12,fontweight="bold",pad=10,loc="left")
callout(ax1,"⚠  Heavy data users without\n    Unlimited Plan churn at 2×\n    plan-matched users.\n\n"
        "    ACTION: Proactively upgrade\n    these customers to Unlimited.",C["warn"])

# Chart 2 — Comparison
style(ax2,"y")
ax2.grid(axis="y",color=C["grid"],linewidth=0.6,zorder=0)
x2 = np.arange(len(comp_df))
colors2=[C["safe"],C["churn"],C["safe"],C["churn"]]
bars2=ax2.bar(x2,comp_df["Churn Rate"],width=0.5,color=colors2,zorder=3,edgecolor=C["bg"],linewidth=0.5)
bmark_v(ax2)
v_labels(ax2,bars2,comp_df["Churn Rate"])
ax2.set_xticks(x2); ax2.set_xticklabels(comp_df["Group"],color=C["text"],fontsize=8)
ax2.set_ylabel("Churn Rate (%)",color=C["subtext"],fontsize=9)
ax2.set_ylim(0,comp_df["Churn Rate"].max()*1.28)
ax2.tick_params(axis="y",colors=C["subtext"])
ax2.set_title("Matched vs Mismatch\nChurn Rate Comparison",color=C["text"],fontsize=11,fontweight="bold",pad=10,loc="left")
ax2.axvline(1.5,color=C["grid"],linewidth=1.2,linestyle=":",zorder=5)
ax2.text(0.5,-0.1,"Data",transform=ax2.get_xaxis_transform(),ha="center",color=C["subtext"],fontsize=8)
ax2.text(2.5,-0.1,"Intl",transform=ax2.get_xaxis_transform(),ha="center",color=C["subtext"],fontsize=8)
ax2.legend(handles=[mpatches.Patch(color=C["safe"],label="Plan matched"),
                    mpatches.Patch(color=C["churn"],label="Overage mismatch")],
           loc="upper left",fontsize=7.5,frameon=False,labelcolor=C["text"])

# Chart 3 — Intl mismatch
style(ax3,"x")
COLORS_I=[C["churn"],C["safe"],C["warn"],C["a1"]]
y3=np.arange(len(intl_df))
bars3=ax3.barh(y3,intl_df["Churn Rate"],color=COLORS_I[:len(intl_df)],height=0.52,zorder=3)
bmark_h(ax3)
h_labels(ax3,bars3,intl_df,intl_df["Churn Rate"].max())
ax3.set_yticks(y3); ax3.set_yticklabels(intl_df["Segment"],fontsize=9)
ax3.set_xlim(0,intl_df["Churn Rate"].max()*1.6)
ax3.set_xlabel("Churn Rate (%)",color=C["subtext"],fontsize=9)
ax3.set_title("INTERNATIONAL Plan Mismatch  —  Churn Rate by Usage vs Plan Combination",
              color=C["text"],fontsize=12,fontweight="bold",pad=10,loc="left")
callout(ax3,"⚠  Intl active customers without\n    an Intl Plan churn at 2×\n    plan-matched users.\n\n"
        "    ACTION: Proactively upgrade\n    Intl Active customers with\n    no Intl Plan.",C["warn"])

# Chart 4 — Revenue at risk
style(ax4,"x")
y4=np.arange(len(rev_df))
bars4=ax4.barh(y4,rev_df["Annual Revenue at Risk"]/1_000_000,
               color=[C["churn"],C["a2"],C["a1"]],height=0.45,zorder=3)
for bar,(_,row) in zip(bars4,rev_df.iterrows()):
    w=bar.get_width()
    ax4.text(w+0.05,bar.get_y()+bar.get_height()/2,
             f"${w:.2f}M\n({row['Churned Customers']:,} customers)",
             va="center",ha="left",color=C["text"],fontsize=8.5,fontweight="bold")
ax4.set_yticks(y4); ax4.set_yticklabels(rev_df["Segment"],color=C["text"],fontsize=9)
ax4.tick_params(axis="x",colors=C["subtext"]); ax4.tick_params(axis="y",colors=C["text"])
ax4.set_xlabel("Annual Revenue at Risk ($M)",color=C["subtext"],fontsize=9)
ax4.set_xlim(0,(rev_df["Annual Revenue at Risk"]/1_000_000).max()*1.6)
ax4.set_title("Annual Revenue at Risk\nby Churn Segment",color=C["text"],fontsize=11,fontweight="bold",pad=10,loc="left")
total_rev=rev_df["Annual Revenue at Risk"].sum()
ax4.text(0.97,0.05,f"Total at risk\n${total_rev/1_000_000:.2f}M / year",
         transform=ax4.transAxes,ha="right",va="bottom",
         color=C["highlight"],fontsize=11,fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.4",facecolor=C["bg"],edgecolor=C["highlight"],alpha=0.9))

plt.savefig("overcharge_analysis.png",dpi=180,bbox_inches="tight",facecolor=C["bg"])
print(f"✓ Saved: overcharge_analysis.png")
plt.show()