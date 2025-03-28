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
        bot_token = os.getenv("BOT_TOKEN")
        print("Bot is starting...")
        app = Application.builder().token(bot_token).build()

        # Command Handlers
        app.add_handler(CommandHandler("start", Commands.start))
        app.add_handler(CommandHandler("help", Commands.help))
        app.add_handler(CommandHandler("balance", Commands.balance))
        app.add_handler(CommandHandler("positions", Commands.positions))
        app.add_handler(CommandHandler("orders", Commands.orders))

        # Message Handler
        app.add_handler(MessageHandler(filters.TEXT, MessageHandling.handle_message))

        # Error Handler
        app.add_error_handler(ErrorHandling.handle_error)

        # Polling
        print("Bot is running...")
        app.run_polling(poll_interval=5)

if __name__ == "__main__":
    app = App()
    app.run()