
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

# Continúa con contenido de tabs como en tu código original (tab1, tab2, tab3, tab4)...
