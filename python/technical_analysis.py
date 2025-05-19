# --- technical_analysis.py ---
import requests
import pandas as pd
import numpy as np
from datetime import datetime

BITVAVO_URL = "https://api.bitvavo.com/v2"
INVESTED_MONEY = 500


def get_all_tickers():
    res = requests.get(f"{BITVAVO_URL}/markets")
    return [m['market'] for m in res.json()]

<<<<<<< HEAD
=======

>>>>>>> eed3b64 (new-logic-candlesfit)
def get_candles(ticker, interval="5m", limit=60):
    res = requests.get(f"{BITVAVO_URL}/{ticker}/candles", params={"interval": interval, "limit": limit})
    candles = res.json()
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df.sort_values("timestamp").reset_index(drop=True)


def frequent_levels(prices, bins=20):
    hist, edges = np.histogram(prices, bins=bins)
    idx_low = np.argmax(hist[:len(hist)//2])
    idx_high = np.argmax(hist[len(hist)//2:]) + len(hist)//2
    low_level = round((edges[idx_low] + edges[idx_low+1])/2, 4)
    high_level = round((edges[idx_high] + edges[idx_high+1])/2, 4)
    return low_level, high_level


def direction(df, idx, period=5):
    if idx < period:
        return None
    ma_prev = df['close'].iloc[idx-period:idx].mean()
    price_now = df['close'].iloc[idx]
    return "up" if price_now > ma_prev else "down"


def trade_with_direction(df):
    low_level, high_level = frequent_levels(df['close'])
    entry_price, exit_price, entry_date, exit_date = None, None, None, None

    for i in range(5, len(df)):
        price = df['close'].iloc[i]
        current_direction = direction(df, i)

        if entry_price is None:
            if price <= low_level and current_direction == "up":
                entry_price = price
                entry_date = df['timestamp'].iloc[i]
        elif entry_price is not None:
            if price >= high_level and current_direction == "down":
                exit_price = price
                exit_date = df['timestamp'].iloc[i]
                break

    if entry_price and exit_price:
        volatility = ((exit_price - entry_price) / entry_price) * 100
        trade_duration = exit_date - entry_date
        return entry_price, exit_price, volatility, trade_duration
    else:
        return None, None, None, None


def simulate_all():
    now = datetime.now().strftime("%Y-%m-%d")
    tickers = get_all_tickers()
    results, skipped = [], []

    for ticker in tickers:
        try:
<<<<<<< HEAD
            df = get_candles(ticker)
=======
            df = get_candles(ticker, interval="5m", limit=60)
>>>>>>> eed3b64 (new-logic-candlesfit)
            if len(df) < 10:
                skipped.append((ticker, "Insufficient data"))
                continue

            entry, exit_price, volatility, duration = trade_with_direction(df)

            if not entry or not exit_price:
                skipped.append((ticker, "No clear directional entry/exit"))
                continue

            avg_price = (entry + exit_price) / 2
            quantity = round(INVESTED_MONEY / avg_price, 4)
            profit_target = round(quantity * (exit_price - entry), 2)
            trade_time_str = str(duration)

            results.append({
                "Date": now,
                "Ticker": ticker,
                "Average Price": round(avg_price, 4),
                "Quantity": quantity,
                "Invested Money": INVESTED_MONEY,
                "Entry": round(entry, 4),
                "Exit": round(exit_price, 4),
                "Volatility between entry and exit": f"{round(volatility, 2)}%",
                "No entry": "No",
                "No Exit": "No",
                "Trigger Points": "Frequent Levels with Direction",
                "Profit Target": f"{profit_target} EUR",
                "Trade Time Expected": trade_time_str,
                "Results": "",
                "Trade Time": ""
            })

        except Exception as e:
            skipped.append((ticker, f"Exception: {e}"))

    df_results = pd.DataFrame(results)
    df_skipped = pd.DataFrame(skipped, columns=["Ticker", "Reason"])

    df_results.to_csv("csv/directional_frequent_levels.csv", index=False)
    df_skipped.to_csv("csv/directional_frequent_levels_skipped.csv", index=False)

    print(f"✅ {len(results)} tickers procesados correctamente.")
    print(f"⚠️ {len(skipped)} tickers omitidos. Revisa 'directional_frequent_levels_skipped.csv'.")


if __name__ == "__main__":
    simulate_all()
