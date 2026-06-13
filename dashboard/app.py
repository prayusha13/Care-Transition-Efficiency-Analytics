import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from streamlit_option_menu import option_menu

st.set_page_config(
    page_title="Care Transition Analytics",
    page_icon="📊",
    layout="wide"
)
st.markdown("""
<style>
.metric-container {
    border-radius: 10px;
    padding: 15px;
    background-color: #1E293B;
}
</style>
""", unsafe_allow_html=True)
from pathlib import Path

@st.cache_data
def load_data():

    DATA_FILE = (
        Path(__file__).parent.parent
        / "data"
        / "HHS_Unaccompanied_Alien_Children_Program.csv"
    )

    df = pd.read_csv(DATA_FILE)

    df = df.dropna(how='all')

    df['Date'] = pd.to_datetime(df['Date'])

    df['Children in HHS Care'] = (
        df['Children in HHS Care']
        .astype(str)
        .str.replace(',', '')
    )

    df['Children in HHS Care'] = pd.to_numeric(
        df['Children in HHS Care']
    )

    df = df.sort_values('Date')

    return df

df = load_data()
df['Transfer Efficiency Ratio'] = (
    df['Children transferred out of CBP custody']
    /
    df['Children in CBP custody']
)

df['Discharge Effectiveness'] = (
    df['Children discharged from HHS Care']
    /
    df['Children in HHS Care']
)

df['Pipeline Throughput'] = (
    df['Children discharged from HHS Care']
    /
    df['Children apprehended and placed in CBP custody*']
)

df['Backlog'] = (
    df['Children apprehended and placed in CBP custody*']
    -
    df['Children discharged from HHS Care']
)

df.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)
with st.sidebar:

    selected = option_menu(
        menu_title="Navigation",
        options=[
            "Overview",
            "Efficiency",
            "Bottlenecks",
            "Forecasting",
            "Recommendations"
        ],
        icons=[
            "house",
            "graph-up",
            "exclamation-triangle",
            "activity",
            "clipboard-data"
        ],
        default_index=0
    )
st.title(
    "📊 Care Transition Efficiency & Placement Outcome Analytics"
)

st.markdown("""
Monitoring transfer efficiency,
placement outcomes,
pipeline bottlenecks,
and future care transition risks.
""")
col1,col2,col3,col4,col5 = st.columns(5)
with col1:

    st.metric(
        "Transfer Efficiency",
        f"{df['Transfer Efficiency Ratio'].mean()*100:.1f}%"
    )
with col2:

    st.metric(
        "Discharge Effectiveness",
        f"{df['Discharge Effectiveness'].mean()*100:.2f}%"
    )
with col3:

    st.metric(
        "Average Backlog",
        round(df['Backlog'].mean(),1)
    )
health_score = 16.75

with col4:

    st.metric(
        "Health Score",
        health_score
    )
avg_backlog = df['Backlog'].mean()

if avg_backlog > 0:
    risk = "🔴 High"

elif avg_backlog > -50:
    risk = "🟡 Moderate"

else:
    risk = "🟢 Low"

with col5:

    st.metric(
        "Risk Status",
        risk
    )
# ======================================================
# OVERVIEW PAGE
# ======================================================

if selected == "Overview":

    st.markdown("---")

    st.subheader("📈 Care Pipeline Overview")

    colA, colB = st.columns(2)

    with colA:
        start_date = st.date_input(
            "Start Date",
            df["Date"].min()
        )

    with colB:
        end_date = st.date_input(
            "End Date",
            df["Date"].max()
        )

    filtered_df = df[
        (df["Date"] >= pd.to_datetime(start_date))
        &
        (df["Date"] <= pd.to_datetime(end_date))
    ]

    fig = px.line(
        filtered_df,
        x="Date",
        y=[
            "Children apprehended and placed in CBP custody*",
            "Children discharged from HHS Care"
        ],
        title="Daily Inflow vs Outflow"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader("🔄 Care Pipeline Flow")

    avg_transferred = filtered_df[
        "Children transferred out of CBP custody"
    ].mean()

    avg_discharged = filtered_df[
        "Children discharged from HHS Care"
    ].mean()

    sankey_fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=20,
                    thickness=20,
                    label=[
                        "CBP Custody",
                        "HHS Care",
                        "Sponsor Placement"
                    ]
                ),
                link=dict(
                    source=[0, 1],
                    target=[1, 2],
                    value=[
                        avg_transferred,
                        avg_discharged
                    ]
                )
            )
        ]
    )

    sankey_fig.update_layout(
        title="Average Care Transition Flow",
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(
        sankey_fig,
        use_container_width=True
    )

    st.info(
        f"""
        Average Transfer Efficiency: {df['Transfer Efficiency Ratio'].mean()*100:.1f}%

        Average Discharge Effectiveness: {df['Discharge Effectiveness'].mean()*100:.2f}%

        Average Backlog: {df['Backlog'].mean():.1f}

        The system generally maintained negative backlog levels,
        indicating outflows often exceeded inflows.
        """
    )
# ======================================================
# EFFICIENCY PAGE
# ======================================================

elif selected == "Efficiency":

    st.subheader("📈 Efficiency Analytics")

    col1, col2 = st.columns(2)

    with col1:

        fig1 = px.line(
            df,
            x="Date",
            y="Transfer Efficiency Ratio",
            title="Transfer Efficiency Over Time"
        )

        fig1.update_layout(
            template="plotly_dark",
            height=500
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    with col2:

        fig2 = px.line(
            df,
            x="Date",
            y="Discharge Effectiveness",
            title="Discharge Effectiveness Over Time"
        )

        fig2.update_layout(
            template="plotly_dark",
            height=500
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    st.subheader("Monthly Efficiency Trends")

    monthly = df.copy()

    monthly["Month"] = monthly["Date"].dt.to_period("M").astype(str)

    monthly_eff = (
    monthly.groupby("Month")
    .agg({
        "Transfer Efficiency Ratio": "mean",
        "Discharge Effectiveness": "mean"
    })
    .reset_index()
)
    fig3 = px.line(
        monthly_eff,
        x="Month",
        y=[
            "Transfer Efficiency Ratio",
            "Discharge Effectiveness"
        ],
        title="Monthly Efficiency Trends"
    )

    fig3.update_layout(
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )
# ======================================================
# BOTTLENECKS PAGE
# ======================================================

elif selected == "Bottlenecks":

    st.subheader("🚦 Bottleneck Detection & Backlog Analysis")

    df["Bottleneck"] = df["Backlog"] > 0

    bottleneck_days = df["Bottleneck"].sum()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Days with Bottlenecks",
            int(bottleneck_days)
        )

    with col2:
        st.metric(
            "Average Backlog",
            round(df["Backlog"].mean(), 1)
        )

    st.markdown("---")

    fig = px.line(
        df,
        x="Date",
        y="Backlog",
        title="Backlog Trend Over Time"
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="red"
    )

    fig.update_layout(
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader("Monthly Backlog Analysis")

    monthly_backlog = (
        df.assign(
            Month=df["Date"].dt.to_period("M").astype(str)
        )
        .groupby("Month")["Backlog"]
        .mean()
        .reset_index()
    )

    fig2 = px.bar(
        monthly_backlog,
        x="Month",
        y="Backlog",
        title="Average Monthly Backlog"
    )

    fig2.update_layout(
        template="plotly_dark",
        height=500
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    if df["Backlog"].mean() < 0:

        st.success(
            "Pipeline generally processed more children than entered the system, indicating low backlog risk."
        )

    else:

        st.warning(
            "Backlog accumulation detected. Further investigation is recommended."
        )
# ======================================================
# FORECASTING PAGE
# ======================================================

elif selected == "Forecasting":

    st.subheader("🔮 Forecasting & Future Outlook")

    from sklearn.linear_model import LinearRegression

    forecast_df = df[
        ["Date", "Transfer Efficiency Ratio"]
    ].copy()

    forecast_df["Day_Number"] = np.arange(
        len(forecast_df)
    )

    X = forecast_df[["Day_Number"]]
    y = forecast_df["Transfer Efficiency Ratio"]

    model = LinearRegression()
    model.fit(X, y)

    future_days = np.arange(
        len(forecast_df),
        len(forecast_df) + 30
    ).reshape(-1, 1)

    future_predictions = model.predict(
        future_days
    )

    future_dates = pd.date_range(
        start=df["Date"].max() + pd.Timedelta(days=1),
        periods=30
    )

    forecast_plot = pd.DataFrame({
        "Date": future_dates,
        "Forecast": future_predictions
    })

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Transfer Efficiency Ratio"],
            mode="lines",
            name="Historical"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=forecast_plot["Date"],
            y=forecast_plot["Forecast"],
            mode="lines",
            name="Forecast"
        )
    )

    fig.update_layout(
        title="30-Day Transfer Efficiency Forecast",
        template="plotly_dark",
        height=550
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    predicted_avg = round(
        forecast_plot["Forecast"].mean() * 100,
        1
    )

    current_avg = round(
        df["Transfer Efficiency Ratio"].tail(30).mean() * 100,
        1
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Current 30-Day Average",
            f"{current_avg}%"
        )

    with col2:
        st.metric(
            "Predicted Next 30 Days",
            f"{predicted_avg}%"
        )

    st.markdown("---")

    if predicted_avg < 50:

        st.error(
            f"""
            ⚠ Risk Alert

            Transfer Efficiency is projected to remain
            below 50%.

            Operational review may be required.
            """
        )

    else:

        st.success(
            f"""
            ✅ Forecast indicates stable
            transfer efficiency performance.
            """
        )

    st.info(
        """
        Forecast generated using a Linear Regression model
        trained on historical transfer efficiency trends.

        The forecast provides an early warning indicator
        for potential future process inefficiencies.
        """
    )
# ======================================================
# RECOMMENDATIONS PAGE
# ======================================================

elif selected == "Recommendations":

    st.subheader("📋 Executive Recommendations")

    st.success(
        """
        Recommendation 1

        Monitor transfer efficiency closely following the
        significant decline observed during 2025.
        """
    )

    st.info(
        """
        Recommendation 2

        Investigate operational or policy changes that
        coincided with the sharp efficiency reduction
        beginning in early 2025.
        """
    )

    st.warning(
        """
        Recommendation 3

        Continue monitoring backlog levels to ensure
        inflows and outflows remain balanced.
        """
    )

    st.success(
        """
        Recommendation 4

        Utilize forecasting outputs as an early-warning
        system for future bottlenecks and placement delays.
        """
    )

    st.info(
        """
        Recommendation 5

        Implement routine efficiency monitoring dashboards
        for decision-makers to support data-driven process
        improvements.
        """
    )

    st.markdown("---")

    st.subheader("Project Summary")

    st.write(
        """
        This dashboard evaluates the effectiveness of the
        care transition pipeline by analyzing transfer
        efficiency, discharge outcomes, backlog behavior,
        bottlenecks, and future performance trends.

        Results indicate that while the system generally
        maintained low backlog levels, transfer efficiency
        declined substantially during 2025 and should be
        monitored closely.
        """
    )
st.markdown("---")

st.caption(
    "Care Transition Efficiency & Placement Outcome Analytics | Unified Mentor Project | Developed by Prayusha Subedi"
)
