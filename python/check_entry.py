import pandas as pd
import requests
import os
from datetime import datetime

BITVAVO_URL = "https://api.bitvavo.com/v2"
LOG_FILE = "error_log.txt"

def log_error(message):
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now().isoformat()} - {message}\n")

def is_valid_market(ticker):
    try:
        res = requests.get(f"{BITVAVO_URL}/markets")
        res.raise_for_status()
        markets = res.json()
        return ticker in [m['market'] for m in markets]
    except Exception as e:
        log_error(f"Error checking market {ticker}: {e}")
        return False

def get_current_price(ticker):
    if not is_valid_market(ticker):
        msg = f"{ticker} no es un mercado válido en Bitvavo."
        print(f"❌ {msg}")
        log_error(msg)
        return None

    url = f"{BITVAVO_URL}/ticker/price?market={ticker}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return float(res.json()['price'])
    except Exception as e:
        print(f"⚠️ Error con {ticker}: {e}")
        log_error(f"{ticker} – {e}")
        return None

def check_entry_conditions_with_profit():
    file_path = "csv2/directional_frequent_levels.csv"
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        print(f"🚫 El archivo {file_path} está vacío o no existe.")
        return

    try:
        df_trades = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Error al leer el archivo CSV: {e}")
        log_error(f"Error al leer {file_path}: {e}")
        return

    if df_trades.empty:
        print("🚫 El archivo no contiene datos utilizables.")
        return

    entries = []

    for _, row in df_trades.iterrows():
        ticker = row["Ticker"]
        entry_price = row["Entry"]
        quantity = row["Quantity"]
        exit_price = row.get("Exit", None)

        current_price = get_current_price(ticker)
        if current_price is None:
            continue

        if current_price <= entry_price * 1.005:
            row_with_data = row.copy()
            row_with_data["Current Price"] = round(current_price, 8)

            if pd.notna(exit_price):
                row_with_data["Profit Target"] = round((exit_price - entry_price) * quantity, 2)
            else:
                row_with_data["Profit Target"] = ""

            unrealized_pnl = round((current_price - entry_price) * quantity, 2)
            row_with_data["Unrealized PnL"] = unrealized_pnl

            if unrealized_pnl > 0:
                row_with_data["Results"] = "Profitable"
            elif unrealized_pnl < 0:
                row_with_data["Results"] = "At loss"
            else:
                row_with_data["Results"] = "Break-even"

            entries.append(row_with_data)

    if not entries:
        print("🚫 Ninguna crypto cumple condiciones de entrada ahora mismo.")
    else:
        df_ready = pd.DataFrame(entries)
        df_ready.to_csv("csv2/tickers_ready_full.csv", index=False)
        print("✅ Archivo generado: tickers_ready_full.csv")
        print(df_ready[["Ticker", "Entry", "Current Price", "Unrealized PnL", "Results"]])

if __name__ == "__main__":
    check_entry_conditions_with_profit()