import os
import sys
from typing import Dict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from TradingStrategy.Constants import TradingSymbol
from TradingStrategy.StrategyData import TradingStrategyData
from TradingStrategy.Constants import BaseExchange, BaseTransactionType
from TradingStrategy.ApiConstantsMapping import UpstoxConstantsMapping as Mappings
from API.Upstox.UpstoxLogin import Login, SandboxLogin
from API.Upstox.Data import MarketQuoteData
from API.Upstox.Constants import Segment
from API.Upstox.TradeExecutor import OrderAPI, OrderAPIv3, PlaceOrderData

def simple_trading_strategy(trading_symbol: TradingSymbol, ltp: float, buy_price: float, sell_price: float, quantity: int) -> TradingStrategyData:
    """
    A simple trading strategy which buys is if LTP is less than buy price and sells if LTP is greater than sell price.
    Args:
        trading_symbol (TradingSymbol): The trading symbol for the stock.
        ltp (float): The last traded price of the stock.
        buy_price (float): The price at which to buy the stock.
        sell_price (float): The price at which to sell the stock.
        quantity (int): The number of shares to trade.
    Returns:
        trade_details (TradingStrategyData): The trade details containing transaction type and other information.
    """
    # Check if the trading symbol is valid
    if trading_symbol not in TradingSymbol:
        raise ValueError(f"Invalid trading symbol: {trading_symbol}")

    # Check if the price and quantity are valid
    if ltp <= 0 or quantity <= 0:
        raise ValueError("Price and quantity must be positive numbers.")

    # Initialize the trade details
    trade_details = TradingStrategyData(
        trading_symbol=trading_symbol,
        ltp=ltp,
        buy_price=buy_price,
        sell_price=sell_price,
        quantity=quantity,
        transaction_type=None
    )

    # Check if the LTP is less than the buy price
    if ltp < buy_price:
        trade_details.transaction_type = BaseTransactionType.BUY

    # Check if the LTP is greater than the sell price
    elif ltp > sell_price:
        trade_details.transaction_type = BaseTransactionType.SELL
    else:
        pass

    # Return the trade details
    return trade_details

def place_order(trade_details: TradingStrategyData, access_token: str = None):
    """
    Places an order based on the trade details.
    Args:
        trade_details (Dict): The trade details containing transaction type and other information.
    Returns:
        order_ids (Dict): A dictionary containing the order IDs for the placed orders.
    """
    if trade_details.transaction_type:
        order_api = OrderAPI(access_token=access_token)
        order_api_v3 = OrderAPIv3(access_token=access_token)

        order_data = PlaceOrderData(trading_symbol=trade_details.trading_symbol, 
                                    transaction_type=trade_details.transaction_type,
                                    quantity=trade_details.quantity,
                                    exchange=Mappings.exchange(BaseExchange.NSE),
                                    )

        order_response = order_api.place_order(order_data=order_data)
        print(f"Order response: {order_response}")
        order_id = order_response["data"]["order_id"]
        order_response_v3 = order_api_v3.place_order(order_data=order_data)
        order_id_v3 = order_response_v3["data"]["order_ids"][0]
        print(f"Order response v3: {order_response_v3}")
        return {
            "order_id": order_id,
            "order_id_v3": order_id_v3,
        }
    else:
        print("No trade action taken.")
        return None
    

if __name__ == "__main__":
    # Initialize UpstoxLogin
    access_token = Login().login()
    sandbox_access_token = SandboxLogin().login()
    print("Logged in successfully!")

    # Fetch LTP of IDEA
    trading_symbol = TradingSymbol.IDEA
    segment = Segment.EQUITY
    exchange = BaseExchange.NSE
    market_quote = MarketQuoteData(access_token=access_token)
    ltp_data = market_quote.get_ltp(trading_symbol=trading_symbol, exchange=exchange)
    print(f"LTP of {TradingSymbol.IDEA}: {ltp_data}")
    
    key = f"{exchange}_{segment}:{trading_symbol}"
    ltp = ltp_data["data"][key]["last_price"]

    # Run the trading strategy for example 1
    buy_price = 7
    sell_price = 10
    quantity = 2
    trade_details = simple_trading_strategy(trading_symbol, ltp, buy_price, sell_price, quantity)
    print(f"Trade details: {trade_details}")
    # order_response = place_order(trade_details, sandbox_access_token)

    # Run the trading strategy for example 2
    buy_price = 5
    sell_price = 10
    quantity = 2
    trade_details = simple_trading_strategy(trading_symbol, ltp, buy_price, sell_price, quantity)
    print(f"Trade details: {trade_details}")
    # order_response = place_order(trade_details, sandbox_access_token)

    # Run the trading strategy for example 3
    buy_price = 5
    sell_price = 6
    quantity = 2
    trade_details = simple_trading_strategy(trading_symbol, ltp, buy_price, sell_price, quantity)
    print(f"Trade details: {trade_details}")
    # order_response = place_order(trade_details, sandbox_access_token)