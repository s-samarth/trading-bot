import os
import sys
from pprint import pprint
# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv
from kiteconnect import KiteConnect

from API.Zerodha.ZerodhaLogin import Login
from API.Zerodha.Data import Data
from API.Zerodha.TradeExecutor import TradeExecutor, PlaceOrderData


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    # Initialize the login class
    kite = KiteConnect(api_key=os.getenv("ZERODHA_API_KEY"))
    zerodha_login = Login(kite=kite)

    # Login to Zerodha
    kite = zerodha_login.login()
    if kite is not None:
        print("Logged in successfully.")
    else:
        print("Failed to log in.")

    # Get profile
    data = Data(kite=kite)
    profile = data.get_profile()
    pprint(f"Profile: \n{profile}")

    # Buying and selling stocks
    trade_executor = TradeExecutor(kite=kite)
    place_order_data = PlaceOrderData(tradingsymbol="IDEA", transaction_type="BUY", quantity=1)
    buy_order = trade_executor.place_order(order_params=place_order_data)
    print(f"Buy Order: {buy_order}")


    