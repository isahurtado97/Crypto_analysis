import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- Helper Functions ---
def generate_trade_plan(initial_investment: float, growth_rate_percent: float, months: list):
    results = []
    investment = initial_investment
    prev_investment = investment

    for i, month in enumerate(months):
        investment = prev_investment * (1 + growth_rate_percent / 100)
        monthly_goal = investment - prev_investment
        daily_goal = monthly_goal / 20

        results.append({
            "Month": month,
            "Daily Goal (€)": round(daily_goal, 2),
            "Monthly Goal (€)": round(monthly_goal, 2),
            "Compound Investment (€)": round(investment, 2)
        })

        prev_investment = investment

    return pd.DataFrame(results)

def save_trade(data: dict, asset_type: str):
    filename = f"trades_{asset_type.lower()}.csv"
    df = pd.DataFrame([data])
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)

def save_all_trades(df: pd.DataFrame, asset_type: str):
    filename = f"trades_{asset_type.lower()}.csv"
    df.to_csv(filename, index=False)

def load_trades(asset_type: str):
    filename = f"trades_{asset_type.lower()}.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        return df
    return pd.DataFrame()

def delete_trade(index: int, asset_type: str):
    filename = f"trades_{asset_type.lower()}.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        if 0 <= index < len(df):
            df.drop(index=index, inplace=True)
            df.reset_index(drop=True, inplace=True)
            df.to_csv(filename, index=False)

# --- Streamlit UI ---
st.set_page_config(page_title="Investment Planner & Trade Log", layout="wide")
st.title("📈 Investment Goal Planner & Trade Log")

# Sidebar config
st.sidebar.header("Goal Settings")
initial_investment = st.sidebar.number_input("Initial Investment (€)", min_value=100.0, value=2835.0, step=100.0)
growth_rate = st.sidebar.slider("Monthly Growth Rate (%)", min_value=1, max_value=200, value=50, step=1)
months_list = ["April", "May", "June", "July", "August", "September",
               "October", "November", "December", "January", "February", "March"]

# Tabs
tab1, tab2 = st.tabs(["📊 Goal Planner", "📝 Trade Log"])

with tab1:
    st.subheader("Compound Investment Projection")

    if "objectives_df" not in st.session_state:
        st.session_state.objectives_df = generate_trade_plan(initial_investment, growth_rate, months_list)

    edited_objectives = st.data_editor(
        st.session_state.objectives_df,
        num_rows="dynamic",
        use_container_width=True,
        key="objectives_editor"
    )

    if st.button("💾 Save Objectives Table"):
        # Detect number of rows left and recalculate
        remaining_months = edited_objectives["Month"].tolist()
        recalculated_df = generate_trade_plan(initial_investment, growth_rate, remaining_months)
        st.session_state.objectives_df = recalculated_df
        st.success("Objectives table recalculated and saved.")

    csv = st.session_state.objectives_df.to_csv(index=False).encode('utf-8')
    st.download_button("📁 Download CSV", data=csv, file_name="trading_plan.csv", mime="text/csv")

with tab2:
    st.subheader("Trade Log")
    asset_type = st.selectbox("Asset Type", ["Crypto", "Stocks", "Index", "Forex"])
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", datetime.today())
            ticker = st.text_input("Ticker")
            avg_price = st.number_input("Average Price", min_value=0.0)
            quantity = st.number_input("Quantity", min_value=0.0)
            entry = st.number_input("Entry Price", min_value=0.0)
            entry_time = st.time_input("Entry Time")
        with col2:
            exit = st.number_input("Exit Price", min_value=0.0)
            exit_time = st.time_input("Exit Time")
            volatility = st.number_input("Volatility %", min_value=0.0)
            profit_target = st.number_input("Profit Target", min_value=0.0)
            result = st.number_input("Result", value=0.0, format="%.2f")
        submitted = st.form_submit_button("Save Trade")

    if submitted:
        trade_data = {
            "Date": date,
            "Ticker": ticker,
            "Average Price": avg_price,
            "Quantity": quantity,
            "Entry": entry,
            "Entry Time": entry_time,
            "Exit": exit,
            "Exit Time": exit_time,
            "Volatility %": volatility,
            "Profit Target": profit_target,
            "Result": result
        }
        save_trade(trade_data, asset_type)
        st.success(f"✅ Trade saved for {asset_type} - {ticker}")
        st.experimental_rerun()

    st.markdown("---")
    st.subheader(f"📋 Saved Trades - {asset_type}")
    trades_df = load_trades(asset_type)

    if not trades_df.empty:
        with st.expander("🔍 Filter Options"):
            col1, col2 = st.columns(2)
            with col1:
                date_range = st.date_input("Filter by date range", [])
                if len(date_range) == 2:
                    trades_df = trades_df[
                        (trades_df["Date"] >= pd.to_datetime(date_range[0])) &
                        (trades_df["Date"] <= pd.to_datetime(date_range[1]))
                    ]
            with col2:
                tickers = trades_df["Ticker"].unique().tolist()
                selected_tickers = st.multiselect("Filter by Ticker", tickers, default=tickers)
                trades_df = trades_df[trades_df["Ticker"].isin(selected_tickers)]

        st.markdown("### ✏️ Edit Trade Table")
        edited_trades_df = st.data_editor(trades_df, num_rows="dynamic", use_container_width=True, key="trades_editor")

        if st.button("💾 Save Edited Trades"):
            save_all_trades(edited_trades_df, asset_type)
            st.success("Edited trades saved successfully.")
            st.experimental_rerun()

        st.markdown("### ❌ Remove Trade")
        index_to_delete = st.number_input("Select row index to delete:", min_value=0, max_value=len(trades_df)-1, step=1, key="delete_index")
        if st.button("Delete Trade"):
            delete_trade(index_to_delete, asset_type)
            st.success("Trade deleted.")
            st.experimental_rerun()

        total_trades = len(trades_df)
        total_invested = (trades_df["Average Price"] * trades_df["Quantity"]).sum()
        net_profit = trades_df["Result"].sum()
        win_rate = (trades_df["Result"] > 0).sum() / total_trades * 100

        st.markdown("### 📊 General Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", total_trades)
        col2.metric("Total Invested (€)", f"{total_invested:,.2f}")
        col3.metric("Net Profit (€)", f"{net_profit:,.2f}")
        col4.metric("Win Rate (%)", f"{win_rate:.2f}%")

        trades_df["Month"] = trades_df["Date"].dt.strftime("%Y-%m")
        monthly_summary = trades_df.groupby("Month").agg({
            "Result": "sum",
            "Ticker": "count"
        }).rename(columns={"Result": "Net Profit", "Ticker": "# Trades"})

        st.markdown("### 📆 Monthly Summary")
        st.dataframe(monthly_summary, use_container_width=True)

        ticker_summary = trades_df.groupby("Ticker").agg({
            "Result": "sum",
            "Quantity": "sum"
        }).rename(columns={"Result": "Total Profit", "Quantity": "Total Quantity"})

        st.markdown("### 🧾 Ticker Summary")
        st.dataframe(ticker_summary, use_container_width=True)

        if "Result" in trades_df.columns:
            st.line_chart(trades_df[["Date", "Result"]].set_index("Date"))
    else:
        st.info("No data available for this asset type.")