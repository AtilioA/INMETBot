import os
import telegram
from telegram.ext import Updater, CommandHandler


# CREDENTIALS
token = os.environ.get("TELEGRAM_INMETBOT_APIKEY")

# TELEGRAM CONFIG
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
bot = telegram.Bot(token)
