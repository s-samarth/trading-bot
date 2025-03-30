import os
import sys
from typing import List
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import requests
from dotenv import load_dotenv
from pprint import pprint

from API.Upstox.UpstoxLogin import Login
from API.Upstox.DataExtractor import DataExtractor
from API.Upstox.Constants import Exchange

class Data:
    def __init__(self, access_token: str):
        """
        Initialize the Data class with the provided access token.
        """
        self.access_token = access_token

    def get_profile(self):
        """
        Get the profile information of the user."
        """
        url = 'https://api.upstox.com/v2/user/profile'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            pprint("User profile fetched successfully.")
            return response.json()
        else:
            print("Error fetching user profile:", response.json())
            return None
        
    def get_fund_and_margin(self):
        """
        Get the positions of the user.
        """
        url = "https://api.upstox.com/v2/user/get-funds-and-margin"

        params={
            'segment': 'SEC'
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        if response.status_code == 200:
            pprint("Fund and margin fetched successfully.")
            return response.json()
        else:
            print("Error fetching fund and margin:", response.json())
            return None
        
    def get_positions(self):
        """
        Get the positions of the user.
        """ 
        url = "https://api.upstox.com/v2/portfolio/short-term-positions"

        payload={}
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            pprint("Positions fetched successfully.")
            return response.json()
        else:
            print("Error fetching positions:", response.json())
            return None

    def get_holdings(self):
        """
        Get the holdings of the user.
        """
        url = "https://api.upstox.com/v2/portfolio/long-term-positions"

        payload={}
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            pprint("Holdings fetched successfully.")
            return response.json()
        else:
            print("Error fetching Holdings:", response.json())
            return None

            
    def get_ltp(self, trading_symbol: str, exchange: str):
        """
        Get the last traded price (LTP) for the given instrument.
        """
        url = "https://api.upstox.com/v2/market-quote/ltp"

        params={
            'instrument_key': self._generate_instrument(trading_symbol=trading_symbol, exchange=exchange)
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        if response.status_code == 200:
            pprint("LTP fetched successfully.")
            return response.json()
        else:
            print("Error fetching LTP:", response.json())
            return None

    def get_multiple_ltp(self, trading_symbols: List[str], exchange: List[str], max_results: int = 5):
        """
        Get the last traded price (LTP) for multiple instruments.
        """
        if len(trading_symbols) != len(exchange):
            raise ValueError("The length of trading_symbols and exchange must be the same.")
        if len(trading_symbols) > max_results:
            raise ValueError(f"The number of trading symbols per request cannot exceed {max_results}.")
        
        url = "https://api.upstox.com/v2/market-quote/ltp"

        instrument_keys = [self._generate_instrument(trading_symbol=trading_symbol, exchange=exchange) for trading_symbol, exchange in zip(trading_symbols, exchange)]
        instrument_keys_str = ','.join(instrument_keys)        

        params={
            'instrument_key': instrument_keys_str
        }
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.access_token}'
        }

        response = requests.request("GET", url, headers=headers, params=params)
        if response.status_code == 200:
            pprint("LTP fetched successfully.")
            return response.json()
        else:
            print("Error fetching LTP:", response.json())
            return None
            
    
    def _generate_instrument(self, trading_symbol: str, exchange: str):
        """
        Generate the instrument key for the given trading symbol and exchange.
        """
        if exchange == Exchange.NSE:
            extractor = DataExtractor()
            trading_instrument = extractor.get_trading_instrument_for_symbol(trading_symbol)
            if trading_instrument:
                return trading_instrument
            else:
                raise ValueError(f"Invalid trading symbol: {trading_symbol}")
                
        elif exchange == Exchange.BSE:
            # Implement BSE logic here
            return None
        



if __name__ == '__main__':
    access_token = Login().login()
    data = Data(access_token)
    profile = data.get_profile()
    print("User Profile:", profile)
    fund_and_margin = data.get_fund_and_margin()
    print("Fund and Margin:", fund_and_margin)
    positions = data.get_positions()
    print("Positions:", positions)
    holdings = data.get_holdings()
    print("Holdings:", holdings)
    ltp = data.get_ltp("RELIANCE", "NSE")
    print("LTP:", ltp)
    multiple_ltp = data.get_multiple_ltp(["RELIANCE", "TCS", "IDEA"], ["NSE", "NSE", "NSE"])
    print("Multiple LTP:", multiple_ltp)

