import os
import web
from functools import wraps
import telegram
from telegram.ext import Updater, CommandHandler
import scrap_satelites
import parse_alerts
import pycep_correios as pycep


# Webserver to prevent the bot from sleeping
urls = ('/', 'index')
class index:
    def GET(self):
        i = web.input(name=None)
        return render.index(i.name)
render = web.template.render('templates/')

# CREDENTIALS
token = os.environ.get("TELEGRAM_INMETBOT_APIKEY")
# print(os.environ.get("TELEGRAM_INMETBOT_APIKEY"))

# TELEGRAM CONFIG
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
bot = telegram.Bot(token)


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
send_upload_document_action = send_action(telegram.ChatAction.UPLOAD_DOCUMENT)


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
    vprImageURL = scrap_satelites.get_vpr_last_image()
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


@send_upload_document_action
def vpr_gif(update, context):
    # scrap_satelites.scrap_page()
    vprImageURL = "VPR.gif"
    context.bot.send_document(chat_id=update.effective_chat.id, document=open(vprImageURL, 'rb'))


@send_upload_photo_action
def acumulada(update, context):
    print("Getting acumulada images...")

    text = update.message.text
    try:
        interval = text.split(' ')[1]
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Não foi possível obter a imagem!\nOs intervalos permitidos são 1, 3, 5, 10, 15, 30 e 90 dias.\nExemplo:\n/acumulada 3")
        pass
    print(interval)
    acumuladaImageURL = scrap_satelites.get_acumulada_last_image(interval)
    if acumuladaImageURL:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=acumuladaImageURL)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Não foi possível obter a imagem!\nOs intervalos permitidos são 1, 3, 5, 10, 15, 30 e 90 dias.\nExemplo:\n/acumulada 3")


@send_upload_photo_action
def acumulada_previsao_24hrs(update, context):
    print("Getting acumulada previsão images...")
    acumuladaPrevisaoImageURL = scrap_satelites.get_acumulada_previsao_24hrs()
    context.bot.send_message(chat_id=update.effective_chat.id, text="Precipitação acumulada prevista para as próximas 24 horas:")
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=acumuladaPrevisaoImageURL)


@send_typing_action
def alertas_brasil(update, context):
    print("Getting alerts...")

    alerts = parse_alerts.parse_alerts()
    if alerts:
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
    else:
        alertMessage = "✅ Não há alertas graves no Brasil no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"
    context.bot.send_message(chat_id=update.effective_chat.id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)


@send_typing_action
def alertas_CEP(update, context):
    print("Getting alerts by CEP (zip code)...")

    text = update.message.text
    cep = text.split(' ')[1]
    if pycp.validar_cep(cep):
        cepJSON = pycep.consultar_cep(cep)
        city = cepJSON["cidade"]
        alerts = parse_alerts.parse_alerts()
        if alerts:
            alertMessage = ""
            for alert in alerts:
                if city in alert.area:
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
            else:
                alertMessage = "✅ Não há alertas graves na região no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"
        else:
            alertMessage = "✅ Não há alertas graves no Brasil no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"
            context.bot.send_message(chat_id=update.effective_chat.id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Não foi possível verificar a região - CEP inválido!\nExemplo:\n/alertas_CEP 29075-910")


@send_upload_video_action
def sorrizoronaldo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="É O *SORRIZO RONALDO* 😁 QUE CHEGOU...", parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAPmXkSUcBDsVM300QABV4Oerb9PcUx3AAL8AAODXihGe5y1jndyb80YBA")


@send_upload_video_action
def sorrizoronaldo_will_rock_you(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="👊👊👏 *SORRIZ*..", parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAICZ15HDelLB1IH1i3hTB8DaKwWlyPMAAJ8AAPfLzhG0hgf8dxd_zQYBA")


# Initialize handlers
start_handler = CommandHandler('start', start)

vpr_handler = CommandHandler('vpr', vpr)
vpr_gif_handler = CommandHandler('vpr_gif', vpr_gif)

acumulada_handler = CommandHandler('acumulada', acumulada)
acumulada_previsao_24hrs_handler = CommandHandler('acumulada_previsao_24hrs', acumulada_previsao_24hrs)

alertas_brasil_handler = CommandHandler('alertas_brasil', alertas_brasil)
alertas_CEP_handler = CommandHandler('alertas_CEP', alertas_CEP)

sorrizoronaldo_handler = CommandHandler('sorrizoronaldo', sorrizoronaldo)
sorrizoronaldo_will_rock_you_handler = CommandHandler('sorrizoronaldo_will_rock_you', sorrizoronaldo_will_rock_you)

# Add handlers to dispatcher
dispatcher.add_handler(start_handler)

dispatcher.add_handler(vpr_handler)
dispatcher.add_handler(vpr_gif_handler)

dispatcher.add_handler(acumulada_handler)
dispatcher.add_handler(acumulada_previsao_24hrs_handler)

dispatcher.add_handler(alertas_brasil_handler)
dispatcher.add_handler(CommandHandler(('alertas', 'alertas_brasil', 'avisos'), alertas_brasil_handler))
dispatcher.add_handler(alertas_CEP_handler)

dispatcher.add_handler(CommandHandler(('sorrizo', 'sorrizoronaldo', 'fodase'), sorrizoronaldo))
dispatcher.add_handler(CommandHandler(('sorrizoronaldo_will_rock_you', 'sorrizorock', 'sorrizoqueen', 'queenfodase'), sorrizoronaldo_will_rock_you))


updater.start_polling()

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
