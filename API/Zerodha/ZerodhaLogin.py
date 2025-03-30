import os
import time
import random
import urllib.parse as urlparse
from enum import StrEnum

import pyotp
from dotenv import load_dotenv
from kiteconnect import KiteConnect
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ChromeDrivers import ChromeDrivers

class RequestTokenMode(StrEnum):
    MANUAL = "manual"
    AUTOMATED = "automated"

class Login:
    def __init__(self, request_token_mode=RequestTokenMode.AUTOMATED):
        """"
        ""Initialize the Login class with the provided request token mode."
        """
        load_dotenv()
        self.api_key = os.getenv("ZERODHA_API_KEY")
        self.user_id = os.getenv("ZERODHA_USER_ID")
        self.password = os.getenv("ZERODHA_PASSWORD")
        self.mpin = os.getenv("ZERODHA_MPIN")
        self.api_secret = os.getenv("ZERODHA_API_SECRET")
        self.totp_secret = os.getenv("ZERODHA_TOTP_SECRET")
        self.kite = KiteConnect(api_key=self.api_key) 
        self.access_token = self.get_access_token()  # Load access token from file if it exists
        self.request_token_mode = request_token_mode

    def login(self):
        if self.access_token:
            self.kite.set_access_token(self.access_token)
            try:
                self.kite.profile()
                print("Access token is valid.")
                return
            except Exception as e:
                print("Access token is invalid. Generating a new one.")
                self.kite.set_access_token(None)

        login_url = self.kite.login_url()

        if self.request_token_mode == RequestTokenMode.MANUAL:
            print("Logging in to Zerodha Manually...")
            request_token = self.manual_login(login_url=login_url)

        elif self.request_token_mode == RequestTokenMode.AUTOMATED:
            print("Logging in to Zerodha Automatatedly...")
            request_token = self.automate_login_selenium(login_url=login_url)

        else:
            print("Invalid request token mode. Please choose either 'manual' or 'automatic'.")
            request_token = None
        
        if request_token:
            self.access_token = self.generate_access_token(request_token)
            if self.access_token:
                self.save_access_token(self.access_token)
                self.kite.set_access_token(self.access_token)
                print("Access token set successfully.")
                print("Access token:", self.access_token)
                try:
                    self.kite.profile()
                    print("Profile retrieved successfully.")
                except Exception as e:  
                    print("Error retrieving profile:", str(e))
                    print("Access token may be invalid.")
                print("Access token is valid.")
            else:
                print("Failed to generate access token.")
        
        return self.kite

    def manual_login(self, login_url):
        print("Please login to Zerodha using the following URL:")
        print(login_url)

        # Extract `request_token` from the Redirect URL
        current_url = input("Enter the current URL after login: ")
        parsed = urlparse.urlparse(current_url)
        query_params = urlparse.parse_qs(parsed.query)
        request_token = query_params.get("request_token", [""])[0]

        print("Request Token:", request_token)

        return request_token

    def automate_login_selenium(self, login_url, default_wait_time=30):
        # Initialize ChromeDriver with caching
        chrome_driver_manager = ChromeDrivers()
        driver = chrome_driver_manager.get_chromedriver()

        try:
            driver.get(login_url)
            print("Navigated to Zerodha login page")
            # Wait for the page to load with human like behaviour
            wait = WebDriverWait(driver, default_wait_time)
        

            # 🟢 Enter User ID
            user_id_input = wait.until(EC.presence_of_element_located((By.ID, "userid")))
            time.sleep(random.uniform(2, 4)) 
            user_id_input.send_keys(self.user_id)
            print("User ID entered")

            # 🟢 Enter Password
            password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
            time.sleep(random.uniform(2, 4))
            password_input.send_keys(self.password)
            print("Password entered")

            # 🟢 Click on Login button
            time.sleep(random.uniform(0.5, 1.5))
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            print("Login button clicked")

            # 🟢 Enter TOTP
            wait = WebDriverWait(driver, default_wait_time)
            totp_input = wait.until(EC.presence_of_element_located((By.ID, "userid")))
            time.sleep(random.uniform(3, 5))
            totp = pyotp.TOTP(self.totp_secret).now()
            totp_input.send_keys(totp)
            print("TOTP entered")

            # 🟢 Extract `request_token` from the Redirect URL
            wait = WebDriverWait(driver, default_wait_time)
            wait.until(lambda driver: "request_token" in driver.current_url)
            current_url = driver.current_url
            time.sleep(random.uniform(2, 3))
            driver.quit()  # Close the browser
            print("Browser closed")

            # Parse the URL to extract the request token
            parsed = urlparse.urlparse(current_url)
            query_params = urlparse.parse_qs(parsed.query)
            request_token = query_params.get("request_token", [""])[0]

            if not request_token or request_token == "":
                raise ValueError("Request token is empty or invalid.")

            return request_token
        
        except Exception as e:
            print("Error during Selenium login:", str(e))
            driver.quit()
            return None

    def generate_access_token(self, request_token):
        try:
            session_data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = session_data["access_token"]
            return access_token
        except Exception as e:
            print("Error generating access token:", str(e))
            return None
        
    def save_access_token(self, access_token):
        with open("access_token.txt", "w") as file:
            file.write(access_token)
        print("Access token saved to access_token.txt")

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

if __name__ == "__main__":
    login = Login()
    kite = login.login() 
    print("Login successful.")