# --- check_entry.py ---
import pandas as pd
import requests
from datetime import datetime
import ta
from technical_analysis import get_candles

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


def compute_indicators(df):
    df = df.copy()
    df["rsi"] = ta.momentum.RSIIndicator(close=df["close"]).rsi()
    macd = ta.trend.MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_trend"] = df["macd"] > df["macd_signal"]
    return df


def check_entry_conditions_with_profit():
    df_trades = pd.read_csv("csv/directional_frequent_levels.csv")
    entries = []

    for _, row in df_trades.iterrows():
        ticker = row["Ticker"]
        entry_price = row["Entry"]
        quantity = row["Quantity"]
        exit_price = row.get("Exit", None)
        current_price = get_current_price(ticker)
        if current_price is None:
            continue

        try:
            df_15m = get_candles(ticker, interval="5m", limit=60)
            df_4h = get_candles(ticker, interval="4h", limit=60)
            df_15m = compute_indicators(df_15m)
            df_4h = compute_indicators(df_4h)
            rsi_15m = df_15m["rsi"].dropna().iloc[-1]
            macd_trend_15m = df_15m["macd_trend"].dropna().iloc[-1]
            rsi_4h = df_4h["rsi"].dropna().iloc[-1]
            macd_trend_4h = df_4h["macd_trend"].dropna().iloc[-1]
        except Exception as e:
            log_error(f"{ticker} – Error en indicadores: {e}")
            continue

        # Condición de entrada: precio actual cercano al nivel de entrada simulado
        if current_price <= entry_price * 1.005:
            row_with_data = row.copy()
            row_with_data["Current Price"] = round(current_price, 8)
            row_with_data["RSI_15m"] = round(rsi_15m, 2)
            row_with_data["MACD Trend 15m"] = "Alcista" if macd_trend_15m else "Bajista"
            row_with_data["RSI_4h"] = round(rsi_4h, 2)
            row_with_data["MACD Trend 4h"] = "Alcista" if macd_trend_4h else "Bajista"

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
        df_ready.to_csv("csv/tickers_ready_full.csv", index=False)
        print("✅ Archivo generado: tickers_ready_full.csv")
        print(df_ready[["Ticker", "Entry", "Current Price", "RSI_15m", "RSI_4h", "MACD Trend 15m", "MACD Trend 4h", "Unrealized PnL", "Results"]])


if __name__ == "__main__":
    check_entry_conditions_with_profit()