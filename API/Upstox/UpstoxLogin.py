import os
import json
import webbrowser
from typing import final

import requests
import urllib.parse
from dotenv import load_dotenv
import upstox_client


class EnvironmentVariables:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("UPSTOX_API_KEY")
        self.api_secret = os.getenv("UPSTOX_API_SECRET")
        self.sandbox_access_token = os.getenv("UPSTOX_SANDBOX_ACCESS_TOKEN")
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI")
        if os.getenv("UPSTOX_AUTH_CODE"):
            self.auth_code = os.getenv("UPSTOX_AUTH_CODE")
        else:
            self.auth_code = None

    def write_env_variable(self, key, value, env_file=".env"):
        """Writes or updates a key-value pair in the .env file."""
        lines = []
        updated = False

        # Read existing .env file if it exists
        try:
            with open(env_file, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass  # File doesn't exist yet

        # Update the existing key if found, otherwise add a new one
        with open(env_file, "w") as f:
            for line in lines:
                if line.startswith(f"{key}="):  # Update the existing key
                    f.write(f"{key}={value}\n")
                    updated = True
                else:
                    f.write(line)

            if not updated:  # Add new key if it doesn't exist
                f.write(f"{key}={value}\n")



class UpstoxLogin:
    def __init__(self):
        self.env = EnvironmentVariables()
        self.api_key = self.env.api_key
        self.api_secret = self.env.api_secret
        self.base_auth_url = "https://api.upstox.com/v2/login/authorization/dialog"
        self.redirect_uri = self.env.redirect_uri
        self.response_type = "code"
        # self.scope = "profile,trade,offline_access"
        self.auth_code = self.env.auth_code

    def login(self) -> upstox_client.Configuration:
        if os.path.exists("access_token.txt"):
            access_token = self.get_access_token()
        else:
            access_token, _ = self.generate_access_token()

        configuration = upstox_client.Configuration()
        try:
            configuration.access_token = access_token
        except Exception as e:
            print("Error:", e)
            access_token, _ = self.generate_access_token()
            configuration.access_token = access_token
        
        print("✅ Logged in successfully!")
        return configuration
    
    @final
    def update_auth_code(self):
        # Open the browser to get the auth code, @final decorator ensures that this method cannot be overridden
        encoded_redirect_uri = urllib.parse.quote(self.redirect_uri, safe="")
        self.auth_url = f"{self.base_auth_url}?response_type={self.response_type}&client_id={self.api_key}&redirect_uri={encoded_redirect_uri}"

        webbrowser.open(self.auth_url)
        self.auth_code = input("Enter the auth code: ")
        self.auth_code = self.auth_code.strip()
        self.env.write_env_variable("UPSTOX_AUTH_CODE", self.auth_code, env_file="../../.env")

    def generate_access_token(self):
        self.update_auth_code()
        self.token_url = "https://api.upstox.com/v2/login/authorization/token"
        payload = {
            "grant_type": "authorization_code",
            "code": self.auth_code,
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
        
        return access_token, response
    
    def save_access_token(self, access_token: str):
        with open("../access_token.txt", "w") as file:
            file.write(access_token)
        print("Access token saved successfully")

    def get_access_token(self):
        with open("../access_token.txt", "r") as file:
            return file.read()
        
    def check_if_trading_session_active(self, access_token: str):
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get("https://api.upstox.com/v2/order/trades", headers=headers)
        if response.status_code == 200:
            print("✅ Trading session is active!")
            return True
        else:
            print("⚠️ Trading session is not active! Please activate it manually.")
            return False
        
        

if __name__ == "__main__":
    upstox_login = UpstoxLogin()
    access_token, response = upstox_login.generate_access_token()
    is_session_active = upstox_login.check_if_trading_session_active(access_token)
    # configuration = Configuration()
    # configuration.access_token = access_token
    # api_client = ApiClient(configuration)


    
    