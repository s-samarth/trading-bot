import os

import requests
from dotenv import load_dotenv
import telebot

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(bot_token)

def get_telegram_alerts(message: str = ""):
    """
    Send alerts to my Telegram
    :param message: Message to send
    """
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")   
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

    print("✅ Alert sent to Telegram")

# Function to handle incoming messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    print(f"Received from Telegram: {text}")

    # Example: Responding to the user
    if text.lower() == "status":
        bot.send_message(chat_id, "Your trading bot is running ✅")
    elif text.lower() == "balance":
        bot.send_message(chat_id, "Fetching balance... (Example: ₹50,000)")
    else:
        bot.send_message(chat_id, "Command not recognized 🚀")


if __name__ == "__main__":
    get_telegram_alerts("LessssGo The telegram alert is working")