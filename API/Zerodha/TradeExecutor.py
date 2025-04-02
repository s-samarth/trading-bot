import os
import sys
import json
from typing import Optional
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from dotenv import load_dotenv
from pydantic import BaseModel
from kiteconnect import KiteConnect

from API.Zerodha.ZerodhaLogin import Login


class PlaceOrderData(BaseModel):
    tradingsymbol: str
    transaction_type: str
    quantity: int = 1
    variety: str = KiteConnect.VARIETY_REGULAR
    exchange: str = KiteConnect.EXCHANGE_NSE
    product: str = KiteConnect.PRODUCT_CNC
    order_type: str = KiteConnect.ORDER_TYPE_MARKET
    price: Optional[float] = None
    validity: Optional[str] = None
    disclosed_quantity: Optional[int] = None
    trigger_price: Optional[float] = None
    tag: Optional[str] = None


class GTTOrderData(BaseModel):
    transaction_type: str
    quantity: int = 1
    price: float
    order_type: str = KiteConnect.ORDER_TYPE_LIMIT
    product: str = KiteConnect.PRODUCT_CNC


class GTTData(BaseModel):
    trigger_type: str = KiteConnect.GTT_TYPE_SINGLE
    tradingsymbol: str
    exchange: str = KiteConnect.EXCHANGE_NSE
    trigger_values: list[float]  # List of values to buy or sell at
    last_price: float
    orders: list[GTTOrderData]


class TradeExecutor:
    def __init__(self, kite: KiteConnect):
        """
        Initialize the TradeExecutor class with the KiteConnect instance.
        """
        self.kite = kite

    def place_order(self, order_data: PlaceOrderData):
        """
        Place an order using the KiteConnect API.
        """
        try:
            order_params = order_data.model_dump()
            order_id = self.kite.place_order(**order_params)
            print(f"Order placed successfully. Order ID: {order_id}")
            return order_id
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

    def cancel_order(
        self,
        order_id: str,
        variety: str = KiteConnect.VARIETY_REGULAR,
        parent_order_id: Optional[str] = None,
    ):
        """
        Cancel an order using the KiteConnect API.
        """
        try:
            response = self.kite.cancel_order(
                order_id=order_id, variety=variety, parent_order_id=parent_order_id
            )
            print(f"Order cancelled successfully. Response: {response}")
            return response
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return None

    def place_gtt(self, gtt_data: GTTData):
        """
        Place a GTT (Good Till Triggered) order using the KiteConnect API.
        """
        try:
            gtt_params = gtt_data.model_dump()
            gtt_id = self.kite.place_gtt(**gtt_params)
            print(f"GTT order placed successfully. GTT ID: {gtt_id}")
            return gtt_id
        except Exception as e:
            print(f"Error placing GTT order: {e}")
            return None


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    # Initialize the login class
    kite = KiteConnect(api_key=os.getenv("ZERODHA_API_KEY"))
    zerodha_login = Login(kite=kite)

    # Login to Zerodha
    kite = zerodha_login.login()
    if kite is not None:
        pass
        # Executing the Trades
        trade_executor = TradeExecutor(kite=kite)
        # Example of placing a buy order
        place_order_data = PlaceOrderData(
            tradingsymbol="IDEA",
            transaction_type=KiteConnect.TRANSACTION_TYPE_BUY,
            quantity=1,
        )
        buy_order = trade_executor.place_order(order_params=place_order_data)
        print(f"Buy Order: {buy_order}")

        # Example of cancelling an order
        if buy_order:
            cancel_order_response = trade_executor.cancel_order(order_id=buy_order)
            print(f"Cancel Order Response: {cancel_order_response}")

        # Example of creating GTT orders
        gtt_order_data = GTTOrderData(
            transaction_type=KiteConnect.TRANSACTION_TYPE_BUY, quantity=1, price=10.0
        )
        gtt_data = GTTData(
            tradingsymbol="IDEA",
            trigger_values=[10.0],
            last_price=9.0,
            orders=[gtt_order_data],
        )
        gtt_order = trade_executor.place_gtt(gtt_data=gtt_data)
        print(f"GTT Order: {gtt_order}")
