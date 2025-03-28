from telegram import Update
from telegram.ext import ContextTypes


class ErrorHandling:
    def __init__(self):
        pass

    async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"An error occurred by the update {update}: {context.error}")
        await update.message.reply_text("An error occurred. Please try again later.")
