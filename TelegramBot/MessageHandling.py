import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

from TelegramBot.ResponseHandling import ResponseHandling


class MessageHandling:
    def __init__(self):
        pass

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_tyoe: str = update.message.chat.type
        text: str = update.message.text
        load_dotenv()
        bot_username = os.getenv("BOT_USERNAME")

        print(f"User: {update.message.chat.id} in ({message_tyoe}): {text}")

        if message_tyoe == 'group':
            if bot_username in text:
                new_text = text.replace(bot_username, "").strip()
                response: str = ResponseHandling.handle_response(new_text)
            else:
                return
        else:
            response: str = ResponseHandling.handle_response(text)

        print(f"Bot: {response}")
        await update.message.reply_text(response)