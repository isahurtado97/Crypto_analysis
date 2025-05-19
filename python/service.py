import streamlit as st
import pandas as pd
import os
import time
import threading
from datetime import datetime
import plotly.graph_objects as go
import pytz
import subprocess
import sys
import numpy as np

# --- BACKGROUND SCHEDULER ---
def background_scheduler():
    time.sleep(60)
    while True:
        print("🔁 Running 30-minute analysis...")
        try:
            subprocess.run([sys.executable, "python/technical_analysis.py"], check=True)
            subprocess.run([sys.executable, "python/check_entry.py"], check=True)
            print("✅ 30-minute analysis completed.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running analysis scripts: {e}")

        now = int(time.time())
        if now % (30 * 60) < 60:
            print("🔁 Running 4-hour prediction check...")
            try:
                subprocess.run([sys.executable, "python/check_prediction.py"], check=True)
                print("✅ 4-hour prediction check completed.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error running prediction script: {e}")

        time.sleep(1800)

# --- Run scheduler only once ---
if "scheduler_started" not in st.session_state:
    threading.Thread(target=background_scheduler, daemon=True).start()
    st.session_state.scheduler_started = True

# --- PAGE LAYOUT ---
st.set_page_config(page_title="Crypto Entry Dashboard", layout="wide")
st.markdown("## 📈 Crypto Entry-Exit Dashboard")
st.markdown("*AI analysis of crypto trade signals*")
st.markdown(
    "<p style='text-align: center; color: #999999; font-size: 0.9em;'>🚨 Investing in cryptocurrencies carries risk. This dashboard is for informational purposes only and does not constitute financial advice.</p>",
    unsafe_allow_html=True)
st.markdown("---")

# --- Manual EXECUTION buttons ---
col_a, col_b = st.columns(2)

if col_a.button("🚀 Run Technical Analysis + Entry Check Now"):
    with st.spinner("Running analysis..."):
        try:
            subprocess.run([sys.executable, "python/technical_analysis.py"], check=True)
            subprocess.run([sys.executable, "python/check_entry.py"], check=True)
            st.success("✅ Analysis completed successfully.")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"❌ Error: {e}")

if col_b.button("📊 Run 24h Prediction Check Now"):
    with st.spinner("Running prediction check..."):
        try:
            subprocess.run([sys.executable, "python/check_prediction.py"], check=True)
            st.success("✅ Prediction check completed.")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"❌ Error: {e}")

st.markdown("---")

# --- DATA LOADERS ---
@st.cache_data(ttl=900)
def load_main_data():
    return pd.read_csv("csv/tickers_ready_full.csv")

@st.cache_data(ttl=900)
def load_checked_data():
    path = "csv/tickers_ready_24h_checked.csv"
    return pd.read_csv(path) if os.path.exists(path) else None

file_path = "csv/tickers_ready_full.csv"

if not os.path.exists(file_path):
    st.info("⏳ Data is being prepared... Please wait for the first analysis or use the button above.")
    st.stop()
else:
    df = load_main_data()

    # --- Sidebar Filters ---
    st.sidebar.header("⚙️ Filters")
    tickers = st.sidebar.multiselect("Select tickers:", options=sorted(df["Ticker"].unique()), default=sorted(df["Ticker"].unique()))
    result_filter = st.sidebar.selectbox("Filter by result:", ["All", "Profitable", "At loss", "Break-even"])

    filtered_df = df[df["Ticker"].isin(tickers)]
    if result_filter != "All":
        filtered_df = filtered_df[filtered_df["Results"] == result_filter]

    # --- Trade Overview Table ---
    st.subheader("🧾 Trade Overview")
    cols_to_show = ["Date", "Ticker", "Average Price", "Entry", "Exit", "Current Price", "Volatility between entry and exit", "RSI", "MACD Trend", "Results"]

    if "Volatility between entry and exit" in filtered_df.columns:
        try:
            filtered_df["Volatility %"] = (
                filtered_df["Volatility between entry and exit"]
                .astype(str)
                .str.replace("%", "")
                .astype(float)
            )
        except:
            filtered_df["Volatility %"] = None

    def highlight_result(val):
        if val == "Profitable":
            return "background-color: #c6f6d5"
        elif val == "At loss":
            return "background-color: #fed7d7"
        return ""

    styled_df = (
        filtered_df[cols_to_show]
        .style
        .applymap(highlight_result, subset=["Results"])
        .background_gradient(
            cmap="YlGn", subset=["Volatility between entry and exit"],
            gmap=filtered_df["Volatility %"] if "Volatility %" in filtered_df else None
        )
    )

    st.dataframe(styled_df)

    # --- Export CSV Button ---
    st.markdown("### 💾 Export CSV")
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

    utc_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    cest = pytz.timezone("Europe/Madrid")
    last_run_cest = utc_time.replace(tzinfo=pytz.utc).astimezone(cest).strftime('%Y-%m-%d %H:%M:%S')
    col2.metric("Last Update", last_run_cest)

    if "Volatility %" in filtered_df.columns:
        try:
            max_row = filtered_df.loc[filtered_df["Volatility %"].idxmax()]
            col3.metric("Max Volatility", f"{max_row['Ticker']}", f"{max_row['Volatility %']:.2f}%")
        except:
            col3.metric("Max Volatility", "Error", "⚠️")

    # --- Ticker Specific Details ---
    if len(tickers) == 1:
        st.markdown("---")
        st.subheader(f"🔎 Details for `{tickers[0]}`")
        info = filtered_df.iloc[0]
        st.markdown(f"""
        - **Average Price:** `{info['Average Price']}`
        - **Entry Price:** `{info['Entry']}`
        - **Exit Price:** `{info['Exit']}`
        - **Current Price:** `{info['Current Price']}`
        - **RSI:** `{info.get('RSI', 'N/A')}`
        - **MACD Trend:** `{info.get('MACD Trend', 'N/A')}`
        """)

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

    # --- Strategy Tables ---
    st.markdown("---")
    st.subheader("📈 Long-Term Trading Opportunities")
    long_term = filtered_df[
        (filtered_df["RSI"] < 40) &
        (filtered_df["MACD Trend"] == "Alcista")
    ]
    st.dataframe(long_term[cols_to_show])

    st.markdown("### 💾 Export Long-Term Opportunities")
    long_csv = long_term.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Long-Term CSV",
        data=long_csv,
        file_name=f"long_term_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.subheader("⚡ Short-Term Trading Opportunities")
    short_term = filtered_df[
        (filtered_df["RSI"] < 40) &
        (filtered_df["MACD Trend"] == "Alcista")
    ]
    st.dataframe(short_term[cols_to_show])

    st.markdown("### 💾 Export Short-Term Opportunities")
    short_csv = short_term.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Short-Term CSV",
        data=short_csv,
        file_name=f"short_term_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    # --- Prediction Check Results ---
    checked_df = load_checked_data()
    if checked_df is not None:
        st.markdown("---")
        st.subheader("📋 Prediction Check (Last 24h)")
        checked_filtered = checked_df[checked_df["Ticker"].isin(filtered_df["Ticker"])]
        st.dataframe(checked_filtered[["Ticker", "Results", "Trade Time"]])
    else:
        st.info("ℹ️ Prediction check results will appear here after the first 4-hour cycle.")
