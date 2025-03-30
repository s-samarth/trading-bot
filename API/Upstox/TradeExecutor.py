import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import requests
from pydantic import BaseModel

from API.Upstox.UpstoxLogin import Login
from API.Upstox.DataExtractor import DataExtractor
from API.Upstox.Data import Data
from API.Upstox.Constants import Exchange


class PlaceOrderData(BaseModel):
    ...

class TradeExecutor:
    def __init__(self):
        """
        Initialize the TradeExecutor class with the provided access token.
        """
        self.access_token = Login().get_access_token()
        self.data = Data(self.access_token)
        self.data_extractor = DataExtractor(self.access_token)

    def place_order(self, instrument, quantity=1):
        """Executes a trade on Upstox."""
        pass

