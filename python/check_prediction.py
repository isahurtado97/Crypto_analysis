import pandas as pd
import requests
from datetime import datetime, timedelta

BITVAVO_URL = "https://api.bitvavo.com/v2"

def get_candles_1m(ticker, start_dt, end_dt):
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    url = f"{BITVAVO_URL}/{ticker}/candles"
    try:
        res = requests.get(url, params={"interval": "1m", "start": start_ms, "end": end_ms})
        res.raise_for_status()
        candles = res.json()
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        print(f"⚠️ Error con {ticker}: {e}")
        return None

def check_predictions_last_24h():
    df = pd.read_csv("csv/tickers_ready_full.csv")
    updated_rows = []

    now = datetime.utcnow()
    start = now - timedelta(hours=24)

    for _, row in df.iterrows():
        ticker = row["Ticker"]
        entry_price = row["Entry"]
        exit_price = row["Exit"]

        candles = get_candles_1m(ticker, start, now)
        if candles is None or candles.empty:
            row["Results"] = "No data"
            row["Trade Time"] = ""
            updated_rows.append(row)
            continue

        entry_hit_time = None
        exit_hit_time = None

        for _, candle in candles.iterrows():
            if entry_hit_time is None and candle["low"] <= entry_price:
                entry_hit_time = candle["timestamp"]
            elif entry_hit_time is not None and candle["high"] >= exit_price:
                exit_hit_time = candle["timestamp"]
                break

        if entry_hit_time and exit_hit_time:
            row["Results"] = "Trade executed successfully"
            row["Trade Time"] = str(exit_hit_time - entry_hit_time)
        elif entry_hit_time:
            row["Results"] = "Entry only"
            row["Trade Time"] = ""
        else:
            row["Results"] = "Not triggered"
            row["Trade Time"] = ""

        updated_rows.append(row)

    df_checked = pd.DataFrame(updated_rows)
    df_checked.to_csv("csv/tickers_ready_24h_checked.csv", index=False)
    print("✅ Verificación de las últimas 24h completada: tickers_ready_24h_checked.csv")

if __name__ == "__main__":
    check_predictions_last_24h()