import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import pandas as pd
from tqdm import tqdm

from config.Config import Config
from TradingStrategy.Constants import TradingSymbol, BaseExchange
from HistoricalData.Data import StockDataRetriever
from HistoricalData.GenerateLTP import simulate_geometric_brownian_motion


if __name__ == "__main__":

    stocks = [
        {"trading_symbol": TradingSymbol.HDFCBANK, "exchange": BaseExchange.NSE},
        {"trading_symbol": TradingSymbol.RELIANCE, "exchange": BaseExchange.NSE},
        {"trading_symbol": TradingSymbol.TATAMOTORS, "exchange": BaseExchange.NSE},
    ]

    for stock in tqdm(stocks):
        stock_data_retriever = StockDataRetriever(
            trading_symbol=stock["trading_symbol"], exchange=stock["exchange"]
        )
        stock_data = stock_data_retriever.get_stock_historical_data(save_data=False)
        stock_data = stock_data.reset_index()
        stock_data["Date"] = pd.to_datetime(stock_data["Date"]).dt.date
        all_timestamps = []
        # For each date, generate 375 timestamps
        for date in stock_data["Date"]:
            # Start time: 09:15:00
            start_time = datetime.combine(date, datetime.min.time()) + timedelta(
                hours=9, minutes=15
            )

            for i in range(375):
                timestamp = start_time + timedelta(minutes=i)
                formatted_timestamp = timestamp.strftime("%Y-%m-%d:%H:%M:%S")
                all_timestamps.append(formatted_timestamp)

        ltps = []
        volumes = []
        for i in range(len(stock_data)):
            O, H, L, C, V = stock_data[["Open", "High", "Low", "Close", "Volume"]].iloc[
                i
            ]
            # Simulate LTP for 375 timestamps
            simulated_ltp, simulated_volume = simulate_geometric_brownian_motion(
                O, H, L, C, V, 375
            )
            ltps.extend(simulated_ltp)
            volumes.extend(simulated_volume)

        generated_ltp_data = pd.DataFrame(
            {
                "Timestamp": all_timestamps,
                "LTP": ltps,
                "Volume": volumes,
            }
        )
        file_path = os.path.join(
            Config.root_dir,
            "HistoricalData",
            stock["trading_symbol"],
            "generated_ltp_data.csv",
        )
        generated_ltp_data.to_csv(file_path, index=False)
        print(f"Saved generated LTP data for {stock['trading_symbol']} to {file_path}")
