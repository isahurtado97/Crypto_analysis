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
        print("\U0001F501 Running 15-minute analysis...")
        try:
            subprocess.run([sys.executable, "python/technical_analysis.py"], check=True)
            subprocess.run([sys.executable, "python/check_entry.py"], check=True)
            print("\u2705 15-minute analysis completed.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running analysis scripts: {e}")

        now = int(time.time())
        if now % (30 * 60) < 60:
            print("\U0001F501 Running 4-hour prediction check...")
            try:
                subprocess.run([sys.executable, "python/check_prediction.py"], check=True)
                print("\u2705 4-hour prediction check completed.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error running prediction script: {e}")

        time.sleep(1800)

# --- Run scheduler only once ---
if "scheduler_started" not in st.session_state:
    threading.Thread(target=background_scheduler, daemon=True).start()
    st.session_state.scheduler_started = True

# --- PAGE LAYOUT ---
st.set_page_config(page_title="Crypto Entry Dashboard", layout="wide")
st.markdown("## \U0001F4C8 Crypto Entry-Exit Dashboard")
st.markdown("*AI analysis of crypto trade signals*")
st.markdown(
    "<p style='text-align: center; color: #999999; font-size: 0.9em;'>⚠️ Investing in cryptocurrencies carries risk. This dashboard is for informational purposes only and does not constitute financial advice.</p>",
    unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "\U0001F4C8 Crypto Dashboard",
    "\U0001F4B0 Calculadora de Take Profit",
    "\U0001F5D3️ Calendario Macroeconómico",
    "\U0001F4E3 Eventos Cripto (CoinMarketCal)"
])

# TAB 1: Crypto Dashboard
with tab1:
    col_a, col_b = st.columns(2)

    if col_a.button("\U0001F680 Run Technical Analysis + Entry Check Now"):
        with st.spinner("Running analysis..."):
            try:
                subprocess.run([sys.executable, "python/technical_analysis.py"], check=True)
                subprocess.run([sys.executable, "python/check_entry.py"], check=True)
                st.success("\u2705 Analysis completed successfully.")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if col_b.button("\U0001F4CA Run 24h Prediction Check Now"):
        with st.spinner("Running prediction check..."):
            try:
                subprocess.run([sys.executable, "python/check_prediction.py"], check=True)
                st.success("\u2705 Prediction check completed.")
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

        # Key metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("\U0001F4CA Tickers cargados", len(df))

        cest = pytz.timezone("Europe/Madrid")
        last_run = datetime.fromtimestamp(os.path.getmtime(file_path)).astimezone(cest)
        col2.metric("\U0001F552 Última ejecución", last_run.strftime('%Y-%m-%d %H:%M:%S'))

        try:
            df["Volatility %"] = df["Volatility between entry and exit"].astype(str).str.replace("%", "").astype(float)
            max_vol_row = df.loc[df["Volatility %"].idxmax()]
            col3.metric("\U0001F525 Máx. Volatilidad", f"{max_vol_row['Ticker']} ({max_vol_row['Volatility %']:.2f}%)")
        except:
            col3.metric("\U0001F525 Máx. Volatilidad", "No disponible")

        st.sidebar.header("⚙️ Filters")
        tickers = st.sidebar.multiselect("Select tickers:", options=sorted(df["Ticker"].unique()), default=sorted(df["Ticker"].unique()))
        result_filter = st.sidebar.selectbox("Filter by result:", ["All", "Profitable", "At loss", "Break-even"])
        rsi_min = st.sidebar.slider("RSI Minimum (any)", min_value=0, max_value=100, value=0)
        rsi_max = st.sidebar.slider("RSI Maximum (any)", min_value=0, max_value=100, value=100)

        filtered_df = df[df["Ticker"].isin(tickers)]
        if result_filter != "All":
            filtered_df = filtered_df[filtered_df["Results"] == result_filter]

        if "RSI_15m" in filtered_df.columns and "RSI_4h" in filtered_df.columns:
            filtered_df = filtered_df[
                ((filtered_df["RSI_15m"] >= rsi_min) & (filtered_df["RSI_15m"] <= rsi_max)) |
                ((filtered_df["RSI_4h"] >= rsi_min) & (filtered_df["RSI_4h"] <= rsi_max))
            ]
        else:
            st.warning("❗️ No se encontraron columnas RSI_15m o RSI_4h en los datos.")

        st.subheader(f"\U0001F9FE Trade Overview – {len(filtered_df)} resultados")
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
            .map(highlight_result, subset=["Results"])
            .map(highlight_rsi, subset=["RSI_15m", "RSI_4h"])
        )

        st.dataframe(styled_df)
        st.download_button(
            label="\U0001F4BE Exportar Trade Overview",
            data=filtered_df[cols_to_show].to_csv(index=False).encode("utf-8"),
            file_name="trade_overview.csv",
            mime="text/csv"
        )

        st.markdown("---")
        st.subheader("\U0001F4C8 Long-Term Trading Opportunities")
        long_term = filtered_df[
            (filtered_df["RSI_4h"] < 30) &
            (filtered_df["MACD Trend 4h"] == "Alcista")
        ]
        if long_term.empty:
            st.info("No hay oportunidades long-term actualmente.")
        else:
            st.dataframe(long_term[cols_to_show])

        st.markdown("---")
        st.subheader("⚡ Short-Term Trading Opportunities")
        short_term = filtered_df[
            (filtered_df["RSI_15m"] < 30) &
            (filtered_df["MACD Trend 15m"] == "Alcista")
        ]
        if short_term.empty:
            st.info("No hay oportunidades short-term actualmente.")
        else:
            st.dataframe(short_term[cols_to_show])

        st.download_button(
            label="\U0001F4E4 Exportar oportunidades Long-Term",
            data=long_term.to_csv(index=False).encode("utf-8"),
            file_name="long_term_opportunities.csv",
            mime="text/csv"
        )
        st.download_button(
            label="\U0001F4E4 Exportar oportunidades Short-Term",
            data=short_term.to_csv(index=False).encode("utf-8"),
            file_name="short_term_opportunities.csv",
            mime="text/csv"
        )

# TAB 2: Calculadora Take Profit
with tab2:
    st.markdown("### \U0001F4B0 Calculadora de Salida con % de Ganancia")
    entry_price = st.number_input("Precio de entrada (€ por unidad)", min_value=0.0, format="%f")
    invested_amount = st.number_input("Inversión en euros", min_value=0.0, format="%f")
    profit_percent = st.slider("% de ganancia esperada", min_value=0.5, max_value=10.0, value=2.0, step=0.1)

    if entry_price > 0 and invested_amount > 0:
        quantity = invested_amount / entry_price
        target_exit_price = entry_price * (1 + profit_percent / 100)
        expected_return = quantity * target_exit_price

        st.success(f"\U0001F3AF Precio objetivo con +{profit_percent:.1f}%: {target_exit_price:.5f} €")
        st.info(f"\U0001F4B0 Obtendrás: {quantity:.2f} unidades por {invested_amount:.2f} €")
        st.success(f"\U0001F4B5 Valor de salida estimado: {expected_return:.2f} €")

# TAB 3: Calendario Macroeconómico
with tab3:
    st.markdown("### \U0001F5D3️ Calendario Macroeconómico")
    st.markdown("[\U0001F517 Abrir Calendario en Investing.com](https://es.investing.com/economic-calendar/?timeZone=56)")

# TAB 4: Eventos Cripto
with tab4:
    st.markdown("### \U0001F4E3 Eventos Importantes de Criptomonedas")
    st.markdown("[\U0001F517 Abrir CoinMarketCal](https://coinmarketcal.com/en/)")