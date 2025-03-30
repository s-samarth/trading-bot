import os
import sys

import urllib.parse
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext


class Commands:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("UPSTOX_API_KEY")
        self.base_auth_url = "https://api.upstox.com/v2/login/authorization/dialog"
        self.redirect_uri = os.getenv("UPSTOX_REDIRECT_URI")

    async def start(self, update: Update, context: ContextTypes):
        await update.message.reply_text("Hello! I am a bot to help you with your trading. How can I help you today?")

    async def help(self, update: Update, context: ContextTypes):
        await update.message.reply_text("I can help you with your trading. Here are some commands you can use:\n\n"
                                        "/start - Start the bot\n"
                                        "/help - Get help\n"
                                        "/balance - Get your account balance\n"
                                        "/positions - Get your open positions\n"
                                        "/orders - Get your open orders\n")
        
    async def balance(self, update: Update, context: ContextTypes):
        await update.message.reply_text("Fetching balance... (Example: ₹50,000)")

    async def positions(self, update: Update, context: ContextTypes):
        await update.message.reply_text("Fetching positions...")

    async def orders(self, update: Update, context: ContextTypes):
        await update.message.reply_text("Fetching orders...")

    async def login(self, update: Update, context: CallbackContext):
        encoded_redirect_uri = urllib.parse.quote(self.redirect_uri, safe="")
        # Construct Auth URL
        auth_url = f"{self.base_auth_url}?response_type=code&client_id={self.api_key}&redirect_uri={encoded_redirect_uri}"        
        await update.message.reply_text(f"Please login to your account by clicking on the link below:\n{auth_url}")
