import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import requests
from dotenv import load_dotenv
from pprint import pprint
from kiteconnect import KiteConnect

from API.Zerodha.ZerodhaLogin import Login


class Data:
    def __init__(self, kite: KiteConnect):
        """
        Initialize the Data class with the provided KiteConnect instance.
        """
        self.kite = kite

    def get_profile(self):
        """
        Get the profile information of the user.
        """
        try:
            profile = self.kite.profile()
            return profile
        except Exception as e:
            print(f"Error fetching profile: {e}")
            return None

    def get_positions(self):
        """
        Get the positions of the user.
        """
        try:
            positions = self.kite.positions()
            return positions
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return None

    def get_holdings(self):
        """
        Get the holdings of the user.
        """
        try:
            holdings = self.kite.holdings()
            return holdings
        except Exception as e:
            print(f"Error fetching holdings: {e}")
            return None

    def get_gtts(self):
        """
        Get all GTTS (Good Till Triggered) orders.
        """
        try:
            gtts = self.kite.get_gtts()
            pprint(f"GTTS orders: {gtts}")
            return gtts
        except Exception as e:
            print(f"Error fetching GTTS orders: {e}")
            return None

    def _generate_instrument(self, tradingsymbol: str, exchange: str):
        """
        Generate the instrument token for the given trading symbol and exchange.
        """
        return f"{exchange}:{tradingsymbol}"

    def get_ltp(self, instrument: str, exchange: str):
        """
        Get the last traded price (LTP) for the given instrument.
        """
        try:
            instrument_token = self._generate_instrument(
                tradingsymbol=instrument, exchange=exchange
            )
            ltp = self.kite.ltp([instrument_token])
            return ltp
        except Exception as e:
            print(f"Error fetching LTP: {e}")
            return None

    def get_nse_ltp(self, symbol: str):
        """
        Fetches the latest LTP (Last Traded Price) of a stock from NSE.
        """
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol.upper()}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={symbol.upper()}",
            "Connection": "keep-alive",
            "DNT": "1",
        }

        # Create a session
        session = requests.Session()
        session.headers.update(headers)

        try:
            # 🔹 Step 1: Visit NSE homepage to set cookies
            session.get("https://www.nseindia.com", timeout=5)

            # 🔹 Step 2: Fetch stock data
            response = session.get(url, timeout=5)
            response.raise_for_status()  # Raises an error for bad response

            # 🔹 Step 3: Extract LTP
            data = response.json()
            ltp = data["priceInfo"]["lastPrice"]

            return float(ltp)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching LTP: {e}")
            return None


if __name__ == "__main__":
    # Example usage
    load_dotenv()
    kite = KiteConnect(api_key=os.getenv("ZERODHA_API_KEY"))
    zerodha_login = Login(kite=kite)
    # Login to Zerodha
    kite = zerodha_login.login()
    if kite is not None:
        data = Data(kite=kite)

        profile = data.get_profile()
        pprint(f"Profile: {profile}")

        positions = data.get_positions()
        pprint(f"Positions: {positions}")

        holdings = data.get_holdings()
        pprint(f"Holdings: {holdings}")

        gtts = data.get_gtts()
        pprint(f"GTTS: {gtts}")

        nse_ltp = data.get_nse_ltp("RELIANCE")
        pprint(f"LTP: {nse_ltp}")
