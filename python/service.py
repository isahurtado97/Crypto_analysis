import streamlit as st
import pandas as pd
import os
import time
import threading
from datetime import datetime
import plotly.graph_objects as go
import pytz  
import subprocess

# --- BACKGROUND SCHEDULER ---
def background_scheduler():
    time.sleep(60)  # Wait to ensure dependencies are loaded in Streamlit Cloud
    while True:
        print("\ud83d\udd01 Running 15-minute analysis...")
        try:
            subprocess.run(["python", "python/technical_analysis.py"], check=True)
            subprocess.run(["python", "python/check_entry.py"], check=True)
            print("\u2705 15-minute analysis completed.")
        except subprocess.CalledProcessError as e:
            print(f"\u274c Error running analysis scripts: {e}")

        now = int(time.time())
        if now % (4 * 60 * 60) < 900:
            print("\ud83d\udd01 Running 4-hour prediction check...")
            try:
                subprocess.run(["python", "python/check_prediction.py"], check=True)
                print("\u2705 4-hour prediction check completed.")
            except subprocess.CalledProcessError as e:
                print(f"\u274c Error running prediction script: {e}")

        time.sleep(900)  # Sleep for 15 minutes

# --- Run scheduler only once ---
if "scheduler_started" not in st.session_state:
    threading.Thread(target=background_scheduler, daemon=True).start()
    st.session_state.scheduler_started = True

# --- PAGE LAYOUT ---
st.set_page_config(page_title="Crypto Entry Dashboard", layout="wide")
st.markdown("<h1 style='text-align: center; color: #00BFA6;'>\ud83d\udcc8 Crypto Entry-Exit Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>AI analysis of crypto trade signals</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #999999; font-size: 0.9em;'>\ud83d\udea8 Investing in cryptocurrencies carries risk. This dashboard is for informational purposes only and does not constitute financial advice.</p>", unsafe_allow_html=True)
st.markdown("---")

# --- Manual EXECUTION buttons ---
col_a, col_b = st.columns(2)

if col_a.button("\ud83d\ude80 Run Technical Analysis + Entry Check Now"):
    with st.spinner("Running analysis..."):
        try:
            subprocess.run(["python", "python/technical_analysis.py"], check=True)
            subprocess.run(["python", "python/check_entry.py"], check=True)
            st.success("\u2705 Analysis completed successfully.")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"\u274c Error: {e}")

if col_b.button("\ud83d\udcca Run 24h Prediction Check Now"):
    with st.spinner("Running prediction check..."):
        try:
            subprocess.run(["python", "python/check_prediction.py"], check=True)
            st.success("\u2705 Prediction check completed.")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"\u274c Error: {e}")

st.markdown("---")

# --- DATA LOADERS ---
@st.cache_data(ttl=900)
def load_main_data():
    return pd.read_csv("csv/tickers_ready_full.csv")

@st.cache_data(ttl=900)
def load_checked_data():
    path = "csv/tickers_ready_24h_checked.csv"
    return pd.read_csv(path) if os.path.exists(path) else None

# --- MAIN LOGIC ---
file_path = "csv/tickers_ready_full.csv"

if not os.path.exists(file_path):
    st.info("\u23f3 Data is being prepared... Please wait for the first analysis or use the button above.")
    st.stop()
else:
    df = load_main_data()

    # --- Sidebar Filters ---
    st.sidebar.header("\u2699\ufe0f Filters")
    tickers = st.sidebar.multiselect("Select tickers:", options=sorted(df["Ticker"].unique()), default=sorted(df["Ticker"].unique()))
    result_filter = st.sidebar.selectbox("Filter by result:", ["All", "Profitable", "At loss", "Break-even"])

    filtered_df = df[df["Ticker"].isin(tickers)]
    if result_filter != "All":
        filtered_df = filtered_df[filtered_df["Results"] == result_filter]

    # --- Trade Table ---
    st.subheader("\ud83d\udcdf Trade Overview")
    st.dataframe(filtered_df.style.applymap(
        lambda val: "background-color: #c6f6d5" if val == "Profitable" else (
            "background-color: #fed7d7" if val == "At loss" else ""),
        subset=["Results"]
    ))

    # --- Export Button ---
    st.markdown("### \ud83d\udcc0 Export CSV")
    csv_export = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv_export,
        file_name=f"filtered_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    # --- Key Metrics ---
    st.subheader("\ud83d\udcca Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Tickers", len(filtered_df))

    # Metric 2: Last Update in CEST
    utc_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    cest = pytz.timezone("Europe/Madrid")
    last_run_cest = utc_time.replace(tzinfo=pytz.utc).astimezone(cest).strftime('%Y-%m-%d %H:%M:%S')
    col2.metric("Last Update", last_run_cest)

    if "Volatility between entry and exit" in filtered_df.columns:
        try:
            filtered_df["Volatility %"] = filtered_df["Volatility between entry and exit"].str.replace("%", "").astype(float)
            max_row = filtered_df.loc[filtered_df["Volatility %"].idxmax()]
            col3.metric("Max Volatility", f"{max_row['Ticker']}", f"{max_row['Volatility %']:.2f}%")
        except:
            col3.metric("Max Volatility", "Error", "\u26a0\ufe0f")

    # --- Ticker Details ---
    if len(tickers) == 1:
        st.markdown("---")
        st.subheader(f"\ud83d\udd0e Details for `{tickers[0]}`")
        info = filtered_df.iloc[0]
        st.markdown(f"""
        - **Average Price:** `{info['Average Price']}`
        - **Entry Price:** `{info['Entry']}`
        - **Exit Price:** `{info['Exit']}`
        - **Current Price:** `{info['Current Price']}`
        """)

        # Chart
        st.subheader("\ud83d\udcc8 Price Comparison")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[info['Average Price'], info['Entry'], info['Exit'], info['Current Price']],
            y=["Average", "Entry", "Exit", "Current"],
            orientation='h',
            marker_color=["#2E86AB", "#EF553B", "#00CC96", "#9B59B6"]
        ))
        fig.update_layout(height=350, margin=dict(l=100, r=40, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

    # --- Prediction Check Results ---
    checked_df = load_checked_data()
    if checked_df is not None:
        st.markdown("---")
        st.subheader("\ud83d\udccb Prediction Check (Last 24h)")
        checked_filtered = checked_df[checked_df["Ticker"].isin(filtered_df["Ticker"])]
        st.dataframe(checked_filtered[["Ticker", "Results", "Trade Time"]])
    else:
        st.info("\u2139\ufe0f Prediction check results will appear here after the first 4-hour cycle.")
