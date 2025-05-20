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
        for script in ["technical_analysis.py", "check_entry.py"]:
            try:
                subprocess.run([sys.executable, f"python/{script}"], check=True)
                print(f"✅ {script} completed.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error running {script}: {e}")

        if int(time.time()) % (30 * 60) < 60:
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
    "<p style='text-align: center; color: #999999; font-size: 0.9em;'>"
    "🚨 Investing in cryptocurrencies carries risk. This dashboard is for informational purposes only and does not constitute financial advice."
    "</p>",
    unsafe_allow_html=True)
st.markdown("---")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Crypto Dashboard", 
    "💰 Calculadora Take Profit", 
    "📅 Eventos Cripto", 
    "📋 Verificar Reglas de Entrada"
])

# --- DATA LOADERS ---
@st.cache_data(ttl=900)
def load_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

main_data_path = "csv/tickers_ready_full.csv"
checked_data_path = "csv/tickers_ready_24h_checked.csv"

# --- STATUS & MANUAL CONTROLS ---
st.markdown("### 🕒 Estado del Análisis")
st.write(f"🗓️ Última ejecución (Amsterdam): `{datetime.now(pytz.timezone('Europe/Amsterdam')).strftime('%Y-%m-%d %H:%M:%S')}`")

df_status = load_csv(main_data_path)
if not df_status.empty:
    if "Volatility between entry and exit" in df_status:
        try:
            df_status["Volatility %"] = df_status["Volatility between entry and exit"].astype(str).str.replace("%", "").astype(float)
            most_volatile = df_status.loc[df_status["Volatility %"].idxmax()]
            st.write(f"📈 Ticker más volátil: `{most_volatile['Ticker']}` con `{most_volatile['Volatility between entry and exit']}`")
        except:
            st.warning("⚠️ Error procesando la volatilidad.")
    st.write(f"🔢 Total de tickers en tabla: `{len(df_status)}`")
else:
    st.info("⏳ Esperando resultados iniciales para mostrar estadísticas.")

col1, col2 = st.columns(2)
with col1:
    if st.button("🔁 Ejecutar análisis manual"):
        for script in ["technical_analysis.py", "check_entry.py"]:
            try:
                subprocess.run([sys.executable, f"python/{script}"], check=True)
                st.success(f"✅ {script} ejecutado correctamente.")
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Error en {script}: {e}")

with col2:
    if st.button("📊 Ejecutar predicción manual"):
        try:
            subprocess.run([sys.executable, "python/check_prediction.py"], check=True)
            st.success("✅ Predicciones ejecutadas correctamente.")
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Error al ejecutar predicción: {e}")

# --- TAB 1: DASHBOARD ---
with tab1:
    df = load_csv(main_data_path)
    if df.empty:
        st.info("⏳ Data is being prepared... Please wait.")
        st.stop()

    # Sidebar filters
    st.sidebar.header("⚙️ Filters")
    tickers = st.sidebar.multiselect("Select tickers:", options=sorted(df["Ticker"].unique()), default=sorted(df["Ticker"].unique()))
    result_filter = st.sidebar.selectbox("Filter by result:", ["All", "Profitable", "At loss", "Break-even"])
    rsi_min, rsi_max = st.sidebar.slider("RSI Range (any)", 0, 100, (0, 100))

    filtered_df = df[df["Ticker"].isin(tickers)]
    if result_filter != "All":
        filtered_df = filtered_df[filtered_df["Results"] == result_filter]

    rsi_cond = (
        ((filtered_df["RSI_15m"] >= rsi_min) & (filtered_df["RSI_15m"] <= rsi_max)) |
        ((filtered_df["RSI_4h"] >= rsi_min) & (filtered_df["RSI_4h"] <= rsi_max))
    )
    filtered_df = filtered_df[rsi_cond]

    if "Volatility between entry and exit" in filtered_df:
        try:
            filtered_df["Volatility %"] = filtered_df["Volatility between entry and exit"].astype(str).str.replace("%", "").astype(float)
        except:
            filtered_df["Volatility %"] = np.nan

    def highlight_result(val):
        return "background-color: #c6f6d5" if val == "Profitable" else "background-color: #fed7d7" if val == "At loss" else ""

    def highlight_rsi(val):
        try:
            v = float(val)
            if v > 70: return "background-color: #fdd"
            elif v < 30: return "background-color: #dfd"
        except: return ""
        return ""

    cols_to_show = [
        "Date", "Ticker", "Average Price", "Entry", "Exit", "Current Price",
        "Volatility between entry and exit", "RSI_15m", "MACD Trend 15m", "RSI_4h", "MACD Trend 4h", "Results"
    ]

    st.subheader("🧾 Trade Overview")
    styled_df = (
        filtered_df[cols_to_show]
        .style
        .applymap(highlight_result, subset=["Results"])
        .applymap(highlight_rsi, subset=["RSI_15m", "RSI_4h"])
        .background_gradient(cmap="YlGn", subset=["Volatility between entry and exit"],
                             gmap=filtered_df["Volatility %"] if "Volatility %" in filtered_df else None)
    )
    st.dataframe(styled_df)

    st.markdown("### 💾 Export CSV")
    st.download_button("Download CSV", filtered_df.to_csv(index=False).encode("utf-8"),
                       file_name=f"filtered_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("📈 Long-Term Trading Opportunities")
    long_term = filtered_df[(filtered_df["RSI_4h"] < 40) & (filtered_df["MACD Trend 4h"] == "Alcista")]
    st.dataframe(long_term[cols_to_show])
    st.download_button("Download Long-Term CSV", long_term.to_csv(index=False).encode("utf-8"),
                       file_name=f"long_term_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")

    st.markdown("---")
    st.subheader("⚡ Short-Term Trading Opportunities")
    short_term = filtered_df[(filtered_df["RSI_15m"] < 40) & (filtered_df["MACD Trend 15m"] == "Alcista")]
    st.dataframe(short_term[cols_to_show])
    st.download_button("Download Short-Term CSV", short_term.to_csv(index=False).encode("utf-8"),
                       file_name=f"short_term_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")

    checked_df = load_csv(checked_data_path)
    if not checked_df.empty:
        st.markdown("---")
        st.subheader("📋 Prediction Check (Last 24h)")
        st.dataframe(checked_df[checked_df["Ticker"].isin(filtered_df["Ticker"])]
                     [["Ticker", "Results", "Trade Time"]])
    else:
        st.info("ℹ️ Prediction check results will appear here after the first 4-hour cycle.")

# ¿Te gustaría que también optimice los tabs 2, 3 y 4 en el mismo estilo?