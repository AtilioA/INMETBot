from telegram.ext import Updater, CommandHandler
from configparser import ConfigParser
from bs4 import BeautifulSoup
import requests
import os
import web
import scrap_satelites

# To prevent the bot from sleeping
urls = ('/', 'index')
class index:
    def GET(self):
        return "200"


# CREDENTIALS
token = os.environ.get("TELEGRAM_INMETBOT_APIKEY")
# print(os.environ.get("TELEGRAM_INMETBOT_APIKEY"))

# TELEGRAM CONFIG
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher


# BOT MESSAGES
welcomeMessage = """Olá! Este bot pode enviar imagens e informações úteis disponíveis no site do INMET diretamente pelo Telegram.
*EM CONSTRUÇÃO*

—
Não filiado ao INMET
Criado por @AtilioA
"""


# BOT FUNCTIONS AND HANDLERS
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcomeMessage, parse_mode="markdown")


def vpr(update, context):
    vprImageURL = scrap_satelites.vpr_last_image()
    # print(vprImageURL)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=vprImageURL)


start_handler = CommandHandler('start', start)
vpr_handler = CommandHandler('vpr', vpr)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(vpr_handler)

# POOL
updater.start_polling()

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
    print("Bot running")
