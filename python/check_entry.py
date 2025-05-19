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
        print("🔁 Running 15-minute analysis...")
        try:
            subprocess.run([sys.executable, "python/technical_analysis.py"], check=True)
            subprocess.run([sys.executable, "python/check_entry.py"], check=True)
            print("✅ 15-minute analysis completed.")
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

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Crypto Dashboard",
    "💰 Calculadora de Take Profit",
    "🗓️ Calendario Macroeconómico",
    "📣 Eventos Cripto (CoinMarketCal)"
])

# TAB 1: Crypto Dashboard
with tab1:
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

        st.sidebar.header("⚙️ Filters")
        tickers = st.sidebar.multiselect("Select tickers:", options=sorted(df["Ticker"].unique()), default=sorted(df["Ticker"].unique()))
        result_filter = st.sidebar.selectbox("Filter by result:", ["All", "Profitable", "At loss", "Break-even"])
        rsi_min = st.sidebar.slider("RSI Minimum (any)", min_value=0, max_value=100, value=0)
        rsi_max = st.sidebar.slider("RSI Maximum (any)", min_value=0, max_value=100, value=100)

        filtered_df = df[df["Ticker"].isin(tickers)]
        if result_filter != "All":
            filtered_df = filtered_df[filtered_df["Results"] == result_filter]

        filtered_df = filtered_df[(filtered_df["RSI_15m"] >= rsi_min) & (filtered_df["RSI_15m"] <= rsi_max) |
                                   (filtered_df["RSI_4h"] >= rsi_min) & (filtered_df["RSI_4h"] <= rsi_max)]

        st.subheader(f"🧾 Trade Overview – {len(filtered_df)} resultados")
        cols_to_show = [
            "Date", "Ticker", "Average Price", "Entry", "Exit", "Current Price",
            "Volatility between entry and exit", "RSI_15m", "MACD Trend 15m", "RSI_4h", "MACD Trend 4h", "Results"
        ]

        def highlight_result(val):
            if val == "Profitable":
                return "background-color: #c6f6d5"
            elif val == "At loss":
                return "background-color: #fed7d7"
            return ""

        def highlight_rsi(val):
            try:
                v = float(val)
                if v > 70:
                    return "background-color: #fdd"
                elif v < 30:
                    return "background-color: #dfd"
            except:
                return ""
            return ""

        styled_df = (
            filtered_df[cols_to_show]
            .style
            .applymap(highlight_result, subset=["Results"])
            .applymap(highlight_rsi, subset=["RSI_15m", "RSI_4h"])
        )

        st.dataframe(styled_df)

        # Key metrics after overview
        st.markdown("---")
        st.subheader("📊 Métricas de la sesión")
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Tickers cargados", len(df))

        cest = pytz.timezone("Europe/Madrid")
        last_run = datetime.fromtimestamp(os.path.getmtime(file_path)).astimezone(cest)
        col2.metric("🕒 Última ejecución", last_run.strftime('%Y-%m-%d %H:%M:%S'))

        try:
            df["Volatility %"] = df["Volatility between entry and exit"].astype(str).str.replace("%", "").astype(float)
            max_vol_row = df.loc[df["Volatility %"].idxmax()]
            col3.metric("🔥 Máx. Volatilidad", f"{max_vol_row['Ticker']} ({max_vol_row['Volatility %']:.2f}%)")
        except:
            col3.metric("🔥 Máx. Volatilidad", "No disponible")

        # Long-Term Opportunities
        st.markdown("---")
        st.subheader("📈 Long-Term Trading Opportunities")
        long_term = filtered_df[
            (filtered_df["RSI_4h"] < 30) &
            (filtered_df["MACD Trend 4h"] == "Alcista")
        ]
        st.dataframe(long_term[cols_to_show])

        # Short-Term Opportunities
        st.markdown("---")
        st.subheader("⚡ Short-Term Trading Opportunities")
        short_term = filtered_df[
            (filtered_df["RSI_15m"] < 30) &
            (filtered_df["MACD Trend 15m"] == "Alcista")
        ]
        st.dataframe(short_term[cols_to_show])

        # Prediction Check Results
        checked_df = load_checked_data()
        if checked_df is not None:
            st.markdown("---")
            st.subheader("📋 Prediction Check (Last 24h)")
            checked_filtered = checked_df[checked_df["Ticker"].isin(filtered_df["Ticker"])]
            st.dataframe(checked_filtered[["Ticker", "Results", "Trade Time"]])
        else:
            st.info("ℹ️ Prediction check results will appear here after the first 4-hour cycle.")