import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

# Attempt to load SHAP for explainability
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# --- 1. Page Configuration & Custom CSS ---
st.set_page_config(
    page_title="Customer Churn Prediction",
    layout="wide",
    initial_sidebar_state="expanded"
)

# UI CSS Injection
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .st-tabs { font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #2c3e50; }
    </style>
""", unsafe_allow_html=True)

# --- 2. Core Resource Caching ---
@st.cache_resource(show_spinner="Loading XGBoost Core...")
def load_model() -> Any:
    """Loads and caches the pre-trained XGBoost model."""
    return joblib.load('xgboost_churn_model.pkl')

try:
    model = load_model()
except Exception as e:
    st.error(f"⚠️ Critical System Error: Model binary missing. Error details: {e}")
    st.stop()

# --- 3. Business Logic Engines ---
def segment_risk(probability: float) -> str:
    """Classifies mathematical probability into business risk segments.
    Note: these are display-only granular tiers, independent of the binary
    Churn/Retained classification threshold set in the sidebar."""
    if probability < 0.25: return '🟢 Low Risk'
    elif probability < 0.50: return '🟡 Medium Risk'
    elif probability < 0.75: return '🟠 High Risk'
    else: return '🔴 Critical Risk'

def generate_recommendation(row: pd.Series) -> str:
    """Generates tailored retention strategies based on customer features."""
    prob = row.get('Churn_Probability', 0)
    calls = row.get('Customer Service Calls', 0)
    contract = str(row.get('Contract Type', ''))
    monthly_charge = row.get('Monthly Charge', 0)
    intl_charge = row.get('Extra International Charges', 0)

    recs = []
    if prob > 0.80:
        recs.append("Immediate executive retention campaign.")
    if calls > 4:
        recs.append("Assign to premium tier customer support.")
    if 'Month-to-Month' in contract:
        recs.append("Offer 15% annual contract migration discount.")
    if monthly_charge > 80:  # Assuming 80 is a high threshold
        recs.append("Initiate personalized pricing audit.")
    if intl_charge > 10:
        recs.append("Propose unlimited international package.")

    return " | ".join(recs) if recs else "Standard lifecycle monitoring."

def calculate_priority_score(prob: float, charge: float, max_charge: float) -> int:
    """
    Calculates a 1-100 priority score heavily weighting churn probability,
    adjusted by the customer's financial value.
    """
    normalized_charge = (charge / max_charge) if max_charge > 0 else 0
    score = (prob * 0.7 + normalized_charge * 0.3) * 100
    return min(max(int(score), 1), 100)

# --- 4. Data Validation & Preprocessing Pipeline ---
@st.cache_data(show_spinner=False)
def process_data(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Validates data, applies existing encoding mappings, and handles missing values."""
    if df.empty:
        st.warning("⚠️ The uploaded file is empty.")
        return None

    df = df.drop_duplicates().copy()

    # Clean column names dynamically
    df.columns = df.columns.astype(str).str.strip()
    raw_columns_lower = {col.lower(): col for col in df.columns}

    # Target Schema Maps (Preserving Original Architecture)
    target_categorical = {
        'intl plan': 'Intl Plan',
        'contract type': 'Contract Type',
        'payment method': 'Payment Method'
    }
    target_numerical = {
        'customer service calls': 'Customer Service Calls',
        'monthly charge': 'Monthly Charge',
        'account length (in months)': 'Account Length (in months)',
        'avg monthly gb download': 'Avg Monthly GB Download',
        'group': 'Group',
        'extra international charges': 'Extra International Charges',
        'intl calls': 'Intl Calls'
    }

    # Dynamic Renaming
    rename_map = {raw_columns_lower[k]: v for k, v in {**target_categorical, **target_numerical}.items() if k in raw_columns_lower}
    df = df.rename(columns=rename_map)

    base_categorical = [name for name in target_categorical.values() if name in df.columns]
    base_numerical = [name for name in target_numerical.values() if name in df.columns]
    available_features = base_numerical + base_categorical

    if not available_features:
        st.error("⚠️ Validation Failed: No recognized features found in the dataset.")
        return None

    # Enforce safe data types & impute NaNs
    for col in base_numerical:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    for col in base_categorical:
        df[col] = df[col].fillna('Unknown')

    X_raw = df[available_features].copy()
    X_encoded = pd.get_dummies(X_raw, columns=base_categorical)

    # Align with model input dimensions dynamically
    try:
        expected_features = model.feature_names_in_.tolist()
    except AttributeError:
        expected_features = [
            'Customer Service Calls', 'Contract Type_Two Year', 'Group',
            'Contract Type_One Year', 'Avg Monthly GB Download',
            'Extra International Charges', 'Account Length (in months)',
            'Payment Method_Direct Debit', 'Intl Calls', 'Monthly Charge'
        ]

    X_final = X_encoded.reindex(columns=expected_features, fill_value=0)
    for col in X_final.columns:
        if X_final[col].dtype == 'bool':
            X_final[col] = X_final[col].astype(int)
        elif X_final[col].dtype == 'object':
            X_final[col] = pd.to_numeric(X_final[col], errors='coerce').fillna(0)

    return df, X_final, available_features

# --- 5. Application Interface ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3121/3121693.png", width=80)
st.sidebar.title("Customer Churn Prediction")
st.sidebar.markdown("Upload your data for analysis and prediction")

uploaded_file = st.sidebar.file_uploader("📂 Ingest Data (CSV/XLSX)", type=["csv", "xlsx"])

# --- 5.1 Configurable Churn Classification Threshold ---
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Model Settings")
CHURN_THRESHOLD = st.sidebar.slider(
    "Churn Classification Threshold",
    min_value=0.10, max_value=0.90, value=0.40, step=0.05,
    help="Lower values catch more at-risk customers (higher recall) at the cost of more false alarms (lower precision). "
         "Default of 0.40 is based on validated threshold-sensitivity analysis."
)

# Reference tradeoff figures from notebook validation (static reference, not live-computed)
threshold_reference = {
    0.40: {"precision": 0.68, "recall": 0.91},
    0.50: {"precision": 0.75, "recall": 0.88},
}
closest_ref = min(threshold_reference.keys(), key=lambda t: abs(t - CHURN_THRESHOLD))
ref_vals = threshold_reference[closest_ref]
st.sidebar.caption(
    f"Reference @ {closest_ref:.2f}: Precision ≈ {ref_vals['precision']:.2f}, Recall ≈ {ref_vals['recall']:.2f}\n\n"
    f"(At 0.40: Recall 91% / Precision 68% | At 0.50: Recall 88% / Precision 75%)"
)

st.title("Customer Churn Prediction")
st.markdown("A customer churn prediction dashboard powered by an XGBoost model to identify at-risk accounts and recommend retention strategies.")

if uploaded_file:
    # Standard Streamlit File Reading
    try:
        if uploaded_file.name.endswith('.csv'):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)

    except Exception as e:
        st.error(f"❌ File parsing failed: {e}")
        st.stop()

    processed_data = process_data(raw_df)

    if processed_data:
        df, X_final, avail_features = processed_data

        with st.spinner("Executing Inference Pipeline..."):
            try:
                # Compute probability first, then classify using the sidebar threshold
                # instead of relying on the model's internal default (0.5) via .predict()
                df['Churn_Probability'] = model.predict_proba(X_final)[:, 1]
                df['Churn_Prediction'] = (df['Churn_Probability'] >= CHURN_THRESHOLD).astype(int)
                df['Status'] = df['Churn_Prediction'].apply(lambda x: 'Churn' if x == 1 else 'Retained')

                # Apply Business Logic
                df['Risk Level'] = df['Churn_Probability'].apply(segment_risk)
                max_charge = df['Monthly Charge'].max() if 'Monthly Charge' in df.columns else 1
                df['Priority Score'] = df.apply(lambda x: calculate_priority_score(x['Churn_Probability'], x.get('Monthly Charge', 0), max_charge), axis=1)
                df['Recommendation'] = df.apply(generate_recommendation, axis=1)

            except Exception as e:
                st.error(f"❌ Inference Pipeline Failed. Dimension mismatch error: {e}")
                st.stop()

        # Dynamic Filters
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Active Filters")
        risk_filter = st.sidebar.multiselect("Filter by Risk Level", options=df['Risk Level'].unique(), default=df['Risk Level'].unique())

        # Apply filters safely
        filtered_df = df[df['Risk Level'].isin(risk_filter)]

        # --- UI Tabs Setup ---
        tab_exec, tab_analytics, tab_shap, tab_export = st.tabs([
            "📊 Executive Summary",
            "📈 Advanced Analytics",
            "🧠 Model Explainability",
            "💾 Data & Export"
        ])

        # ---------------- TAB 1: EXECUTIVE SUMMARY ----------------
        with tab_exec:
            st.subheader("C-Suite Overview")
            st.caption(f"Classification threshold currently set to {CHURN_THRESHOLD:.2f} — adjustable in the sidebar.")

            total_customers = len(filtered_df)
            critical_risk = len(filtered_df[filtered_df['Risk Level'] == '🔴 Critical Risk'])
            high_risk = len(filtered_df[filtered_df['Risk Level'] == '🟠 High Risk'])
            churned_count = len(filtered_df[filtered_df['Status'] == 'Churn'])

            rev_at_risk = 0
            if 'Monthly Charge' in filtered_df.columns:
                rev_at_risk = filtered_df[filtered_df['Risk Level'].isin(['🔴 Critical Risk', '🟠 High Risk'])]['Monthly Charge'].sum()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👥 Total Analyzed", f"{total_customers:,}")
            c2.metric("🚩 Flagged as Churn", f"{churned_count:,}")
            c3.metric("📉 Avg Risk Score", f"{filtered_df['Churn_Probability'].mean():.1%}")
            c4.metric("💰 Est. Revenue at Risk", f"${rev_at_risk:,.2f}" if rev_at_risk else "N/A")

            st.markdown("---")
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                fig_risk = px.pie(filtered_df, names='Risk Level', title='Risk Segmentation Distribution',
                                  color='Risk Level',
                                  color_discrete_map={
                                      '🔴 Critical Risk': '#d32f2f', '🟠 High Risk': '#f57c00',
                                      '🟡 Medium Risk': '#fbc02d', '🟢 Low Risk': '#388e3c'
                                  }, hole=0.4)
                st.plotly_chart(fig_risk, use_container_width=True)

            with col_chart2:
                if 'Customer Service Calls' in filtered_df.columns:
                    fig_calls = px.box(filtered_df, x='Risk Level', y='Customer Service Calls',
                                       title='Service Strain by Risk Level',
                                       color='Risk Level')
                    st.plotly_chart(fig_calls, use_container_width=True)

        # ---------------- TAB 2: ADVANCED ANALYTICS ----------------
        with tab_analytics:
            st.subheader("Granular Cohort Analysis")
            r1c1, r1c2 = st.columns(2)

            with r1c1:
                if 'Contract Type' in filtered_df.columns:
                    fig_contract = px.histogram(filtered_df, x='Contract Type', color='Risk Level',
                                                barmode='stack', title='Risk Exposure by Contract Type')
                    st.plotly_chart(fig_contract, use_container_width=True)
                else:
                    st.info("💡 'Contract Type' not found in dataset.")

            with r1c2:
                if 'Monthly Charge' in filtered_df.columns:
                    fig_charge = px.scatter(filtered_df, x='Monthly Charge', y='Churn_Probability',
                                            color='Risk Level', title='Financial Profile vs. Churn Probability',
                                            hover_data=['Customer Service Calls'] if 'Customer Service Calls' in filtered_df.columns else [])
                    st.plotly_chart(fig_charge, use_container_width=True)

            st.markdown("---")
            st.subheader("Top 20 Highest Priority Customers")
            top_20 = filtered_df.sort_values(by='Priority Score', ascending=False).head(20)

            display_cols_top = ['Risk Level', 'Priority Score', 'Churn_Probability']
            if 'Monthly Charge' in top_20.columns: display_cols_top.append('Monthly Charge')
            if 'Customer Service Calls' in top_20.columns: display_cols_top.append('Customer Service Calls')

            st.dataframe(
                top_20[display_cols_top],
                use_container_width=True,
                column_config={"Churn_Probability": st.column_config.ProgressColumn("Risk", format="%.2f", min_value=0.0, max_value=1.0)}
            )

        # ---------------- TAB 3: SHAP & EXPLAINABILITY ----------------
        with tab_shap:
            st.subheader("Model Explainability Engine")
            col_f1, col_f2 = st.columns([1, 1])

            with col_f1:
                try:
                    importances = model.feature_importances_
                    feat_names = X_final.columns
                    imp_df = pd.DataFrame({'Feature': feat_names, 'Importance': importances}).sort_values(by='Importance', ascending=True).tail(15)

                    fig_imp = px.bar(imp_df, x='Importance', y='Feature', orientation='h',
                                     title='Top Global Predictive Features (Gain)',
                                     color_discrete_sequence=['#2980b9'])
                    st.plotly_chart(fig_imp, use_container_width=True)
                    st.caption("Note: gain-based importance can overweight features that are redundant with others "
                               "(e.g., a raw count and its binned equivalent). SHAP (right) provides more reliable, "
                               "per-prediction attribution.")
                except AttributeError:
                    st.info("💡 Built-in feature importance is unavailable for this specific model architecture.")

            with col_f2:
                if SHAP_AVAILABLE:
                    with st.spinner("Generating local SHAP explanations..."):
                        try:
                            # 1. Initialize Explainer and sample data for memory efficiency
                            explainer = shap.TreeExplainer(model)
                            shap_sample = X_final.sample(n=min(100, len(X_final)), random_state=42)

                            # For XGBoost, shap_values might be a list (for multiclass) or array (binary).
                            # We extract the relevant array for binary classification.
                            shap_values = explainer.shap_values(shap_sample)
                            if isinstance(shap_values, list):
                                shap_values = shap_values[1] # Target class (Churn)

                            st.markdown("**SHAP Global Summary (Feature Impact)**")

                            # 2. Render SHAP plot using Matplotlib inside Streamlit
                            fig, ax = plt.subplots(figsize=(8, 6))
                            shap.summary_plot(shap_values, shap_sample, show=False)
                            st.pyplot(fig, clear_figure=True)

                        except Exception as e:
                            st.warning(f"SHAP explainer not compatible with this tree format: {e}")
                else:
                    st.warning("⚠️ `shap` library is not installed in the current environment.")


        # ---------------- TAB 4: DATA TABLE & EXPORT ----------------
        with tab_export:
            st.subheader("Actionable Data Roster")

            export_df = filtered_df.sort_values(by='Priority Score', ascending=False)

            # Organize columns for optimal export UX
            front_cols = ['Risk Level', 'Priority Score', 'Churn_Probability', 'Recommendation', 'Status']
            back_cols = [c for c in export_df.columns if c not in front_cols and c not in ['Churn_Prediction']]
            final_display_df = export_df[front_cols + back_cols]

            st.dataframe(
                final_display_df,
                use_container_width=True,
                height=400
            )

            csv = final_display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Export Actionable CRM Roster (CSV)",
                data=csv,
                file_name='customer_churn_report.csv',
                mime='text/csv',
                type="primary"
            )

else:
    st.info("Please establish a data connection via the sidebar to initialize the workspace.")
