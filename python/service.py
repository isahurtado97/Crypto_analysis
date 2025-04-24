import streamlit as st
import pandas as pd
import os
import time
import threading
from datetime import datetime
import plotly.graph_objects as go

# --- BACKGROUND SCHEDULER ---
def background_scheduler():
    while True:
        print("🔁 Running 15-minute analysis...")
        try:
            exec(open("python/technical_analysis.py").read())
            exec(open("python/check_entry.py").read())
        except Exception as e:
            print("❌ Error during analysis:", e)

        # Run prediction every 4 hours (with a time window)
        now = int(time.time())
        if now % (4 * 60 * 60) < 900:  # within a 15-min window
            print("🔁 Running 4-hour prediction check...")
            try:
                exec(open("python/check_prediction.py").read())
            except Exception as e:
                print("❌ Error during prediction check:", e)

        time.sleep(900)  # Wait 15 minutes

# --- Start scheduler only once per Streamlit session ---
if "scheduler_started" not in st.session_state:
    threading.Thread(target=background_scheduler, daemon=True).start()
    st.session_state.scheduler_started = True

# --- PAGE LAYOUT ---
st.set_page_config(page_title="Crypto Entry Dashboard", layout="wide")
st.markdown("<h1 style='text-align: center; color: #00BFA6;'>📈 Crypto Trade Entry Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Auto-analysis of frequent level signals + direction every 15 min</p>", unsafe_allow_html=True)
st.markdown("---")

# --- DATA LOADERS ---
@st.cache_data(ttl=900)
def load_main_data():
    return pd.read_csv("csv/tickers_ready_full.csv")

@st.cache_data(ttl=900)
def load_checked_data():
    path = "csv/tickers_ready_24h_checked.csv"
    return pd.read_csv(path) if os.path.exists(path) else None

# Manual reload
if st.sidebar.button("🔄 Force data refresh"):
    st.cache_data.clear()

# --- MAIN DATA ---
file_path = "csv/tickers_ready_full.csv"

if not os.path.exists(file_path):
    st.warning("⚠️ File `tickers_ready_full.csv` not found. Run the analysis first.")
else:
    df = load_main_data()

    # --- Sidebar Filters ---
    st.sidebar.header("⚙️ Filters")
    tickers = st.sidebar.multiselect("Select tickers:", options=sorted(df["Ticker"].unique()), default=sorted(df["Ticker"].unique()))
    result_filter = st.sidebar.selectbox("Filter by result:", ["All", "Profitable", "At loss", "Break-even"])

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

    # --- Export ---
    st.markdown("### 💾 Export Filtered CSV")
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
    col1.metric("Tickers", len(filtered_df))
    last_run = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    col2.metric("Last Update", last_run)

    if "Volatility between entry and exit" in filtered_df.columns:
        try:
            filtered_df["Volatility %"] = filtered_df["Volatility between entry and exit"].str.replace("%", "").astype(float)
            max_row = filtered_df.loc[filtered_df["Volatility %"].idxmax()]
            col3.metric("Max Volatility", f"{max_row['Ticker']}", f"{max_row['Volatility %']:.2f}%")
        except:
            col3.metric("Max Volatility", "Error", "⚠️")

    # --- Details of single ticker ---
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

        # Chart
        st.subheader("📊 Price Comparison")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[info['Average Price'], info['Entry'], info['Exit'], info['Current Price']],
            y=["Average", "Entry", "Exit", "Current"],
            orientation='h',
            marker_color=["#2E86AB", "#EF553B", "#00CC96", "#9B59B6"]
        ))
        fig.update_layout(height=350, margin=dict(l=100, r=40, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

    # --- Prediction Results ---
    checked_df = load_checked_data()
    if checked_df is not None:
        st.markdown("---")
        st.subheader("📋 Prediction Check (Last 24h)")
        checked_filtered = checked_df[checked_df["Ticker"].isin(filtered_df["Ticker"])]
        st.dataframe(checked_filtered[["Ticker", "Results", "Trade Time"]])
    else:
        st.info("ℹ️ Prediction check results will appear here after the first 4-hour cycle.")