import streamlit as st
import pandas as pd
import plotly.express as px

# ============================
# PAGE CONFIGURATION
# ============================

st.set_page_config(
    page_title="Care Transition Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sleek Modern UI
st.markdown("""
<style>
    /* Metric / KPI Card Styling */
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .kpi-title {
        color: #64748b;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .kpi-value {
        color: #0f172a;
        font-size: 1.6rem;
        font-weight: 800;
    }

    /* Business Insight Card Styling */
    .insight-card {
        background-color: #ffffff;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .insight-title {
        font-weight: 700;
        color: #1e293b;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }
    .insight-desc {
        color: #475569;
        font-size: 0.88rem;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================
# DATA LOADING & CACHING
# ============================

@st.cache_data
def load_and_preprocess_data():
    df = pd.read_csv("data/healthcare.csv")
    df.dropna(how="all", inplace=True)

    # Convert Date column
    df["Date"] = pd.to_datetime(df["Date"])

    # List of all numeric columns used in calculations
    numeric_cols = [
        "Children transferred out of CBP custody",
        "Children in CBP custody",
        "Children discharged from HHS Care",
        "Children in HHS Care",
        "Children apprehended and placed in CBP custody*"
    ]

    # Clean and convert all numeric columns safely
    for col in numeric_cols:
        if col in df.columns:
            # Remove commas and non-numeric characters, then convert to numeric
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Set Date as index
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)

    # KPI Feature Engineering (Now safe to divide!)
    df["Transfer Efficiency Ratio"] = (
        df["Children transferred out of CBP custody"] / df["Children in CBP custody"].replace(0, pd.NA)
    )

    df["Discharge Effectiveness"] = (
        df["Children discharged from HHS Care"] / df["Children in HHS Care"].replace(0, pd.NA)
    )

    df["Pipeline Throughput Rate"] = (
        df["Children discharged from HHS Care"] / df["Children apprehended and placed in CBP custody*"].replace(0, pd.NA)
    )

    df["Backlog Accumulation"] = (
        df["Children apprehended and placed in CBP custody*"] - df["Children discharged from HHS Care"]
    )

    return df

df_raw = load_and_preprocess_data()


# ============================
# SIDEBAR CONTROLS
# ============================

st.sidebar.title("📊 Dashboard Options")
st.sidebar.markdown("---")

# Dynamic Date Filter
min_date = df_raw.index.min().to_pydatetime()
max_date = df_raw.index.max().to_pydatetime()

date_range = st.sidebar.date_input(
    "📅 Filter Analysis Period",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply Date Filtering safely
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    df = df_raw.loc[pd.to_datetime(start_date):pd.to_datetime(end_date)]
else:
    df = df_raw.copy()

st.sidebar.markdown("---")
st.sidebar.write("**Project:** Care Transition Analytics")
st.sidebar.write(f"**Records Loaded:** {len(df):,}")
st.sidebar.write(f"**Analysis Period:** {df.index.year.min()} - {df.index.year.max()}")

st.sidebar.markdown("---")
st.sidebar.info(
    "This dashboard analyzes care transition efficiency using operational KPIs and monthly trends."
)


# ============================
# KPI CALCULATIONS
# ============================

transfer_efficiency = df["Transfer Efficiency Ratio"].mean() * 100
discharge_effectiveness = df["Discharge Effectiveness"].mean() * 100

pipeline_throughput = (
    df["Children discharged from HHS Care"].sum()
    / df["Children apprehended and placed in CBP custody*"].sum()
) * 100

outcome_stability = df["Children discharged from HHS Care"].std()
average_backlog = df["Backlog Accumulation"].mean()


# ============================
# RESAMPLED MONTHLY DATA
# ============================

monthly_data = df.resample("ME").sum(numeric_only=True).reset_index()


# ============================
# HEADER & TITLE
# ============================

st.markdown("""
<div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px;">
    <span style="font-size: 2.3rem; line-height: 1;">📊</span>
    <h1 style="margin: 0; padding: 0; font-size: 2.2rem; font-weight: 700; color: #0f172a; line-height: 1.2;">
        Care Transition Efficiency & Placement Outcome Analytics
    </h1>
</div>
""", unsafe_allow_html=True)

# Subtle Dataset Badge / Source Subtitle
st.caption("📁 **Dataset:** HHS Unaccompanied Children Program (2023–2025)")

st.markdown("""
An interactive executive overview of operational efficiency, transfer rates, 
and monthly placement outcomes for the Unaccompanied Children Program.
""")

st.markdown("<br>", unsafe_allow_html=True)

# ============================
# KPI DISPLAY (CUSTOM CARDS)
# ============================

st.subheader("📈 Key Performance Indicators")

kpi_cols = st.columns(5)
kpi_metrics = [
    ("Transfer Efficiency", f"{transfer_efficiency:.2f}%"),
    ("Discharge Effectiveness", f"{discharge_effectiveness:.2f}%"),
    ("Pipeline Throughput", f"{pipeline_throughput:.2f}%"),
    ("Outcome Stability", f"{outcome_stability:.2f}"),
    ("Average Backlog", f"{average_backlog:.2f}")
]

for col, (title, val) in zip(kpi_cols, kpi_metrics):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{val}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ============================
# TREND CHARTS (2-COLUMN GRID)
# ============================

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📈 Monthly Children Apprehended")
    fig_app = px.area(
        monthly_data,
        x="Date",
        y="Children apprehended and placed in CBP custody*",
        markers=True,
        color_discrete_sequence=["#2563EB"]
    )
    fig_app.update_layout(
        height=380,
        template="plotly_white",
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title=None,
        yaxis_title="Apprehended Count"
    )
    st.plotly_chart(fig_app, use_container_width=True)

with chart_col2:
    st.subheader("📉 Monthly Children Discharged")
    fig_dis = px.area(
        monthly_data,
        x="Date",
        y="Children discharged from HHS Care",
        markers=True,
        color_discrete_sequence=["#0D9488"]
    )
    fig_dis.update_layout(
        height=380,
        template="plotly_white",
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title=None,
        yaxis_title="Discharged Count"
    )
    st.plotly_chart(fig_dis, use_container_width=True)

st.divider()


# ============================
# COMPARISON CHART
# ============================

st.subheader("📊 Monthly Apprehended vs. Discharged Comparison")

fig_comp = px.line(
    monthly_data,
    x="Date",
    y=[
        "Children apprehended and placed in CBP custody*",
        "Children discharged from HHS Care"
    ],
    markers=True,
    color_discrete_map={
        "Children apprehended and placed in CBP custody*": "#2563EB",
        "Children discharged from HHS Care": "#0D9488"
    }
)

fig_comp.update_layout(
    height=400,
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_title=None,
    yaxis_title="Volume Count"
)
st.plotly_chart(fig_comp, use_container_width=True)

st.divider()


# ============================
# BUSINESS INSIGHTS
# ============================

st.subheader("💡 Key Business Insights")

col_ins1, col_ins2 = st.columns(2)

with col_ins1:
    st.markdown("""
    <div class="insight-card">
        <div class="insight-title">⚡ Consistent Transfer Rates</div>
        <div class="insight-desc">Transfer Efficiency averaged <b>69.10%</b>, demonstrating steady operational handoff across facilities.</div>
    </div>
    <div class="insight-card">
        <div class="insight-title">📈 2024 Peak & Subsequent Decline</div>
        <div class="insight-desc">Monthly apprehensions peaked in early 2024 before experiencing a sharp downward trend entering 2025.</div>
    </div>
    """, unsafe_allow_html=True)

with col_ins2:
    st.markdown("""
    <div class="insight-card" style="border-left-color: #0D9488;">
        <div class="insight-title">🔄 High Pipeline Throughput</div>
        <div class="insight-desc">Throughput exceeded <b>100%</b>, reflecting significant discharges from backlog admitted prior to the observation window.</div>
    </div>
    <div class="insight-card" style="border-left-color: #0D9488;">
        <div class="insight-title">📉 Negative Backlog Trend</div>
        <div class="insight-desc">Average backlog accumulation remained negative, confirming that discharge velocity effectively outpaced incoming apprehensions.</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()


# ============================
# DATASET OVERVIEW
# ============================

st.subheader("📂 Dataset Overview")

# Clean formatting for table display
df_display = df.reset_index().copy()
df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d")

# Format floating metrics as clean percentages
df_display["Transfer Efficiency Ratio"] = df_display["Transfer Efficiency Ratio"].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "")
df_display["Discharge Effectiveness"] = df_display["Discharge Effectiveness"].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "")

st.dataframe(df_display.head(10), use_container_width=True, hide_index=True)

st.divider()


# ============================
# FOOTER
# ============================

st.markdown("""
<br><hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0 20px 0;">
<div style="
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
">
    <h4 style="margin: 0 0 6px 0; color: #1e293b; font-size: 1.1rem; font-weight: 700;">
        Care Transition Analytics Dashboard
    </h4>
    <p style="margin: 0 0 12px 0; color: #64748b; font-size: 0.88rem;">
        Developed by <b> Saif Chogle </b>
    </p>
    <div style="display: inline-block; background-color: #e2e8f0; height: 1px; width: 60px; margin-bottom: 12px;"></div>
    <br>
    <span style="
        background-color: #3b82f6;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    ">
        Developed as part of an AI/ML Internship • 2026
    </span>
</div>
<br>
""", unsafe_allow_html=True)