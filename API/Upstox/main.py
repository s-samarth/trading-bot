import os
import sys
from pprint import pprint
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import upstox_client
from upstox_client import ApiClient 
from upstox_client.rest import ApiException

from Upstox.UpstoxLogin import UpstoxLogin


if __name__ == "__main__":
    upstox_login = UpstoxLogin()

    # Login to Upstox
    configuration =upstox_login.login()
    api_instance = upstox_client.UserApi(ApiClient(configuration=configuration))
    api_version = 'api_version_example' # str | API Version Header

    try:
        # Get profile
        api_response = api_instance.get_profile(api_version)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling UserApi->get_profile: %s\n" % e)
    
    # Place an order
    api_instance = upstox_client.OrderApiV3()
    body = upstox_client.PlaceOrderV3Request(
        quantity=1,
        product="D",
        validity="DAY",
        order_type="MARKET",
        transaction_type="BUY",
        instrument_token="IDEA",
        is_amo=False,
        price=7.0,
        disclosed_quantity=0,
        trigger_price=7.0
    )

    try:
        api_response = api_instance.place_order(body)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling OrderApiV3->place_order: %s\n" % e)