import os
import sys
import json
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from config.Config import Config
from API.Upstox.Data import HistoricalData
from API.Upstox.UpstoxLogin import Login as UpstoxLogin
from TradingStrategy.Constants import TradingSymbol, BaseExchange


class StockDataRetriever:
    """
    Class to retrieve historical stock data using yfinance.
    This class provides methods to fetch historical stock data for a given trading symbol
    """

    def __init__(
        self, trading_symbol: TradingSymbol, exchange: BaseExchange = BaseExchange.NSE
    ):
        """
        Initialize the StockDataRetriever with a trading symbol and exchange.
        :param trading_symbol: Trading symbol of the stock
        :param exchange: Exchange where the stock is listed
        """
        self.trading_symbol = trading_symbol
        self.exchange = exchange

        self.folder_path = os.path.join(
            Config.root_dir, "HistoricalData", trading_symbol
        )
        os.makedirs(self.folder_path, exist_ok=True)

    def get_stock_historical_data(
        self, start_date: str = None, end_date: str = None, save_data: bool = False
    ):
        """
        Get historical stock data using yfinance.
        :param start_date: Start date in 'DD-MM-YYYY' format
        :param end_date: End date in 'DD-MM-YYYY' format
        """
        if self.exchange == BaseExchange.NSE:
            stock_ticker_symbol = f"{self.trading_symbol}.NS"
        elif self.exchange == BaseExchange.BSE:
            stock_ticker_symbol = f"{self.trading_symbol}.BO"
        else:
            raise ValueError(
                "Unsupported exchange. Supported exchanges are NSE and BSE."
            )

        if start_date is None:
            start_date = "01-01-1900"
        if end_date is None:
            end_date = datetime.now().strftime("%d-%m-%Y")

        start_date = datetime.strptime(start_date, "%d-%m-%Y").strftime("%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%d-%m-%Y").strftime("%Y-%m-%d")

        stock_data = yf.Ticker(stock_ticker_symbol).history(
            start=start_date,
            end=end_date,
            interval="1d",
            actions=True,
            auto_adjust=True,
            back_adjust=True,
        )

        if save_data:
            file_path = os.path.join(self.folder_path, "daily_OHLCV.csv")
            stock_data.to_csv(file_path, index=True, header=True)
            print(f"Saved historical data for {self.trading_symbol} to {file_path}")

        return stock_data

    def get_stock_data_minute_candles(
        self, start_date: str = None, end_date: str = None, save_data: bool = False
    ):
        """
        Get historical stock data using yfinance.
        :param start_date: Start date in 'DD-MM-YYYY' format
        :param end_date: End date in 'DD-MM-YYYY' format
        """
        if end_date is None:
            end_date = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")

        if start_date is None:
            start_date = (
                datetime.strptime(end_date, "%d-%m-%Y") - timedelta(days=175)
            ).strftime("%d-%m-%Y")

        # Check if end_date - start_date is more than 175 days
        if (
            datetime.strptime(end_date, "%d-%m-%Y")
            - datetime.strptime(start_date, "%d-%m-%Y")
        ).days > 175:
            start_date = (
                datetime.strptime(end_date, "%d-%m-%Y") - timedelta(days=175)
            ).strftime("%d-%m-%Y")

        access_token = UpstoxLogin().login()
        historical_data_api = HistoricalData(access_token)
        stock_data_minute_response = historical_data_api.get_historical_data(
            trading_symbol=self.trading_symbol,
            exchange=self.exchange,
            interval="1minute",
            from_date=start_date,
            to_date=end_date,
        )
        if (
            stock_data_minute_response is None
            or stock_data_minute_response["status"] != "success"
        ):
            raise ValueError(
                f"Error fetching data, Message: {stock_data_minute_response if stock_data_minute_response else 'No data found'}"
            )

        stock_data_minute_raw = stock_data_minute_response["data"]["candles"]
        stock_data_minute = pd.DataFrame(
            columns=[
                "Timestamp",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "OpenInterest",
            ],
            data=stock_data_minute_raw,
        )

        if save_data:
            file_path = os.path.join(self.folder_path, "minute_OHLCV.csv")
            stock_data_minute.to_csv(file_path, index=False, header=True)
            print(
                f"Saved Minute by Minute historical data for {self.trading_symbol} to {file_path}"
            )

        return stock_data_minute
