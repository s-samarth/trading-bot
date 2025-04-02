import os
import json

import pyotp
from dotenv import load_dotenv
from SmartApi import SmartConnect


class TradingLogin:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("ANGELONE_TRADING_API_KEY")
        self.client_id = os.getenv("ANGELONE_CLIENT_ID")
        self.password = os.getenv("ANGELONE_PASSWORD")
        self.totp_secret = os.getenv("ANGELONE_TOTP_SECRET")  # Store this securely

    def generate_totp(self):
        totp = pyotp.TOTP(self.totp_secret).now()
        return totp

    def generate_tokens(self):
        # Generate TOTP
        totp = self.generate_totp()
        print(f"Generated TOTP: {totp}")

        # Initialize SmartConnect
        smart_api = SmartConnect(self.api_key)
        login_response = smart_api.generateSession(self.client_id, self.password, totp)

        # Store Access Token and Refresh Token for later use
        access_token = login_response["data"]["jwtToken"]
        refresh_token = login_response["data"]["refreshToken"]

        return access_token, refresh_token

    def save_tokens(self, access_token, refresh_token):
        # Save tokens securely
        with open("tokens.json", "w") as f:
            json.dump({"access_token": access_token, "refresh_token": refresh_token}, f)
        print("Tokens saved successfully! Use them for API requests.")

    def get_tokens(self):
        # Load tokens from file
        if os.path.exists("tokens.json"):
            with open("tokens.json", "r") as f:
                tokens = json.load(f)
                try:
                    self.access_token = tokens["access_token"]
                    self.refresh_token = tokens["refresh_token"]
                except Exception as e:
                    print("Error loading tokens:", e)
                    self.access_token, self.refresh_token = self.generate_tokens()
                    self.save_tokens(self.access_token, self.refresh_token)
        else:
            self.access_token, self.refresh_token = self.generate_tokens()
            self.save_tokens(self.access_token, self.refresh_token)

    def login(self):
        smart_api = SmartConnect(api_key=self.api_key)
        # Load tokens
        self.get_tokens()
        session_data = smart_api.generateToken(self.refresh_token)
        self.access_token = session_data["data"]["jwtToken"]
        print("Logged in successfully!")
        # Save tokens securely
        self.save_tokens(self.access_token, self.refresh_token)
        return self.access_token


if __name__ == "__main__":
    trading_login = TradingLogin()
    totp = trading_login.generate_totp()
    print(f"Generated TOTP: {totp}")
