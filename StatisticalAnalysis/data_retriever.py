from datetime import datetime

import yfinance as yf

def get_today_date():
    """
    Get today's date in the format 'YYYY-MM-DD'
    :return: Today's date in the format 'YYYY-MM-DD'
    """
    return datetime.now().strftime('%Y-%m-%d')

def get_stock_historical_data(stock_ticker_symbol: str, start_date: str, end_date: str = get_today_date(), stock_name: str = None):
    """
    Download historical stock data for a given stock ticker symbol and save it to a CSV file.
    :param stock_ticker_symbol: Stock ticker symbol
    :param start_date: Start date in the format 'YYYY-MM-DD'
    :param end_date: End date in the format 'YYYY-MM-DD'
    :param stock_name: Name of the stock
    """
    stock = yf.download(stock_ticker_symbol, start=start_date, end=end_date)
    if stock_name is not None:
        stock.to_csv(f'Data/{stock_name}.csv')
        print(f"Downloaded {stock_name} data")
    else:
        stock.to_csv(f'Data/{stock_ticker_symbol}.csv')
        print(f"Downloaded {stock_ticker_symbol} data")


if __name__ == "__main__":
    today = get_today_date()
    get_stock_historical_data("HDFCBANK.NS", "2000-01-01", today, "HDFCBank")