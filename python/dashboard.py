import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objects as go

# --- Layout & Title ---
st.set_page_config(page_title="Crypto Entry Dashboard", layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: #00BFA6;'>📈 Crypto Trade Entry Dashboard</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center; color: gray;'>Analyze entry signals and trade execution based on frequent price levels and directional movement</p>",
    unsafe_allow_html=True
)
st.markdown("---")

# --- Cached CSV Loaders (auto-refresh every 15 min) ---
@st.cache_data(ttl=900)
def load_main_data():
    return pd.read_csv("csv/tickers_ready_full.csv")

@st.cache_data(ttl=900)
def load_checked_data():
    path = "csv/tickers_ready_24h_checked.csv"
    return pd.read_csv(path) if os.path.exists(path) else None

# --- Manual refresh button ---
st.sidebar.markdown("### 🔄 Data Refresh")
if st.sidebar.button("Force reload now"):
    st.cache_data.clear()

# --- Load Data ---
file_path = "csv/tickers_ready_full.csv"
if not os.path.exists(file_path):
    st.warning("⚠️ File `tickers_ready_full.csv` not found. Run the analysis first.")
else:
    df = load_main_data()

    # --- Sidebar Filters ---
    st.sidebar.header("⚙️ Filters")
    tickers = st.sidebar.multiselect("Select tickers:", options=sorted(df["Ticker"].unique()), default=sorted(df["Ticker"].unique()))
    result_filter = st.sidebar.selectbox("Filter by trade result:", ["All", "Profitable", "At loss", "Break-even"])

    # Filter dataframe
    filtered_df = df[df["Ticker"].isin(tickers)]
    if result_filter != "All":
        filtered_df = filtered_df[filtered_df["Results"] == result_filter]

    # --- Trade Table ---
    st.subheader("🧾 Trade Overview")
    st.dataframe(filtered_df.style.applymap(
        lambda val: "background-color: #c6f6d5" if val == "Profitable" else (
            "background-color: #fed7d7" if val == "At loss" else ""),
        subset=["Results"]
    ))

    # --- Download Button ---
    st.markdown("### 💾 Export Filtered Results")
    csv_export = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv_export,
        file_name=f"filtered_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    # --- Key Metrics ---
    st.subheader("📊 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Tickers Displayed", len(filtered_df))

    last_run = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    col2.metric("Last Run Time", last_run)

    if "Volatility between entry and exit" in filtered_df.columns:
        try:
            filtered_df["Volatility %"] = filtered_df["Volatility between entry and exit"].str.replace("%", "").astype(float)
            max_row = filtered_df.loc[filtered_df["Volatility %"].idxmax()]
            col3.metric("Max Volatility Ticker", f"{max_row['Ticker']}", f"{max_row['Volatility %']:.2f}%")
        except:
            col3.metric("Max Volatility Ticker", "Error", "⚠️")

    # --- Selected Ticker Details ---
    if len(tickers) == 1:
        st.markdown("---")
        st.subheader(f"🔎 Details for `{tickers[0]}`")
        info = filtered_df.iloc[0]
        st.markdown(f"""
        - **Average Price:** `{info['Average Price']}`
        - **Entry Price:** `{info['Entry']}`
        - **Exit Price:** `{info['Exit']}`
        - **Current Price:** `{info['Current Price']}`
        """)

        # --- Price Chart ---
        st.subheader("📊 Price Comparison")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[info['Average Price'], info['Entry'], info['Exit'], info['Current Price']],
            y=["Average", "Entry", "Exit", "Current"],
            orientation='h',
            marker_color=["#2E86AB", "#EF553B", "#00CC96", "#9B59B6"]
        ))
        fig.update_layout(
            height=350,
            margin=dict(l=100, r=40, t=40, b=40),
            plot_bgcolor="#f9f9f9",
            paper_bgcolor="#f9f9f9"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Prediction Check Results ---
    checked_df = load_checked_data()
    if checked_df is not None:
        st.markdown("---")
        st.subheader("📋 Prediction Outcome (Last 24h)")
        checked_filtered = checked_df[checked_df["Ticker"].isin(filtered_df["Ticker"])]
        st.dataframe(checked_filtered[["Ticker", "Results", "Trade Time"]])
    else:
        st.info("ℹ️ The results of the last 24h prediction check will appear here once available.")