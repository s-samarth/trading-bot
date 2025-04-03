import os
import sys
import json
from typing import Optional, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import requests
from pydantic import BaseModel

from API.Upstox.UpstoxLogin import Login, SandboxLogin
from API.Upstox.DataExtractor import DataExtractor
from API.Upstox.Constants import (
    Exchange,
    Validity,
    TransactionType,
    ProductType,
    OrderType,
    Segment,
)
from API.Upstox.DataExtractor import generate_instrument_token


class PlaceOrderData(BaseModel):
    """
    Data model for placing an order.
    """

    trading_symbol: str
    quantity: int = 1
    transaction_type: TransactionType = TransactionType.BUY
    product_type: ProductType = ProductType.DELIVERY
    exchange: Exchange = Exchange.NSE
    order_type: OrderType = OrderType.LIMIT
    validity: Validity = Validity.DAY
    price: float = (
        0  # The price at which the order is to be executed. For market orders, this is ignored.
    )
    tag: Optional[str] = None
    disclosed_quantity: int = (
        0  # The portion of the total order quantity that is visible to the market at any given time. Used by big traders to hide their order size and avoid market impact.
    )
    trigger_price: float = (
        0  # The price at which the order is triggered. This is used for stop-loss orders. For market orders, this is ignored.
    )
    is_amo: bool = (
        False  # After market order. If True, the order will be placed after the market closes and will be valid for the next trading day.
    )


class ModifyOrderData(BaseModel):
    """
    Data model for modifying an order.
    """

    order_id: str  # The order ID of the order to be modified.
    quantity: Optional[int] = (
        None  # The quantity of the order. If not provided, the order will be modified with the same quantity.
    )
    price: float = 0  # The price at which the order was placed
    validity: Validity = (
        Validity.DAY
    )  # The validity of the order. If not provided, the order will be valid for the day.
    order_type: OrderType = (
        OrderType.MARKET
    )  # The type of order. If not provided, the order will be a market order.
    disclosed_quantity: Optional[int] = (
        None  # If provided, this value must be non-zero.
    )
    trigger_price: float = (
        0  # If the order is a stop loss order then the trigger price to be set is mentioned here
    )


class TradeExecutor:
    def __init__(self, access_token: str, sandbox_mode: bool = True):
        """
        Initialize the TradeExecutor class with the provided access token.
        """
        if access_token:
            self.access_token = access_token
        else:
            try:
                self.access_token = Login().login()
            except Exception as e:
                raise RuntimeError(
                    "Failed to retrieve access token from Upstox. "
                ) from e
        self.live_url = "https://api-hft.upstox.com/v2"
        if sandbox_mode:
            self.live_url = "https://api-sandbox.upstox.com/v2"

    def validate_response(self, response, endpoint):
        """
        Check the response from the API.
        """
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 207:
            print(
                f"Partial success for endpoint: {endpoint}, Response: {response.json()}\n"
            )
            return response.json()
        else:
            print(
                f"Error accessing endpoint: {endpoint}, Status code: {response.status_code}, Response: {response.json()}\n"
            )
            return None

    def drop_keys_with_none_values(self, data):
        """
        Drop keys with None values from the dictionary.
        """
        return {k: v for k, v in data.items() if v is not None}


class OrderAPI(TradeExecutor):
    """
    Class to handle placing orders using the Upstox API.
    """

    def __init__(self, access_token: str = None, sandbox_mode: bool = True):
        """
        Initialize the PlaceOrderAPI class with the provided access token.
        """
        super().__init__(access_token, sandbox_mode)

    def place_order(self, order_data: PlaceOrderData):
        """
        Place an order using the Upstox API.
        Limitations: Places only 1 order in a single request.
        Uses POST method for placing orders.
        """
        endpoint = "order/place"
        url = f"{self.live_url}/{endpoint}"
        instrument_token = generate_instrument_token(
            order_data.trading_symbol, order_data.exchange
        )
        data = {
            "instrument_token": instrument_token,
            "quantity": order_data.quantity,
            "transaction_type": order_data.transaction_type,
            "product": order_data.product_type,
            "order_type": order_data.order_type,
            "validity": order_data.validity,
            "price": order_data.price,
            "tag": order_data.tag,
            "disclosed_quantity": order_data.disclosed_quantity,
            "trigger_price": order_data.trigger_price,
            "is_amo": order_data.is_amo,
        }
        data = self.drop_keys_with_none_values(data)
        payload = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        response = requests.post(url, headers=headers, data=payload)
        return self.validate_response(response, endpoint)

    def place_multi_order(self, orders_data: List[PlaceOrderData], slice: bool = False):
        """
        Place multiple orders using the Upstox API.
        Limitations: Places only 25 orders in a single request.
        Uses POST method for placing orders.
        """
        if len(orders_data) > 25:
            raise ValueError("Cannot place more than 25 orders in a single request.")

        endpoint = "order/multi/place"
        url = f"{self.live_url}/{endpoint}"
        orders = []
        for i, order_data in enumerate(orders_data):
            instrument_token = generate_instrument_token(
                order_data.trading_symbol, order_data.exchange
            )
            data = {
                "correlation_id": f"{i}",
                "instrument_token": instrument_token,
                "quantity": order_data.quantity,
                "transaction_type": order_data.transaction_type,
                "product": order_data.product_type,
                "order_type": order_data.order_type,
                "validity": order_data.validity,
                "price": order_data.price,
                "tag": order_data.tag,
                "disclosed_quantity": order_data.disclosed_quantity,
                "trigger_price": order_data.trigger_price,
                "is_amo": order_data.is_amo,
                "slice": slice,
            }
            data = self.drop_keys_with_none_values(data)
            orders.append(data)
        payload = json.dumps(orders)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        response = requests.post(url, headers=headers, data=payload)
        return self.validate_response(response, endpoint)

    def modify_order(self, order_data: ModifyOrderData):
        """
        Modify an open or pending order using the Upstox API."
        Uses PUT method for modifying orders.
        """
        endpoint = f"order/modify"
        url = f"{self.live_url}/{endpoint}"
        data = {
            "order_id": order_data.order_id,
            "quantity": order_data.quantity,
            "validity": order_data.validity,
            "price": order_data.price,
            "order_type": order_data.order_type,
            "disclosed_quantity": order_data.disclosed_quantity,
            "trigger_price": order_data.trigger_price,
        }
        data = self.drop_keys_with_none_values(data)
        payload = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        response = requests.put(url, headers=headers, data=payload)
        return self.validate_response(response, endpoint)

    def cancel_order(self, order_id: str):
        """
        Cancel an open or pending order using the Upstox API.
        Can Be applied to AMO orders as well.
        It may also serve to exit a Cover Order (CO)
        Uses DELETE method for cancelling orders.
        """
        endpoint = f"order/cancel"
        url = f"{self.live_url}/{endpoint}?order_id={order_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        response = requests.delete(url, headers=headers)
        return self.validate_response(response, endpoint)

    def cancel_multi_order(
        self,
        exchange: Optional[Exchange] = None,
        segment: Optional[Segment] = None,
        tag: Optional[str] = None,
    ):
        """
        Use this API to cancel all open orders in one go.
        You can filter by segment or tag to cancel specific orders,
        or cancel all open orders with a single request.
        This applies to both AMO and regular orders.
        The order_ids of the cancelled orders will be returned in the response.
        Status Code: 207 indicates partial success. Ie. some orders were cancelled and some were not.
        Limitations: Places only 200 orders in a single request.
        Uses DELETE method for cancelling orders.
        """
        endpoint = f"order/multi/cancel"
        url = f"{self.live_url}/{endpoint}"

        if tag is not None and exchange is not None:
            raise ValueError("Tag and exchange cannot be provided at the same time.")

        if tag is not None:
            url += f"?tag={tag}"

        if exchange is not None and segment is not None:
            segment = exchange + "_" + segment
            url += f"?segment={segment}"
        elif exchange is not None and segment is None:
            raise ValueError("Segment cannot be None if exchange is provided.")
        elif exchange is None and segment is not None:
            raise ValueError("Exchange cannot be None if segment is provided.")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        response = requests.delete(url, headers=headers)
        return self.validate_response(response, endpoint)


class TradeExecutorV3:
    def __init__(self, access_token: str, sandbox_mode: bool = True):
        """
        Initialize the TradeExecutorV3 class with the provided access token.
        """
        if access_token:
            self.access_token = access_token
        else:
            try:
                self.access_token = Login().login()
            except Exception as e:
                raise RuntimeError(
                    "Failed to retrieve access token from Upstox. "
                ) from e
        self.live_url = "https://api-hft.upstox.com/v3"
        if sandbox_mode:
            self.live_url = "https://api-sandbox.upstox.com/v3"

    def validate_response(self, response, endpoint):
        """
        Check the response from the API.
        """
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Error accessing endpoint: {endpoint}, Response: {response.json()}\n"
            )
            return None

    def drop_keys_with_none_values(self, data):
        """
        Drop keys with None values from the dictionary.
        """
        return {k: v for k, v in data.items() if v is not None}


class OrderAPIv3(TradeExecutorV3):
    """
    Class to handle placing orders using the Upstox API V3.
    """

    def __init__(self, access_token: str = None, sandbox_mode: bool = True):
        """
        Initialize the PlaceOrderAPI class with the provided access token.
        """
        super().__init__(access_token, sandbox_mode)

    def place_order(self, order_data: PlaceOrderData, slice: bool = False):
        """
        Place an order using the Upstox API.
        Pros:
        - Features an auto slicing capability to split larger orders into smaller ones
        based on the freeze quantity. You can enable or disable this feature using the slice parameter.
        Limitations:
        - Places only 25 orders in a single request.
        - When slicing is applicable, Brokerage will be charged for each individual sliced order.
        - Currently product type OCO is not supported.
        Uses POST method for placing orders.
        """
        endpoint = "order/place"
        url = f"{self.live_url}/{endpoint}"
        instrument_token = generate_instrument_token(
            order_data.trading_symbol, order_data.exchange
        )
        data = {
            "instrument_token": instrument_token,
            "quantity": order_data.quantity,
            "transaction_type": order_data.transaction_type,
            "product": order_data.product_type,
            "order_type": order_data.order_type,
            "validity": order_data.validity,
            "price": order_data.price,
            "tag": order_data.tag,
            "disclosed_quantity": order_data.disclosed_quantity,
            "trigger_price": order_data.trigger_price,
            "is_amo": order_data.is_amo,
            "slice": slice,
        }
        data = self.drop_keys_with_none_values(data)
        payload = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        response = requests.post(url, headers=headers, data=payload)
        return self.validate_response(response, endpoint)

    def modify_order(self, order_data: ModifyOrderData):
        """
        This is an enhanced version of the Modify Order API which includes
        latency information in the meta object of the response,
        providing insight into the time Upstox took to process your request.
        Uses PUT method for modifying orders.
        """
        endpoint = f"order/modify"
        url = f"{self.live_url}/{endpoint}"
        data = {
            "order_id": order_data.order_id,
            "quantity": order_data.quantity,
            "validity": order_data.validity,
            "price": order_data.price,
            "order_type": order_data.order_type,
            "disclosed_quantity": order_data.disclosed_quantity,
            "trigger_price": order_data.trigger_price,
        }
        data = self.drop_keys_with_none_values(data)
        payload = json.dumps(data)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        response = requests.put(url, headers=headers, data=payload)
        return self.validate_response(response, endpoint)

    def cancel_order(self, order_id: str):
        """
        This is an enhanced version of the Cancel Order API which includes
        latency information in the meta object of the response,
        providing insight into the time Upstox took to process your request.
        Uses DELETE method for cancelling orders.
        """
        endpoint = f"order/cancel"
        url = f"{self.live_url}/{endpoint}?order_id={order_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        response = requests.delete(url, headers=headers)
        return self.validate_response(response, endpoint)


if __name__ == "__main__":
    # access_token = Login().login()
    access_token = SandboxLogin().login()
    trade_executor = TradeExecutor(access_token=access_token)

    # Example usage of OrderAPI
    print("Place Order Class Usage:\n")
    order_api = OrderAPI(access_token=access_token)
    order_data = PlaceOrderData(trading_symbol="RELIANCE", quantity=1)
    place_order_response = order_api.place_order(order_data)
    print(f"Place Order Response: {place_order_response}\n")
    orders_data = [
        PlaceOrderData(trading_symbol="RELIANCE", quantity=1),
        PlaceOrderData(trading_symbol="TCS", quantity=2),
    ]
    place_multi_order_response = order_api.place_multi_order(orders_data, slice=True)
    print(f"Place Multi Order Response: {place_multi_order_response}\n")

    modify_order_data = ModifyOrderData(
        order_id=place_order_response["data"]["order_id"]
    )
    modify_order_response = order_api.modify_order(order_data=modify_order_data)
    print(f"Modify Order Response: {modify_order_response}\n")

    cancel_order_response = order_api.cancel_order(
        order_id=place_order_response["data"]["order_id"]
    )
    print(f"Cancel Order Response: {cancel_order_response}\n")

    cancel_multi_order_response = order_api.cancel_multi_order(
        exchange=Exchange.NSE, segment=Segment.EQUITY
    )
    print(f"Cancel Multi Order Response: {cancel_multi_order_response}\n")
    print("=========================================================\n\n")

    # Example usage of OrderAPIv3
    print("Place Order Class Usage:\n")
    order_api_v3 = OrderAPIv3(access_token=access_token)
    order_data = PlaceOrderData(trading_symbol="RELIANCE", quantity=1)
    place_order_response = order_api_v3.place_order(order_data)
    print(f"Place Order Response: {place_order_response}\n")

    modify_order_data = ModifyOrderData(
        order_id=place_order_response["data"]["order_ids"][0]
    )
    modify_order_response = order_api_v3.modify_order(order_data=modify_order_data)
    print(f"Modify Order Response: {modify_order_response}\n")

    cancel_order_response = order_api_v3.cancel_order(
        order_id=place_order_response["data"]["order_ids"][0]
    )
    print(f"Cancel Order Response: {cancel_order_response}\n")
