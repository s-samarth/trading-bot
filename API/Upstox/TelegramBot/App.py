import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from TelegramBot.Commands import Commands
from TelegramBot.MessageHandling import MessageHandling
from TelegramBot.ErrorHandling import ErrorHandling

class App:
    def __init__(self):
        pass

    def run(self):
        load_dotenv()
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        print("Bot is starting...")
        app = Application.builder().token(bot_token).build()

        # Command Handlers
        commands = Commands()
        app.add_handler(CommandHandler("start", commands.start))
        app.add_handler(CommandHandler("help", commands.help))
        app.add_handler(CommandHandler("balance", commands.balance))
        app.add_handler(CommandHandler("positions", commands.positions))
        app.add_handler(CommandHandler("orders", commands.orders))
        app.add_handler(CommandHandler("login", commands.login))

        # Message Handler
        message_handling = MessageHandling()
        app.add_handler(MessageHandler(filters.TEXT, message_handling.handle_message))

        # Error Handler
        error_handling = ErrorHandling()
        app.add_error_handler(error_handling.handle_error)

        # Polling
        print("Bot is running...")
        app.run_polling(poll_interval=5)

if __name__ == "__main__":
    app = App()
    app.run()