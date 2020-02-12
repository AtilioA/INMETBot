from telegram.ext import Updater, CommandHandler
from configparser import ConfigParser
from bs4 import BeautifulSoup
import requests
import os
import web
# import scrap_satelites

# To prevent the bot from sleeping
urls = ('/input', 'index')
class index:
    def GET(self):
        i = web.input(name=None)
        return render.index(i.name)
render = web.template.render('templates/')


inmetSateliteBrasilVPR_URL = "http://www.inmet.gov.br/projetos/cga/capre/sepra/GEO/GOES12/REGIOES/BRASIL/"
def vpr_last_image():
    targetPage = "http://www.inmet.gov.br/satelites/?area=0&produto=GO_br_VPR&ct=1"
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(targetPage, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Skip first option element (not a photo)
        # Get option's value if it is a filename (not Mapa or numbers)
        option = html.find_all("option")[1]["value"]
        imageURL = f"{inmetSateliteBrasilVPR_URL}{option}"
        return imageURL
    else:
        print("Failed GET request.")
        return None


# CONFIG SETUP
config = ConfigParser()
config.read('config.ini')

# CREDENTIALS
token = config.get('access', 'token')
# print(token)

# CONFIG TELEGRAM
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
    vprImageURL = vpr_last_image()
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
