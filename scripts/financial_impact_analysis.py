#financial_impact_analysis
total_customers = len(df)
total_churners  = (df["Churn Label"] == "Yes").sum()
overall_rate    = total_churners / total_customers * 100

df = df.copy()
df["Churned"] = (df["Churn Label"] == "Yes").astype(int)

churners_df  = df[df["Churned"] == 1].copy()
retained_df  = df[df["Churned"] == 0].copy()

avg_monthly       = churners_df["Monthly Charge"].mean()
total_annual_risk = int(total_churners * avg_monthly * 12)

# ── 2. REVENUE AT RISK BY CHURN CATEGORY ──────────────────────────────────────
cat_df = (churners_df.groupby("Churn Category")
                     .agg(Churners=("Monthly Charge","count"),
                          Avg_Monthly=("Monthly Charge","mean"))
                     .reset_index())
cat_df.columns = ["Category","Churners","Avg Monthly"]
cat_df["Annual Rev at Risk"] = (cat_df["Churners"] * cat_df["Avg Monthly"] * 12).astype(int)
cat_df = cat_df.sort_values("Annual Rev at Risk", ascending=True).reset_index(drop=True)

# ── 3. REVENUE AT RISK BY CONTRACT TYPE ───────────────────────────────────────
contract_df = (churners_df.groupby("Contract Type")
                          .agg(Churners=("Monthly Charge","count"),
                               Avg_Monthly=("Monthly Charge","mean"))
                          .reset_index())
contract_df.columns = ["Contract","Churners","Avg Monthly"]
contract_df["Annual Rev at Risk"] = (contract_df["Churners"] * contract_df["Avg Monthly"] * 12).astype(int)
contract_df = contract_df.sort_values("Annual Rev at Risk", ascending=True).reset_index(drop=True)

# ── 4. MONTHLY CHARGE TIER × CHURN RATE ──────────────────────────────────────
charge_bins   = [0, 20, 40, 60, 80, 100, 9999]
charge_labels = ["<20","20-40","40-60","60-80","80-100","100+"]
df["Charge Tier"] = pd.cut(df["Monthly Charge"],
                            bins=charge_bins, labels=charge_labels)
mc_df = (df.groupby("Charge Tier", observed=True)
           .agg(Total=("Churned","count"),
                Churned=("Churned","sum"))
           .reset_index())
mc_df.columns = ["Bucket","Total","Churned"]
mc_df["Churn Rate"] = (mc_df["Churned"] / mc_df["Total"] * 100).round(1)

# ── 5. RETENTION ROI SCENARIOS ────────────────────────────────────────────────
retention_cost_per_customer = 150   # adjust to your business
pct_scenarios = [0.10, 0.20, 0.30, 0.40, 0.50]
scenario_rows = []
for pct in pct_scenarios:
    saved      = int(total_churners * pct)
    rev_saved  = int(saved * avg_monthly * 12)
    cost       = int(saved * retention_cost_per_customer)
    net_roi    = rev_saved - cost
    scenario_rows.append({
        "Scenario":          f"Retain {int(pct*100)}%",
        "Customers Saved":   saved,
        "Annual Rev Saved":  rev_saved,
        "Cost of Retention": cost,
        "Net ROI":           net_roi,
    })
scenario_df = pd.DataFrame(scenario_rows)

# ── 6. PALETTE ────────────────────────────────────────────────────────────────
C = {
    "bg":"#0F1B2D","panel":"#162236","text":"#EAEEF4","subtext":"#7A8FA6",
    "grid":"#1E3048","churn":"#E8533F","highlight":"#F5A623",
    "safe":"#7BC67E","a1":"#4A90D9","a2":"#B07FD4","warn":"#F2994A",
}
CAT_COLS = {
    "Competitor":"#E8533F","Dissatisfaction":"#4A90D9",
    "Price":"#F2994A","Attitude":"#B07FD4","Other":"#7A8FA6",
}

# ── 7. HELPERS ────────────────────────────────────────────────────────────────
def style_h(ax):
    ax.set_facecolor(C["panel"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(axis="x",colors=C["subtext"],labelsize=8)
    ax.tick_params(axis="y",colors=C["text"],labelsize=9)
    ax.grid(axis="x",color=C["grid"],linewidth=0.6,zorder=0)
    ax.set_axisbelow(True)

def style_v(ax):
    ax.set_facecolor(C["panel"])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(axis="x",colors=C["text"],labelsize=9)
    ax.tick_params(axis="y",colors=C["subtext"],labelsize=8)
    ax.grid(axis="y",color=C["grid"],linewidth=0.6,zorder=0)
    ax.set_axisbelow(True)

def callout(ax, text, color, x=0.97, y=0.05, va="bottom"):
    ax.text(x,y,text,transform=ax.transAxes,ha="right",va=va,
            color=color,fontsize=9,fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4",facecolor=C["bg"],
                      edgecolor=color,alpha=0.9))

# ── 8. FIGURE ─────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(20,14), facecolor=C["bg"])

fig.text(0.04,0.955,"Financial Impact Sizing  —  Revenue at Risk",
         color=C["text"],fontsize=22,fontweight="bold",va="top")
fig.text(0.04,0.925,
         f"Total annual revenue at risk: "
         f"USD {total_annual_risk:,.0f}  |  "
         f"{total_churners:,} churners  |  "
         f"avg USD {avg_monthly:.0f}/month",
         color=C["highlight"],fontsize=11,fontweight="bold",va="top")

gs  = GridSpec(2,3,figure=fig,left=0.05,right=0.97,
               top=0.895,bottom=0.07,hspace=0.46,wspace=0.38)
ax1 = fig.add_subplot(gs[0,:2])
ax2 = fig.add_subplot(gs[0,2])
ax3 = fig.add_subplot(gs[1,:2])
ax4 = fig.add_subplot(gs[1,2])

# Chart 1 — Revenue at risk by churn category
style_h(ax1)
y1    = np.arange(len(cat_df))
cols1 = [CAT_COLS.get(c,C["a1"]) for c in cat_df["Category"]]
bars1 = ax1.barh(y1,cat_df["Annual Rev at Risk"]/1_000_000,
                 color=cols1,height=0.52,zorder=3)
max_v1=(cat_df["Annual Rev at Risk"]/1_000_000).max()
for bar,(_,row) in zip(bars1,cat_df.iterrows()):
    w=bar.get_width(); pct=row["Annual Rev at Risk"]/total_annual_risk*100
    ax1.text(w+max_v1*0.02,bar.get_y()+bar.get_height()/2,
             f"{w:.2f}M  ({pct:.1f}% of total)  "
             f"·  {row['Churners']:,} customers  "
             f"·  avg {row['Avg Monthly']:.0f}/mo",
             va="center",ha="left",color=C["text"],fontsize=8.5,fontweight="bold")
ax1.set_yticks(y1); ax1.set_yticklabels(cat_df["Category"],fontsize=11)
ax1.set_xlabel("Annual Revenue at Risk (USD M)",color=C["subtext"],fontsize=9)
ax1.set_xlim(0,max_v1*1.9)
ax1.set_title("Annual Revenue at Risk by Churn Category",
              color=C["text"],fontsize=13,fontweight="bold",pad=10,loc="left")
ax1.text(0.98,0.05,
         f"Total annual\nrevenue at risk\nUSD {total_annual_risk/1_000_000:.2f}M",
         transform=ax1.transAxes,ha="right",va="bottom",
         color=C["highlight"],fontsize=12,fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.45",facecolor=C["bg"],
                   edgecolor=C["highlight"],alpha=0.95))

# Chart 2 — Revenue at risk by contract type
style_h(ax2)
y2=np.arange(len(contract_df))
cols2=[C["a1"],C["warn"],C["churn"]][:len(contract_df)]
bars2=ax2.barh(y2,contract_df["Annual Rev at Risk"]/1_000_000,
               color=cols2,height=0.45,zorder=3)
max_v2=(contract_df["Annual Rev at Risk"]/1_000_000).max()
for bar,(_,row) in zip(bars2,contract_df.iterrows()):
    w=bar.get_width()
    ax2.text(w+max_v2*0.03,bar.get_y()+bar.get_height()/2,
             f"{w:.2f}M\n({row['Churners']:,} churners)",
             va="center",ha="left",color=C["text"],fontsize=8.5,fontweight="bold")
ax2.set_yticks(y2); ax2.set_yticklabels(contract_df["Contract"],fontsize=10)
ax2.set_xlabel("Annual Revenue at Risk (USD M)",color=C["subtext"],fontsize=9)
ax2.set_xlim(0,max_v2*1.75)
ax2.set_title("Revenue at Risk\nby Contract Type",
              color=C["text"],fontsize=11,fontweight="bold",pad=10,loc="left")
m2m_row=contract_df[contract_df["Contract"]=="Month-to-Month"]
if len(m2m_row):
    m2m_pct=m2m_row["Annual Rev at Risk"].values[0]/total_annual_risk*100
    callout(ax2,f"Month-to-Month\naccounts for\n{m2m_pct:.1f}% of\nrevenue at risk",C["churn"])

# Chart 3 — Retention ROI scenarios
style_v(ax3)
x3=np.arange(len(scenario_df)); bw=0.28
b_rev =ax3.bar(x3-bw,scenario_df["Annual Rev Saved"]/1_000,
               width=bw,color=C["safe"],zorder=3,label="Revenue Saved (K USD)")
b_cost=ax3.bar(x3,   scenario_df["Cost of Retention"]/1_000,
               width=bw,color=C["warn"],zorder=3,label="Retention Cost (K USD)")
b_roi =ax3.bar(x3+bw,scenario_df["Net ROI"]/1_000,
               width=bw,color=C["a1"], zorder=3,label="Net ROI (K USD)")
for bars in [b_rev,b_cost,b_roi]:
    for bar in bars:
        h=bar.get_height()
        ax3.text(bar.get_x()+bar.get_width()/2,h+4,f"{h:.0f}K",
                 ha="center",va="bottom",color=C["text"],fontsize=7.5,fontweight="bold")
for i,(_,row) in enumerate(scenario_df.iterrows()):
    mult=row["Annual Rev Saved"]/row["Cost of Retention"]
    ax3.text(i,row["Annual Rev Saved"]/1_000*1.09,f"{mult:.1f}x ROI",
             ha="center",va="bottom",color=C["highlight"],fontsize=8,fontweight="bold")
ax3.set_xticks(x3); ax3.set_xticklabels(scenario_df["Scenario"],color=C["text"],fontsize=10)
ax3.set_ylabel("Value (K USD)",color=C["subtext"],fontsize=9)
ax3.set_ylim(0,(scenario_df["Annual Rev Saved"]/1_000).max()*1.3)
ax3.set_title("Retention ROI Scenarios  —  What If We Retained X% of Churners?",
              color=C["text"],fontsize=12,fontweight="bold",pad=10,loc="left")
ax3.legend(loc="upper left",fontsize=8.5,frameon=False,labelcolor=C["text"])
ax3.text(0.01,0.01,
         f"Assumptions: retention cost = {retention_cost_per_customer} USD/customer  "
         f"|  avg monthly charge = {avg_monthly:.2f} USD  |  12-month revenue horizon",
         transform=ax3.transAxes,ha="left",va="bottom",
         color=C["subtext"],fontsize=7,style="italic")

# Chart 4 — Monthly charge tier vs churn rate
style_v(ax4)
x4=np.arange(len(mc_df))
cols4=[C["safe"] if r<=overall_rate else
       C["warn"] if r<=overall_rate*1.4 else
       C["churn"] for r in mc_df["Churn Rate"]]
bars4=ax4.bar(x4,mc_df["Churn Rate"],width=0.55,
              color=cols4,zorder=3,edgecolor=C["bg"],linewidth=0.5)
ax4.axhline(overall_rate,color=C["highlight"],linewidth=1.3,
            linestyle="--",zorder=4,alpha=0.85)
ax4.text(len(mc_df)-0.5,overall_rate+0.8,f"avg {overall_rate:.1f}%",
         color=C["highlight"],fontsize=7.5,ha="right",va="bottom")
for bar,(_,row) in zip(bars4,mc_df.iterrows()):
    h=bar.get_height()
    ax4.text(bar.get_x()+bar.get_width()/2,h+0.6,f"{h:.1f}%",
             ha="center",va="bottom",color=C["text"],fontsize=9.5,fontweight="bold")
    ax4.text(bar.get_x()+bar.get_width()/2,h*0.07,f"n={row['Total']:,}",
             ha="center",va="bottom",color="white",fontsize=7,alpha=0.7)
z4=np.polyfit(range(len(mc_df)),mc_df["Churn Rate"],1)
ax4.plot(x4,np.poly1d(z4)(x4),color=C["a1"],linewidth=1.5,
         linestyle="--",zorder=5,alpha=0.7)
ax4.set_xticks(x4)
ax4.set_xticklabels(mc_df["Bucket"],color=C["text"],fontsize=9,rotation=15,ha="right")
ax4.set_ylabel("Churn Rate (%)",color=C["subtext"],fontsize=9)
ax4.set_ylim(0,mc_df["Churn Rate"].max()*1.28)
ax4.set_title("Churn Rate by\nMonthly Charge Tier",
              color=C["text"],fontsize=11,fontweight="bold",pad=10,loc="left")
lo=mc_df.iloc[0]["Churn Rate"]; hi=mc_df.iloc[-1]["Churn Rate"]
callout(ax4,f"Higher payers churn more:\n100+ tier = {hi:.1f}%\nvs <20 tier = {lo:.1f}%",
        C["warn"],y=0.95,va="top")

plt.savefig("financial_impact_analysis.png",dpi=180,bbox_inches="tight",facecolor=C["bg"])
print(f"✓ Saved: financial_impact_analysis.png")
plt.show()