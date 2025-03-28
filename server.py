from flask import Flask, request
import requests
import os
from dotenv import load_dotenv

from UpstoxLogin import UpstoxLogin, EnvironmentVariables

# Load API Keys
load_dotenv()
UPSTOX_API_KEY = os.getenv("API_KEY")
UPSTOX_API_SECRET = os.getenv("API_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

app = Flask(__name__)

@app.route('/callback', methods=['GET'])
def receive_auth_code():
    auth_code = request.args.get('code')
    if not auth_code:
        return "❌ No auth code received", 400

    # Exchange auth code for access token
    env = EnvironmentVariables()
    env.write_env_variable("AUTH_CODE", auth_code)
    upstox_login = UpstoxLogin()
    _ , response = upstox_login.generate_access_token()
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")

        # Save token to a file
        with open("access_token.txt", "w") as file:
            file.write(access_token)

        # Send token to Telegram
        message = f"🚀 Access Token: `{access_token}`\n"
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

        return "✅ Access Token Received & Sent to Telegram!", 200
    else:
        return f"❌ Failed to exchange auth code for token", 500

if __name__ == '__main__':
    app.run(port=8000)