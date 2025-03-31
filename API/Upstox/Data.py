import os
import sys
import re
from datetime import datetime, date
from typing import List, Optional
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import requests

from API.Upstox.UpstoxLogin import Login
from API.Upstox.DataExtractor import DataExtractor
from API.Upstox.Constants import Exchange, TransactionType, ProductType, Segment, HistoricalDataInterval


class Data:
    """
    Base class for Upstox API data operations.
    """
    def __init__(self, access_token: str):
        """
        Initialize the Data class with the provided access token.
        """
        self.access_token = access_token
        self.live_url = "https://api.upstox.com/v2"

    def validate_response(self, response, endpoint):
        """
        Check the response from the API.
        """
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error accessing endpoint: {endpoint}, Response: {response.json()}\n")
            return None
    
    def _convert_date_format(self, date_given: str):
        """
        Convert the date format from DD-MM-YYYY to YYYY-MM-DD.
        """
        try:
            date_obj = datetime.strptime(date_given, "%d-%m-%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD-MM-YYYY.")
        return date_obj.strftime("%Y-%m-%d")
         
        
    def _generate_instrument_token(self, trading_symbol: str, exchange: Exchange):
        """
        Generate the instrument key for the given trading symbol and exchange.
        """
        if exchange == Exchange.NSE:
            extractor = DataExtractor()
            trading_instrument = extractor.get_nse_trading_instrument_for_symbol(trading_symbol)
            return trading_instrument
                
        elif exchange == Exchange.BSE:
            raise NotImplementedError("BSE exchange is not supported yet.")
        
        elif exchange == Exchange.NFO:
            raise NotImplementedError("NFO exchange is not supported yet.")
        
        elif exchange == Exchange.BFO:
            raise NotImplementedError("BFO exchange is not supported yet.")
        
        elif exchange == Exchange.CDS:
            raise NotImplementedError("CDS exchange is not supported yet.")
        
        elif exchange == Exchange.BCD:
            raise NotImplementedError("BCD exchange is not supported yet.")
        
        elif exchange == Exchange.NSCOM:
            raise NotImplementedError("NSCOM exchange is not supported yet.")
        
        elif exchange == Exchange.MCX:
            raise NotImplementedError("MCX exchange is not supported yet.")
        
        else:
            raise ValueError(f"Unsupported exchange: {exchange}. Please provide a valid exchange.")


class UserData(Data):
    """
    Class for Upstox API user data operations.
    """
    def __init__(self, access_token: str):
        """
        Initialize the UserData class with the provided access token.
        """
        super().__init__(access_token)

    def get_profile(self):
        """
        Get the profile information of the user.
        Uses GET method to fetch user profile.
        """
        endpoint = "user/profile"
        url = f"{self.live_url}/{endpoint}"
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        return self.validate_response(response, endpoint)
        
    def get_fund_and_margin(self):
        """
        Get the funds and margin information of the user.
        Uses GET method to fetch fund and margin.
        """
        endpoint = "user/get-funds-and-margin"
        url = f"{self.live_url}/{endpoint}"
        params={
            'segment': 'SEC'
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)


class OrderData(Data):
    """
    Class for Upstox API order data operations.
    """
    def __init__(self, access_token: str):
        """
        Initialize the OrderData class with the provided access token.
        """
        super().__init__(access_token)

    def get_order_details(self, order_id: str):
        """
        Get the order details for the given order ID.
        Uses GET method to fetch order details.
        """
        endpoint = "order/details"
        url = f"{self.live_url}/{endpoint}"
        params={
            'order_id': order_id
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
    
    def get_order_history(self, order_id: Optional[str]=None, tag : Optional[str] = None):
        """
        Get the order history for the given order ID or tag.
        Uses GET method to fetch order history.
        """
        endpoint = "order/history"
        url = f"{self.live_url}/{endpoint}"
        params={}
        if order_id:
            params['order_id'] = order_id
        if tag:
            params['tag'] = tag
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
    
    def get_order_book(self):
        """
        Get the order book of the user.
        Uses GET method to fetch order book.
        """
        endpoint = "order/retrieve-all"
        url = f"{self.live_url}/{endpoint}"
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        return self.validate_response(response, endpoint)
    
    def get_trades_for_today(self):
        """
        Get the trades for today.
        Uses GET method to fetch today's trades.
        """
        endpoint = "order/trades/get-trades-for-day"
        url = f"{self.live_url}/{endpoint}"
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        return self.validate_response(response, endpoint)

    def get_order_trades(self, order_id: str):
        """
        Get the all trades you executed for the given order ID.
        Uses GET method to fetch order trades.
        """
        endpoint = "order/trades"
        url = f"{self.live_url}/{endpoint}"
        params={
            'order_id': order_id
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)

    def get_trade_history(self, start_date: str, end_date: str, page_number: int = 1, page_size: int = 2*31-1, segment: Optional[Segment]=None):
        """
        Get the trade history for the given date range.
        Uses GET method to fetch trade history.
        Enter From and To date in DD-MM-YYYY format.
        Both From and To date should be in the last 3 Financial Years.
        """
        start_date = self._convert_date_format(start_date)
        end_date = self._convert_date_format(end_date)
        endpoint = "charges/historical-trades"
        url = f"{self.live_url}/{endpoint}"
        params={
            'start_date': start_date,
            'end_date': end_date,
            'page_number': page_number,
            'page_size': page_size
        }
        if segment:
            params['segment'] = segment
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)

class PortfolioData(Data):
    """
    Class for Upstox API portfolio data operations.
    """
    def __init__(self, access_token: str):
        """
        Initialize the PortfolioData class with the provided access token.
        """
        super().__init__(access_token)

    def get_positions(self):
        """
        Get the positions of the user.
        Uses GET method to fetch short-term positions.
        """
        endpoint = "portfolio/short-term-positions"
        url = f"{self.live_url}/{endpoint}"
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        return self.validate_response(response, endpoint)
        
    def get_holdings(self):
        """
        Get the holdings of the user.
        Uses GET method to fetch long-term positions.
        """
        endpoint = "portfolio/long-term-holdings"
        url = f"{self.live_url}/{endpoint}"
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        return self.validate_response(response, endpoint)


class MarketQuoteData(Data):
    """
    Class for Upstox API market quote data operations.
    """
    def __init__(self, access_token: str):
        """
        Initialize the MarketQuoteData class with the provided access token.
        """
        super().__init__(access_token)

    def get_ltp(self, trading_symbol: str, exchange: Exchange):
        """
        Get the last traded price (LTP) for the given instrument.
        Uses GET method to fetch the LTP.
        """
        endpoint = "market-quote/ltp"
        url = f"{self.live_url}/{endpoint}"
        params={
            'instrument_key': self._generate_instrument_token(trading_symbol=trading_symbol, exchange=exchange)
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)

    def get_multiple_ltp(self, trading_symbols: List[str], exchange: List[Exchange], max_results: int = 5):
        """
        Get the last traded price (LTP) for multiple instruments.
        """
        if len(trading_symbols) != len(exchange):
            raise ValueError("The length of trading_symbols and exchange must be the same.")
        if len(trading_symbols) > max_results:
            raise ValueError(f"The number of trading symbols per request cannot exceed {max_results}.")
        
        endpoint = "market-quote/ltp"
        url = f"{self.live_url}/{endpoint}"
        instrument_tokens = [self._generate_instrument_token(trading_symbol=trading_symbol, exchange=exchange) for trading_symbol, exchange in zip(trading_symbols, exchange)]
        instrument_tokens_str = ','.join(instrument_tokens)        

        params={
            'instrument_key': instrument_tokens_str
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
    

class BrokerageData(Data):
    """
    Class for Upstox API brokerage data operations.
    """
    def __init__(self, access_token: str):
        """
        Initialize the BrokerageData class with the provided access token.
        """
        super().__init__(access_token)

    def get_brokerage(self, trading_symbol: str, exchange: Exchange, quantity: int, product: ProductType, transaction_type: TransactionType, price: float):
        """
        Get the brokerage details for the given order ID.
        Uses GET method to fetch brokerage details.
        """
        endpoint = "charges/brokerage"
        url = f"{self.live_url}/{endpoint}"
        params={
            'instrument_token': self._generate_instrument_token(trading_symbol=trading_symbol, exchange=exchange),
            'quantity': quantity,
            'product': product,
            'transaction_type': transaction_type,
            'price': price
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
        

class ProfitAndLossData(Data):
    """
    Class for Upstox API profit and loss data operations.
    This works for only one financial year at a time.
    """
    def __init__(self, access_token: str):
        """
        Initialize the ProfitAndLossData class with the provided access token.
        """
        super().__init__(access_token)

    def get_profit_and_loss_report(self, segment: Segment, financial_year: str, page_number: int = 1, page_size: int = 2*31-1, from_date: Optional[str]=None, to_date: Optional[str]=None):
        """
        Get the profit and loss report for the given date range.
        Uses GET method to fetch profit and loss report.
        Enter From and To date in DD-MM-YYYY format.
        Enter financial year in YYYY-YYYY format.
        From Date and To Date should be within the financial year.
        """
        endpoint = "trade/profit-loss/data"
        url = f"{self.live_url}/{endpoint}"
        params={
            'segment': segment,
            'financial_year': self._get_financial_year(financial_year),
            'page_number': page_number,
            'page_size': page_size
        }
        if from_date:
            self._check_if_date_in_financial_year(from_date, financial_year)
            params['from_date'] = from_date
        if to_date:
            self._check_if_date_in_financial_year(to_date, financial_year)
            params['to_date'] = to_date
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
    
    def trade_charges(self, segment: Segment, financial_year: str, from_date: Optional[str]=None, to_date: Optional[str]=None):
        """
        Get the trade charges for the given date range.
        Uses GET method to fetch trade charges.
        Enter From and To date in DD-MM-YYYY format.
        Enter financial year in YYYY-YYYY format.
        From Date and To Date should be within the financial year.
        """
        endpoint = "trade/profit-loss/charges"
        url = f"{self.live_url}/{endpoint}"
        params={
            'segment': segment,
            'financial_year': self._get_financial_year(financial_year)
        }
        if from_date:
            self._check_if_date_in_financial_year(from_date, financial_year)
            params['from_date'] = from_date
        if to_date:
            self._check_if_date_in_financial_year(to_date, financial_year)
            params['to_date'] = to_date
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
    
    def get_report_metadata(self, segment: Segment, financial_year: str, from_date: Optional[str]=None, to_date: Optional[str]=None):
        """
        Get the report metadata for the given date range.
        Uses GET method to fetch report metadata.
        Enter From and To date in DD-MM-YYYY format.
        Enter financial year in YYYY-YYYY format.
        From Date and To Date should be within the financial year.
        """
        endpoint = "trade/profit-loss/metadata"
        url = f"{self.live_url}/{endpoint}"
        params={
            'segment': segment,
            'financial_year': self._get_financial_year(financial_year)
        }
        if from_date:
            self._check_if_date_in_financial_year(from_date, financial_year)
            params['from_date'] = from_date
        if to_date:
            self._check_if_date_in_financial_year(to_date, financial_year)
            params['to_date'] = to_date
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
    
    def _check_if_date_in_financial_year(self, date_given: str, financial_year: str):
        """
        Check if the given date is within the financial year.
        """
        try:
            date_obj = datetime.strptime(date_given, "%d-%m-%Y").date()
        except:
            raise ValueError("Invalid date format. Use DD-MM-YYYY.")
        try:
            start_year, end_year = map(int, financial_year.split('-'))
        except:
            raise ValueError("Invalid financial year format. Use YYYY-YYYY.")
        
        fy_start_date = date(start_year, 4, 1)
        fy_end_date = date(end_year, 3, 31)
        if not (fy_start_date <= date_obj <= fy_end_date):
            raise ValueError(f"Date {date_given} is not within the financial year {financial_year}.")
        return True

    def _get_financial_year(self, financial_year: str):
        """
        Get the current financial year.
        """
        pattern = r"^(19|20)\d{2}-(19|20)\d{2}$"
        if not re.match(pattern, financial_year):
            raise ValueError("Invalid financial year format. Use YYYY-YYYY.")
        start_year, end_year = map(int, financial_year.split('-'))
        if end_year != start_year + 1:
            raise ValueError("Invalid financial year range. Must be consecutive years.")
        return financial_year[2:4]+financial_year[7:] 


class HistoricalData(Data):
    """
    Class for Upstox API historical data operations.
    It retrieves historical data as OHLC (Open, High, Low, Close) values.
    """
    def __init__(self, access_token: str):
        """
        Initialize the HistoricalData class with the provided access token.
        """
        super().__init__(access_token)

    def get_historical_data(self, trading_symbol: str, exchange: Exchange, interval: HistoricalDataInterval, to_date: str, from_date: Optional[str]=None):
        """
        Get historical data for the given instrument token.
        Give the date in DD-MM-YYYY format.
        Uses GET method to fetch historical data.
        """
        to_date = self._convert_date_format(to_date)
        instrument_token = self._generate_instrument_token(trading_symbol=trading_symbol, exchange=exchange)
        endpoint = f"historical-candle/{self._convert_instrument_token_for_url_parse(instrument_token)}/{interval}/{to_date}"
        if from_date:
            from_date = self._convert_date_format(from_date)
            endpoint += f"/{from_date}"
        url = f"{self.live_url}/{endpoint}"
        params={
            'instrument_token': instrument_token,
            'interval': interval,
            'from_date': from_date,
            'to_date': to_date
        }
        headers = {
        'Accept': 'application/json',
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
    
    def get_current_trading_day_data(self, trading_symbol: str, exchange: Exchange, interval: HistoricalDataInterval):
        """
        Get the current trading day data for the given instrument token.
        Uses Intraday API for current trading day data.
        Uses GET method to fetch current trading day data.
        One-minute and 30-minute candle data are accessible solely for the preceding six months.
        """
        instrument_token = self._generate_instrument_token(trading_symbol=trading_symbol, exchange=exchange)
        endpoint = f"historical-candle/intraday/{self._convert_instrument_token_for_url_parse(instrument_token)}/{interval}"
        url = f"{self.live_url}/{endpoint}"
        params={
            'instrument_token': instrument_token,
            'interval': interval
        }
        headers = {
        'Accept': 'application/json',
        }

        response = requests.request("GET", url, headers=headers, params=params)
        return self.validate_response(response, endpoint)
    
    def _convert_instrument_token_for_url_parse(self, instrument_token: str):
        """
        Convert the instrument token for URL parsing.
        """
        # Replace | with %7C
        return instrument_token.replace("|", "%7C")


class MarketInformationData(Data):
    """
    Class for Upstox API market information data operations.
    """
    def __init__(self, access_token: str):
        """
        Initialize the MarketInformationData class with the provided access token.
        """
        super().__init__(access_token)

    def get_market_holiday_info(self, date_given: str):
        """
        Get the market holidays for the given date.
        Give the date in DD-MM-YYYY format.
        Uses GET method to fetch market holidays.
        """
        date_given = self._convert_date_format(date_given)
        endpoint = f"market/holidays/{date_given}"
        url = f"{self.live_url}/{endpoint}"
        headers = {
        'Accept': 'application/json',
        }

        response = requests.request("GET", url, headers=headers)
        return self.validate_response(response, endpoint)
        
    def get_market_timings(self, date_given: str):
        """
        Get the market timings for the given date.
        Give the date in DD-MM-YYYY format.
        Uses GET method to fetch market timings.
        """
        date_given = self._convert_date_format(date_given)
        endpoint = f"market/timings/{date_given}"
        url = f"{self.live_url}/{endpoint}"
        headers = {
        'Accept': 'application/json',
        }

        response = requests.request("GET", url, headers=headers)
        return self.validate_response(response, endpoint)
    
    def get_exchange_status(self, exchange: Exchange):
        """
        Get the market status for the given exchange.
        Uses GET method to fetch exchange status.
        """
        endpoint = f"market/status/{exchange}"
        url = f"{self.live_url}/{endpoint}"
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers)
        return self.validate_response(response, endpoint)

if __name__ == '__main__':
    access_token = Login().login()
    data = Data(access_token)

    # # Example usage of UserData
    # print("User Data Class Usage:\n")
    # user_data = UserData(access_token)
    # print(f"User Profile: {user_data.get_profile()}")
    # print(f"Fund and Margin: {user_data.get_fund_and_margin()}")
    # print("=========================================================\n")

    # # Example usage of PortfolioData
    # print("Portfolio Data Class Usage:\n")
    # portfolio_data = PortfolioData(access_token)
    # print(f"Positions: {portfolio_data.get_positions()}")
    # print(f"Holdings: {portfolio_data.get_holdings()}")
    # print("=========================================================\n")

    # # Example usage of MarketQuoteData
    # print("Market Quote Data Class Usage:\n")
    # market_data = MarketQuoteData(access_token)
    # print(f"LTP: {market_data.get_ltp('RELIANCE', Exchange.NSE)}")
    # print(f"Multiple LTP: {market_data.get_multiple_ltp(['RELIANCE', 'TCS'], [Exchange.NSE, Exchange.NSE])}")
    # print("=========================================================\n")

    # # Example usage of OrderData
    # print("Order Data Class Usage:\n")
    # order_data = OrderData(access_token)
    # print(f"Order Details: {order_data.get_order_details('250331025005353')}")
    # print(f"Order History: {order_data.get_order_history()}")
    # print(f"Order Book: {order_data.get_order_book()}")
    # print(f"Trades for Today: {order_data.get_trades_for_today()}")
    # print(f"Order Trades: {order_data.get_order_trades('250331025005353')}")
    # print(f"Trade History: {order_data.get_trade_history(start_date='01-01-2024', end_date='31-03-2025')}")
    # print("=========================================================\n")

    # # Example usage of BrokerageData
    # print("Brokerage Data Class Usage:\n")
    # brokerage_data = BrokerageData(access_token)
    # print(f"Brokerage: {brokerage_data.get_brokerage(trading_symbol='RELIANCE', exchange=Exchange.NSE, quantity=1, product=ProductType.DELIVERY, transaction_type="BUY", price=1000)}")
    # print("=========================================================\n")

    # # Example usage of ProfitAndLossData
    # print("Profit and Loss Data Class Usage:\n")
    # profit_loss_data = ProfitAndLossData(access_token)
    # print(f"Profit and Loss Report: {profit_loss_data.get_profit_and_loss_report(segment=Segment.EQ, financial_year='2025-2026', from_date='05-04-2025', to_date='31-01-2026')}")
    # print(f"Trade Charges: {profit_loss_data.trade_charges(segment=Segment.EQ, financial_year='2025-2026')}")
    # print(f"Report Metadata: {profit_loss_data.get_report_metadata(segment=Segment.EQ, financial_year='2025-2026')}")
    # print("=========================================================\n")

    # # Example usage of HistoricalData
    # print("Historical Data Class Usage:\n")
    # historical_data = HistoricalData(access_token)
    # print(f"Historical Data: {historical_data.get_historical_data(trading_symbol='RELIANCE', exchange=Exchange.NSE, interval=HistoricalDataInterval.MONTH, from_date='01-01-2024', to_date='15-09-2024')}")
    # print(f"Current Trading Day Data: {historical_data.get_current_trading_day_data(trading_symbol='RELIANCE', exchange=Exchange.NSE, interval=HistoricalDataInterval.THRITY_MINUTES)}")
    # print("=========================================================\n")

    # # Example usage of MarketInformationData
    # print("Market Information Data Class Usage:\n")
    # market_info_data = MarketInformationData(access_token)
    # print(f"Market Holiday Info: {market_info_data.get_market_holiday_info(date_given='31-03-2025')}")
    # print(f"Market Timings: {market_info_data.get_market_timings(date_given='26-03-2025')}")
    # print(f"Exchange Status: {market_info_data.get_exchange_status(exchange=Exchange.NSE)}")
    # print("=========================================================\n")