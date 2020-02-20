import os
import logging
import requests
import pycep_correios as pycep
import viacep
import models
import scrap_satelites
import bot_messages
import bot_utils
import parse_alerts
from telegram.ext.dispatcher import run_async

functionsLogger = logging.getLogger(__name__)
functionsLogger.setLevel(logging.DEBUG)


@bot_utils.send_typing_action
def send_instructions_message(update, context):
    """ Reply to the last message with the instructions message. """

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.instructions)


@run_async
def catch_all_if_not_group(update, context):
    """ Reply to any message not handled (if not sent to a group/channel). """

    if not bot_utils.is_group_or_channel(update.effective_chat.id):
        functionsLogger.debug("catch_all: not group")
        return send_instructions_message(update, context)


@run_async
@bot_utils.send_typing_action
def cmd_help(update, context):
    """ Send the help message to the user. """

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.helpMessage, parse_mode="markdown", disable_web_page_preview=True)


@run_async
@bot_utils.send_typing_action
def cmd_start(update, context):
    """ Send the help message to the user.  """

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.welcomeMessage, parse_mode="markdown")


@run_async
@bot_utils.send_upload_photo_action
def cmd_vpr(update, context):
    """ Fetch and send latest VPR satellite image to the user """

    vprImageURL = scrap_satelites.get_vpr_last_image()
    context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, photo=vprImageURL, timeout=1000)


@bot_utils.send_upload_video_action
def send_vpr_video(update, context, vprVideoPath):
    """ Send the .mp4 file to the user and delete it """

    context.bot.send_animation(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, animation=open(vprVideoPath, 'rb'), timeout=1000)
    os.remove(vprVideoPath)
    functionsLogger.info(f"Deleted {vprVideoPath}.")


@run_async
@bot_utils.send_typing_action
def cmd_vpr_gif(update, context):
    """ Create and send GIF made of recent VPR satellite images to the user. """

    text = update.message.text

    nImages = bot_utils.parse_n_images_input(update, context, text)
    if nImages:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"⏳ Buscando as últimas {nImages} imagens e criando GIF...", parse_mode="markdown")

        vprVideoPath = scrap_satelites.get_vpr_gif(nImages)

        return send_vpr_video(update, context, vprVideoPath)


@run_async
@bot_utils.send_upload_photo_action
def cmd_acumulada(update, context):
    """ Fetch and send accumulated precipitation within given interval satellite image to the user. """

    functionsLogger.debug("Getting acumulada images...")

    text = update.message.text

    # Parse input
    try:
        interval = text.split(' ')[1]
    except IndexError:
        functionsLogger.warning(f"No input in cmd_acumulada. Message text: \"{text}\"")
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.acumuladaError, parse_mode="markdown")
        interval = 1  # Use 24 hours as default

    acumuladaImageURL = scrap_satelites.get_acumulada_last_image(interval)
    if acumuladaImageURL:
        context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, photo=acumuladaImageURL, timeout=1000)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ Não foi possível obter a imagem!", parse_mode="markdown")


@run_async
@bot_utils.send_upload_photo_action
def cmd_acumulada_previsao_24hrs(update, context):
    """ Fetch and send accumulated precipitation satellite image forecast for the next 24 hours to the user. """

    functionsLogger.debug("Getting acumulada previsão images...")

    acumuladaPrevisaoImageURL = scrap_satelites.get_acumulada_previsao_24hrs()

    context.bot.send_message(chat_id=update.effective_chat.id, text="Precipitação acumulada prevista para as próximas 24 horas:", parse_mode="markdown")
    context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, photo=acumuladaPrevisaoImageURL, timeout=1000)


@run_async
@bot_utils.send_typing_action
def cmd_alerts_brasil(update, context):
    """ Fetch and send active high-risk alerts for Brazil. """

    functionsLogger.debug("Getting alerts for Brazil...")

    # Ignore moderate alerts
    alerts = models.alertsCollection.find({"severity": {"$ne": "Perigo Potencial"}})
    if alerts:
        alertMessage = ""
        for alert in alerts:
            alertObj = models.Alert(alertDict=alert)
            alertMessage += bot_utils.get_alert_message(alertObj)
        alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"
    else:
        alertMessage = "✅ Não há alertas graves para o Brasil no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)


@run_async
@bot_utils.send_typing_action
def cmd_alerts_CEP(update, context):
    """ Fetch and send active high-risk alerts for given CEP (zip code). """

    functionsLogger.debug("Getting alerts by CEP (zip code)...")

    text = update.message.text

    # Parse input
    try:
        cep = text.split(' ')[1].strip()  # Get string after "/alertas_CEP"
    except IndexError:  # No number after /alertas_CEP
        functionsLogger.error(f"No input in cmd_alerts_CEP. Message text: \"{text}\"")
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ CEP não informado!\nExemplo:\n`/alertas_CEP 29075-910`", parse_mode="markdown")
        return None

    try:
        if pycep.validar_cep(cep):
            city = viacep.get_cep_city(cep)
            cityWarned = False

            # Include moderate alerts
            alerts = models.alertsCollection.find({})
            if alerts:
                alertMessage = ""
                for alert in alerts:
                    alertObj = models.Alert(alertDict=alert)
                    if city in alertObj.cities:
                        cityWarned = True
                        alertMessage += bot_utils.get_alert_message(alertObj, city)

                alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"
                if not cityWarned:
                    alertMessage = f"✅ Não há alertas para {city} no momento.\n\nVocê pode ver outros alertas em http://www.inmet.gov.br/portal/alert-as/"
            else:
                alertMessage = "✅ Não há alertas para o Brasil no momento."

            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ CEP inválido/não existe!\nExemplo:\n`/alertas_CEP 29075-910`", parse_mode="markdown")
    except pycep.excecoes.ExcecaoPyCEPCorreios as zipError:  # Invalid zip code
        functionsLogger.error(f"{zipError} on cmd_alerts_CEP. Message text: \"{text}\"")
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ CEP inválido/não existe!\nExemplo:\n`/alertas_CEP 29075-910`", parse_mode="markdown")
        return None


@run_async
@bot_utils.send_typing_action
def cmd_alerts_map(update, context):
    """ Take screenshot of the alerts map and send to the user """

    context.bot.send_message(chat_id=update.effective_chat.id, text=bot_messages.alertsMapMessage, parse_mode="markdown", disable_web_page_preview=True)

    alertsMapPath = parse_alerts.take_screenshot_alerts_map()
    functionsLogger.debug(alertsMapPath)
    send_alerts_map_screenshot(update, context, alertsMapPath)


@bot_utils.send_upload_photo_action
def send_alerts_map_screenshot(update, context, alertsMapPath):
    context.bot.send_photo(chat_id=update.effective_chat.id, caption="Fonte: http://www.inmet.gov.br/portal/alert-as/", reply_to_message_id=update.message.message_id, photo=open(alertsMapPath, 'rb'), timeout=1000)

    os.remove(alertsMapPath)
    functionsLogger.info(f"Deleted {alertsMapPath}.")


@run_async
@bot_utils.send_typing_action
def alerts_location(update, context):
    """ Handle location messages by checking for alerts in that region.

        Send message with current alerts, if any.
    """

    location = update.message
    if location:
        latitude = location['location']['latitude']
        longitude = location['location']['longitude']

        reverseGeocode = requests.get(f"https://api.3geonames.org/{latitude},{longitude}.json")
        if reverseGeocode.status_code == 200:
            functionsLogger.info("Successful GET request to reverse geocoding API!")
            json = reverseGeocode.json()
            functionsLogger.debug(f"reverseGeocode json: {json}")
            state = json["nearest"]["state"]
            if state == "BR":
                city = json["nearest"]["region"]
                cityWarned = False

                # Ignore moderate alerts
                alerts = models.alertsCollection.find({"severity": {"$ne": "Perigo Potencial"}})
                if alerts:
                    alertMessage = ""
                    for alert in alerts:
                        alertObj = models.Alert(alertDict=alert)
                        if city in alertObj.cities:
                            cityWarned = True
                            alertMessage += bot_utils.get_alert_message(alertObj, city)

                    alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"

                    if not cityWarned:
                        alertMessage = f"✅ Não há alertas para {city} no momento.\n\nVocê pode ver outros alertas em http://www.inmet.gov.br/portal/alert-as/"
                else:
                    alertMessage = "✅ Não há alertas para o Brasil no momento."

                context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)

            else:
                context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ A localização indica uma região fora do Brasil.", parse_mode="markdown")

        else:
            functionsLogger.error("Failed GET request to reverse geocoding API.")
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ Não foi possível verificar a região 😔", parse_mode="markdown")


@run_async
@bot_utils.send_typing_action
def cmd_subscribed_alerts(update, context):
    statusMessage = ""
    isGroupOrChannel = bot_utils.is_group_or_channel(update.effective_chat.id)

    if models.is_subscribed(update.effective_chat.id):
        if isGroupOrChannel:
            statusMessage += "O grupo está inscrito nos alertas.\n\n"
        else:
            statusMessage += "Você está inscrito nos alertas.\n\n"

        CEPs = models.get_CEPs(update.effective_chat.id)
        if CEPs:
            statusMessage += "CEPs inscritos:\n"
            for cep in CEPs:
                statusMessage += f"{cep}\n"
        else:
            statusMessage += "Não há CEPs inscritos."
    else:
        if isGroupOrChannel:
            statusMessage += "O grupo não está inscrito nos alertas."
        else:
            statusMessage += "Você não está inscrito nos alertas."

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=statusMessage, parse_mode="markdown")


@bot_utils.send_typing_action
def cmd_subscribe_alerts(update, context):
    text = update.message.text
    textArgs = text.split(' ')

    # Parse input
    try:
        cep = textArgs[1].strip().replace("-", "")  # Get string after "/alertas_CEP"
    except IndexError:  # No string after /alertas_CEP
        functionsLogger.warning(f"No input in cmd_subscribe_alerts. Message text: \"{text}\"")
        cep = None
    else:
        if not pycep.validar_cep(cep):
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"❌ CEP inválido/não existe!\nExemplo:\n`{textArgs[0]} 29075-910`", parse_mode="markdown")
            return None

    subscribeMessage = bot_utils.get_subscribe_message(update, cep, textArgs)
    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=subscribeMessage, parse_mode="markdown")


@bot_utils.send_typing_action
def cmd_unsubscribe_alerts(update, context):
    text = update.message.text
    textArgs = text.split(' ')

    # Parse input
    try:
        cep = text.split(' ')[1].strip().replace("-", "")  # Get string after "/alertas_CEP"
    except IndexError:  # No number after /alertas_CEP
        functionsLogger.warning(f"No input in cmd_unsubscribe_alerts. Message text: \"{text}\"")
        cep = None
    else:
        if not pycep.validar_cep(cep):
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=f"❌ CEP inválido/não existe!\nExemplo:\n`{text.split(' ')[0]} 29075-910`", parse_mode="markdown")
            return None

    unsubscribeMessage = bot_utils.get_unsubscribe_message(update, cep, textArgs)
    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=unsubscribeMessage, parse_mode="markdown")


@run_async
@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo(update, context):
    """ Send default Sorrizo Ronaldo video. """

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.sorrizoChegou, parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAPmXkSUcBDsVM300QABV4Oerb9PcUx3AAL8AAODXihGe5y1jndyb80YBA")


@run_async
@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo_will_rock_you(update, context):
    """ Send "We Will Rock You" Sorrizo Ronaldo video variation. """

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.sorrizoQueen, parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAICZ15HDelLB1IH1i3hTB8DaKwWlyPMAAJ8AAPfLzhG0hgf8dxd_zQYBA")


@run_async
def error(update, context):
    """ Log errors caused by Updates. """

    functionsLogger.warning('Update "%s" caused error "%s"', update, context.error)
