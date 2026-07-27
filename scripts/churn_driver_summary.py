# ==============================================================================
# CHURN DRIVER SUMMARY & BRIDGE TO MODELING
# ==============================================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

overall_churn_rate = (df['Churn Label'] == 'Yes').mean()
print(f"Overall Churn Rate (baseline): {overall_churn_rate:.1%}\n")

# --- 1. Bin Customer Service Calls (raw counts are too sparse at the high end) ---
df['CS Calls (Binned)'] = pd.cut(
    df['Customer Service Calls'],
    bins=[-1, 0, 1, 2, 3, 4, 100],
    labels=['0', '1', '2', '3', '4', '5+']
)

# --- 2. Compute churn rate spread (max - min) for a given feature ---
def churn_rate_spread(column, min_group_size=20):
    rates = df.groupby(column, observed=True)['Churn Label'].apply(lambda x: (x == 'Yes').mean())
    counts = df.groupby(column, observed=True).size()
    valid = rates[counts >= min_group_size]
    return valid.max() - valid.min() if not valid.empty else 0.0

# --- 3. Candidate features to rank (marginal effect only, not joint effects) ---
features = {
    "Contract Type": "Contract Type",
    "Customer Service Calls": "CS Calls (Binned)",
    "Payment Method": "Payment Method",
    "Group": "Group",
    "Senior": "Senior",
    "Under 30": "Under 30",
    "Intl Plan": "Intl Plan",
    "Unlimited Data Plan": "Unlimited Data Plan",
}

spread_df = pd.DataFrame([
    {"Feature": name, "Churn Rate Spread": churn_rate_spread(col)}
    for name, col in features.items() if col in df.columns
]).sort_values("Churn Rate Spread", ascending=False)

# --- 4. Assign Impact tier from spread, and Actionability from business judgment ---
def impact_tier(spread):
    if spread >= 0.30: return "Very High"
    if spread >= 0.15: return "High"
    if spread >= 0.05: return "Medium"
    return "Low"

actionability = {
    "Contract Type": "Very High", "Customer Service Calls": "Very High",
    "Payment Method": "Medium", "Group": "High", "Senior": "Low",
    "Under 30": "Low", "Intl Plan": "Very High", "Unlimited Data Plan": "Very High",
}

spread_df["Impact"] = spread_df["Churn Rate Spread"].apply(impact_tier)
spread_df["Actionability"] = spread_df["Feature"].map(actionability)

driver_summary = spread_df.reset_index(drop=True)
driver_summary.index = driver_summary.index + 1
driver_summary.index.name = "Rank"

print("CHURN DRIVER SUMMARY")
print("=" * 60)
print(driver_summary.to_string())

# --- 5. Visualization ---
plt.figure(figsize=(10, 6))
sns.barplot(data=driver_summary.reset_index(), x="Churn Rate Spread", y="Feature",
            hue="Feature", palette="viridis", legend=False)
plt.title("Churn Driver Summary — Rate Spread by Feature", fontweight="bold")
plt.xlabel("Churn Rate Spread (Max Category - Min Category)")
plt.ylabel("")
plt.tight_layout()
plt.savefig("outputs/churn_driver_summary.png", dpi=150, bbox_inches="tight")
plt.show()

# --- 6. Notes ---
print("\nNote: 'Churn Category' excluded — post-outcome variable (label leakage).")
print("Note: 'Intl Plan' shows low marginal spread here, but a much larger effect")
