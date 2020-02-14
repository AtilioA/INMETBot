import telegram
from telegram.ext import Updater, CommandHandler
from configparser import ConfigParser
from bs4 import BeautifulSoup
import requests
import os
import web
import scrap_satelites
import parse_alerts
from functools import wraps

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
bot = telegram.Bot(token)
# for update in bot.get_updates():
    # print(update)


# Decorators to simulate user feedback
def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func

    return decorator

send_typing_action = send_action(telegram.ChatAction.TYPING)
send_upload_photo_action = send_action(telegram.ChatAction.UPLOAD_PHOTO)
send_upload_video_action = send_action(telegram.ChatAction.UPLOAD_VIDEO)


# BOT MESSAGES
welcomeMessage = """Olá! Este bot pode enviar imagens e informações úteis disponíveis no site do INMET diretamente pelo Telegram.
*EM CONSTRUÇÃO*

—
Não filiado ao INMET
Criado por @AtilioA
"""

# BOT FUNCTIONS AND HANDLERS
@send_typing_action
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcomeMessage, parse_mode="markdown")

@send_upload_photo_action
def vpr(update, context):
    vprImageURL = scrap_satelites.vpr_last_image()
    # print(vprImageURL)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=vprImageURL)

@send_typing_action
def alertas(update, context):
    print("Getting alerts...")

    alerts = parse_alerts.parse_alerts()
    alertMessage = ""
    for alert in alerts:
        if alert.severity == "Perigo":
            severityEmoji = "🔶"
        else:
            severityEmoji = "🚨"

        area = ','.join(alert.area)

        formattedStartDate = alert.startDate.strftime("%d/%m/%Y %H:%M")
        formattedEndDate = alert.endDate.strftime("%d/%m/%Y %H:%M")

        alertMessage += f"""
{severityEmoji} *{alert.event}*

        *Áreas afetadas*: {area}.
        *Vigor*: De {formattedStartDate} a {formattedEndDate}.
        {alert.description}

"""
        # Gráfico do alerta: {alert.graphURL}

    alertMessage += "Veja os gráficos em http://www.inmet.gov.br/portal/alert-as/"
    context.bot.send_message(chat_id=update.effective_chat.id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)

@send_upload_video_action
def sorrizoronaldo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="É O *SORRIZO RONALDO* 😁 QUE CHEGOU...", parse_mode="markdown")
    sorrizoVideo = context.bot.get_file("BAACAgEAAxkBAAPmXkSUcBDsVM300QABV4Oerb9PcUx3AAL8AAODXihGe5y1jndyb80YBA")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAPmXkSUcBDsVM300QABV4Oerb9PcUx3AAL8AAODXihGe5y1jndyb80YBA")


start_handler = CommandHandler('start', start)
vpr_handler = CommandHandler('vpr', vpr)
alertas_handler = CommandHandler('alertas', alertas)
sorrizoronaldo_handler = CommandHandler('sorrizoronaldo', sorrizoronaldo)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(vpr_handler)
dispatcher.add_handler(alertas_handler)
dispatcher.add_handler(sorrizoronaldo_handler)

updater.start_polling()

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
