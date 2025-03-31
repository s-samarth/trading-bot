import os
import sys
import time
import json
import random
import webbrowser
from enum import StrEnum
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import requests
import pyotp
import urllib.parse as urlparse
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ChromeDrivers.ChromeDrivers import ChromeDrivers


class LoginMode(StrEnum):
    MANUAL = "manual"
    AUTOMATED = "automated"


class Login:
    def __init__(self, login_mode=LoginMode.AUTOMATED):
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv("UPSTOX_API_KEY")
        self.api_secret = os.getenv("UPSTOX_API_SECRET")
        self.base_auth_url = "https://api.upstox.com/v2/login/authorization/dialog"
        self.response_type = "code"
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI")
        self.encoded_redirect_uri = urlparse.quote(self.redirect_uri, safe="")
        self.login_url = f"{self.base_auth_url}?response_type={self.response_type}&client_id={self.api_key}&redirect_uri={self.encoded_redirect_uri}"
        self.api_version = os.getenv("UPSTOX_API_VERSION")
        
        self.login_mode = login_mode
        if self.login_mode == LoginMode.AUTOMATED:
            self.mobile_number = os.getenv("UPSTOX_MOBILE_NUMBER")
            self.totp_secret = os.getenv("UPSTOX_TOTP_SECRET")
            self.mpin = os.getenv("UPSTOX_MPIN")
        self.access_token = self.get_access_token()  # Load access token from file if it exists

    def login(self) -> str:
        if self.access_token:
            user_profile = self._get_user_profile()
            if user_profile:
                print("Access token is valid.")
                return self.access_token
            else:
                print("Access token is invalid. Generating a new one.")
                self.access_token = None

        if self.login_mode == LoginMode.MANUAL:
            self.access_token = self.manual_login()
        elif self.login_mode == LoginMode.AUTOMATED:
            self.access_token = self.automate_login_selenium()
        else:   
            print("Invalid login mode. Please choose either 'manual' or 'automated'.")
            return None

        user_profile = self._get_user_profile()
        if user_profile:
            print("Logged in successfully!")
        else:
            print("Failed to set access token.")
            print("Please login again.")
        return self.access_token
    
    def manual_login(self):
        print("Logging in to Upstox Manually...")
        # Generate access token using the auth code
        auth_code = self.get_auth_code_manually()
        access_token = self.generate_access_token(auth_code=auth_code)
        return access_token
    
    def automate_login_selenium(self, default_wait_time=30):
        """
        Automate the login process using Selenium WebDriver.
        """
        print("Logging in to Upstox Automatically...")
        # Initialize ChromeDriver with caching
        chrome_driver_manager = ChromeDrivers()
        driver = chrome_driver_manager.get_chromedriver()

        try:
            driver.get(self.login_url)
            print("Navigated to Upstox login page")
            # Wait for the page to load with human like behaviour
            wait = WebDriverWait(driver, default_wait_time)
        

            # 🟢 Enter Mobile Number
            mobile_number_input = wait.until(EC.presence_of_element_located((By.ID, "mobileNum")))
            time.sleep(random.uniform(2, 4)) 
            mobile_number_input.send_keys(self.mobile_number)
            print("Mobile Number entered")

            # 🟢 Click on Get OTP button
            time.sleep(random.uniform(0.5, 1.5))
            driver.find_element(By.ID, "getOtp").click()
            print("Get OTP button clicked")

            
            # 🟢 Enter TOTP
            wait = WebDriverWait(driver, default_wait_time)
            totp_input = wait.until(EC.presence_of_element_located((By.ID, "otpNum")))
            totp_input.click()
            time.sleep(random.uniform(3, 5))
            totp = pyotp.TOTP(self.totp_secret).now()
            totp_input.send_keys(totp)
            print("TOTP entered")

            # 🟢 Click on Login button
            time.sleep(random.uniform(0.5, 1.5))
            driver.find_element(By.ID, "continueBtn").click()
            print("Login button clicked")

            # 🟢 Enter MPIN
            wait = WebDriverWait(driver, default_wait_time)
            mpin_input = wait.until(EC.presence_of_element_located((By.ID, "pinCode")))
            time.sleep(random.uniform(2, 3))
            mpin_input.send_keys(self.mpin)
            print("MPIN entered")

            # 🟢 Click on Login button
            time.sleep(random.uniform(0.5, 1.5))
            driver.find_element(By.ID, "pinContinueBtn").click()
            print("Login button clicked")

            # 🟢 Extract auth_code from the Redirect URL
            wait = WebDriverWait(driver, default_wait_time)
            wait.until(lambda driver: "code" in driver.current_url)
            current_url = driver.current_url
            time.sleep(random.uniform(2, 3))
            driver.quit()  # Close the browser
            print("Browser closed")

            # Parse the URL to extract the request token
            parsed = urlparse.urlparse(current_url)
            query_params = urlparse.parse_qs(parsed.query)
            auth_code = query_params.get("code", [""])[0].strip()
            if not auth_code or auth_code == "":
                raise ValueError("Auth Code is empty or invalid.")

            access_token = self.generate_access_token(auth_code=auth_code)
            if not access_token or access_token == "":
                raise ValueError("Access token is empty or invalid.")
            return access_token
    
        except Exception as e:
            print("Error during Automated Selenium login:", str(e))
            driver.quit()
            return None

    def get_auth_code_manually(self):
        # Open the browser to get the auth code, @final decorator ensures that this method cannot be overridden
        print("Please login to Upstox using the following URL:")
        print(self.login_url)
        webbrowser.open(self.login_url)
        auth_url = input("Enter the auth url: ")
        parsed = urlparse.urlparse(auth_url)
        query_params = urlparse.parse_qs(parsed.query)
        auth_code = query_params.get("code", [""])[0].strip()
        if not auth_code or auth_code == "":
            raise ValueError("Auth Code is empty or invalid.")
        return auth_code

    def generate_access_token(self, auth_code: str = None):
        self.token_url = "https://api.upstox.com/v2/login/authorization/token"
        payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "redirect_uri": self.redirect_uri
        }
        response = requests.post(self.token_url, data=payload)
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            self.save_access_token(access_token)
        else:
            print("Error:", response.json())
            access_token = None
        
        return access_token
    
    def save_access_token(self, access_token: str):
        with open("access_token.txt", "w") as file:
            file.write(access_token)
        print("Access token saved successfully")

    def get_access_token(self):
        try:
            with open("access_token.txt", "r") as file:
                access_token = file.read().strip()
            print("Access token retrieved from file.")
            return access_token
        except FileNotFoundError:
            print("Access token file not found. Please login again.")
            return None
        except Exception as e:
            print(f"Error retrieving access token: {str(e)}")
            return None
        
    def logout(self, access_token: str):
        url = 'https://api.upstox.com/v2/logout'
        headers = headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            print("Logged out successfully.")
            return True
        else:
            print("Error logging out:", response.json())
            return False
        
    def _get_user_profile(self):
        url = 'https://api.upstox.com/v2/user/profile'
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None
            

class SandboxLogin:
    def __init__(self):
        self.sandbox_access_token_file_path = "sandbox_access_token.txt"

    def login(self):
        sandbox_access_token = self.get_sandbox_access_token()
        order = self._place_order(sandbox_access_token)
        if order:
            return sandbox_access_token
        else:
            raise PermissionError("Sandbox Token Expired, Regenerate and try again.")
            
    def get_sandbox_access_token(self):
        try:
            with open(self.sandbox_access_token_file_path, "r") as file:
                sandbox_access_token = file.read().strip()
            print("Sandbox Access token retrieved from file.")
            return sandbox_access_token
        except FileNotFoundError:
            print("Sandbox Access token file not found. Please login again.")
            return None
        except Exception as e:
            print(f"Error retrieving sandbox access token: {str(e)}")
            return None
        
    def _place_order(self, sandbox_access_token: str):
        url = "https://api-sandbox.upstox.com/v2/order/place"

        payload = json.dumps({
        "quantity": 1,
        "product": "D",
        "validity": "DAY",
        "price": 0,
        "tag": "string",
        "instrument_token": "NSE_EQ|INE848E01016",
        "order_type": "MARKET",
        "transaction_type": "BUY",
        "disclosed_quantity": 0,
        "trigger_price": 0,
        "is_amo": False
        })
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {sandbox_access_token}',
        'Accept': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.json() if response.status_code == 200 else None


if __name__ == "__main__":
    upstox_login = Login()
    access_token = upstox_login.login()
    # upstox_login.logout(access_token)

    sandbox_login = SandboxLogin()
    sandbox_access_token = sandbox_login.login()

    
    