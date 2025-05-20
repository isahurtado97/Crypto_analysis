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

tab1, tab2, tab3, tab4 = st.tabs(["📊 Crypto Dashboard", "💰 Calculadora Take Profit", "📅 Eventos Cripto", "📋 Verificar Reglas de Entrada"])

# --- DATA LOADERS ---
@st.cache_data(ttl=900)
def load_main_data():
    return pd.read_csv("csv/tickers_ready_full.csv")

@st.cache_data(ttl=900)
def load_checked_data():
    path = "csv/tickers_ready_24h_checked.csv"
    return pd.read_csv(path) if os.path.exists(path) else None

file_path = "csv/tickers_ready_full.csv"

with tab1:
    if not os.path.exists(file_path):
        st.info("⏳ Data is being prepared... Please wait for the first analysis or use the button above.")
        st.stop()
    else:
        df = load_main_data()

        # --- Sidebar Filters ---
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

        # --- Trade Overview Table ---
        st.subheader("🧾 Trade Overview")
        cols_to_show = [
            "Date", "Ticker", "Average Price", "Entry", "Exit", "Current Price",
            "Volatility between entry and exit", "RSI_15m", "MACD Trend 15m", "RSI_4h", "MACD Trend 4h", "Results"
        ]

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

        # --- Strategy Tables ---
        st.markdown("---")
        st.subheader("📈 Long-Term Trading Opportunities")
        long_term = filtered_df[
            (filtered_df["RSI_4h"] < 40) &
            (filtered_df["MACD Trend 4h"] == "Alcista")
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
            (filtered_df["RSI_15m"] < 40) &
            (filtered_df["MACD Trend 15m"] == "Alcista")
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

with tab2:
    st.markdown("### 💰 Calculadora de Salida con % de Ganancia")
    entry_price = st.number_input("Precio de entrada (€ por unidad)", min_value=0.0, format="%f")
    invested_amount = st.number_input("Inversión en euros", min_value=0.0, format="%f")
    profit_percent = st.slider("% de ganancia esperada", min_value=0.5, max_value=10.0, value=2.0, step=0.1)

    if entry_price > 0 and invested_amount > 0:
        quantity = invested_amount / entry_price
        target_exit_price = entry_price * (1 + profit_percent / 100)
        expected_return = quantity * target_exit_price

        st.success(f"🎯 Precio objetivo con +{profit_percent:.1f}%: {target_exit_price:.5f} €")
        st.info(f"💰 Obtendrás: {quantity:.2f} unidades por {invested_amount:.2f} €")
        st.success(f"💵 Valor de salida estimado: {expected_return:.2f} €")

with tab3:
    st.markdown("### 📅 Eventos Importantes que Afectan a las Criptomonedas")
    st.markdown("Consulta CoinMarketCal para conocer próximos eventos relevantes que pueden impactar el mercado cripto.")
    st.markdown("[🔗 Ver en CoinMarketCal](https://coinmarketcal.com/en/)")

with tab4:
    st.markdown("### 📋 Verificar Reglas de Entrada para Trading")

    strategy = st.selectbox("Selecciona estrategia:", ["Long-Term", "Short-Term"])

    entry_price = st.number_input("Precio de entrada")
    low_price = st.number_input("Precio más bajo frecuente")
    macd = st.selectbox("MACD", ["Alcista", "Bajista"])

    if strategy == "Long-Term":
        rsi_4h = st.number_input("RSI 4h", min_value=0, max_value=100)
        if st.button("Verificar Long-Term"):
            price_diff_pct = ((entry_price - low_price) / low_price) * 100 if low_price > 0 else 0
            if rsi_4h < 30 and macd == "Alcista" and price_diff_pct > 1:
                st.success("✅ Cumple condiciones para estrategia Long-Term")
            else:
                st.error("❌ No cumple condiciones para estrategia Long-Term")

    if strategy == "Short-Term":
        rsi_15m = st.number_input("RSI 15m", min_value=0, max_value=100)
        if st.button("Verificar Short-Term"):
            price_diff_pct = ((entry_price - low_price) / low_price) * 100 if low_price > 0 else 0
            if rsi_15m < 30 and macd == "Alcista" and price_diff_pct > 1:
                st.success("✅ Cumple condiciones para estrategia Short-Term")
            else:
                st.error("❌ No cumple condiciones para estrategia Short-Term")
