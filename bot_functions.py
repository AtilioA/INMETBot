import os
import logging
import requests
import pycep_correios as pycep
from utils import viacep
import models
from scraping import scrap_satellites
from utils import bot_messages
from utils import bot_utils
from scraping import parse_alerts
from telegram.ext.dispatcher import run_async

functionsLogger = logging.getLogger(__name__)
functionsLogger.setLevel(logging.DEBUG)

MAX_ALERTS_PER_MESSAGE = 6  # To avoid "message is too long" error


@bot_utils.send_typing_action
def send_instructions_message(update, context):
    """Reply to the last message with the instructions message."""

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.instructions)


@run_async
def catch_all_if_private(update, context):
    """Reply to any message not handled (if not sent to a group/channel)."""

    chat = models.create_chat_obj(update)

    if chat.type == "private":
        functionsLogger.debug(f"catch_all: {update.message.chat.type} to @{update.message.chat.username}")
        return send_instructions_message(update, context)


@run_async
@bot_utils.send_typing_action
def cmd_help(update, context):
    """Send the help message to the user."""

    functionsLogger.debug(f"{update.message.chat.type} to @{update.message.chat.username}")

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.helpMessage, parse_mode="markdown", disable_web_page_preview=True)


@run_async
@bot_utils.send_typing_action
def cmd_start(update, context):
    """Send the start message to the user."""

    functionsLogger.debug(f"{update.message.chat.type} to @{update.message.chat.username}")

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.welcomeMessage, parse_mode="markdown")


@run_async
@bot_utils.send_upload_photo_action
def cmd_vpr(update, context):
    """Fetch and send latest VPR satellite image to the user."""

    vprImageURL = scrap_satellites.get_vpr_last_image()
    context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, photo=vprImageURL, timeout=10000)


@bot_utils.send_upload_video_action
def send_vpr_video(update, context, vprVideoPath, nImages, waitMessage):
    """Send the .mp4 file to the user and delete it."""

    caption = f"Últimas {nImages} imagens"
    context.bot.send_animation(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, caption=caption, animation=open(vprVideoPath, 'rb'), timeout=10000)
    context.bot.delete_message(chat_id=waitMessage.chat.id, message_id=waitMessage.message_id)
    os.remove(vprVideoPath)
    functionsLogger.info(f"Deleted {vprVideoPath}.")


@run_async
@bot_utils.send_typing_action
def cmd_vpr_gif(update, context):
    """Create and send GIF made of recent VPR satellite images to the user."""

    nImages = bot_utils.parse_n_images_input(update, context)
    if nImages:
        # Save the message so it can be deleted afterwards
        waitMessage = context.bot.send_message(chat_id=update.effective_chat.id, text=f"⏳ Buscando as últimas {nImages} imagens e criando GIF...", parse_mode="markdown")

        vprVideoPath = scrap_satellites.get_vpr_gif(nImages)

        return send_vpr_video(update, context, vprVideoPath, nImages, waitMessage)


@run_async
@bot_utils.send_upload_photo_action
def cmd_acumulada(update, context):
    """Fetch and send accumulated precipitation within given interval satellite image to the user."""

    functionsLogger.debug("Getting acumulada images...")

    # Parse input
    try:
        interval = context.args[0]
    except IndexError:
        functionsLogger.warning(f"No input in cmd_acumulada. Message text: \"{update.message.text}\"")
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.acumuladaError, parse_mode="markdown")
        interval = 1  # Use 24 hours as default

    acumuladaImageURL = scrap_satellites.get_acumulada_last_image(interval)
    if acumuladaImageURL:
        if interval == 1:
            caption = "Precipitação acumulada nas últimas 24 horas"
        else:
            caption = f"Precipitação acumulada nos últimos {interval} dias"
        context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, caption=caption, photo=acumuladaImageURL, timeout=10000)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text="❌ Não foi possível obter a imagem!", parse_mode="markdown")


@run_async
@bot_utils.send_upload_photo_action
def cmd_acumulada_previsao(update, context):
    """Fetch and send accumulated precipitation satellite image forecast for the next 24 hours to the user."""

    functionsLogger.debug("Getting acumulada previsão images...")

    acumuladaPrevisaoImageURL = scrap_satellites.get_acumulada_previsao()

    context.bot.send_photo(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, caption="Precipitação acumulada prevista para as próximas 24 horas", photo=acumuladaPrevisaoImageURL, timeout=10000)


def parse_CEP(update, context, cepRequired=True):
    """Parse CEP from user's text message."""

    text = update.message.text

    try:
        cep = context.args[0].strip().replace("-", "")  # Get string after "/alertas_CEP"
        return cep
    except IndexError:  # No number after /command
        functionsLogger.warning(f"No input in parse_CEP. Message text: \"{text}\"")
        message = f"❌ CEP não informado!\nExemplo:\n`{text.split(' ')[0]} 29075-910`"
    else:
        if not pycep.validar_cep(cep):
            message = f"❌ CEP inválido/não existe!\nExemplo:\n`{text.split(' ')[0]} 29075-910`"

    if cepRequired:
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=message, parse_mode="markdown")
        return None


def check_and_send_alerts_warning(update, context, alerts, city=None):
    """Check for alerts and send message to the user. Limits search to city if passed as input.

    Returns
    --------
    warned : bool
        True if any alert was sent, False otherwise.
    """

    warned = False
    alertMessage = ""
    alertCounter = 1

    if alerts:
        for alert in alerts:
            alertObj = models.Alert(alertDict=alert)
            warned = True
            if not city:
                alertMessage += alertObj.get_alert_message()
                if alertCounter >= MAX_ALERTS_PER_MESSAGE:
                    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
                    alertMessage = ""
                    alertCounter = 1
                alertCounter += 1
            else:
                alertMessage += alertObj.get_alert_message(city)
                if alertCounter >= 6:
                    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
                    alertMessage = ""
                    alertCounter = 1
                alertCounter += 1
        # "Footer" message after all alerts
        alertMessage += "\nMais informações em http://www.inmet.gov.br/portal/alert-as/"
    elif not city:
        alertMessage = "✅ Não há alertas graves para o Brasil no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"
    else:
        alertMessage = f"✅ Não há alertas para {city} no momento.\n\nVocê pode ver outros alertas em http://www.inmet.gov.br/portal/alert-as/"

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)

    return warned


@run_async
@bot_utils.send_typing_action
def cmd_alerts_brasil(update, context):
    """Fetch and send active high-risk alerts for Brazil."""

    functionsLogger.debug("Getting alerts for Brazil...")

    # Ignore moderate alerts
    alerts = models.INMETBotDB.alertsCollection.find({"severity": {"$ne": "Perigo Potencial"}})
    if alerts:
        if check_and_send_alerts_warning(update, context, alerts):
            return None
    else:
        alertMessage = "✅ Não há alertas graves para o Brasil no momento.\n\nVocê pode ver outros alertas menores em http://www.inmet.gov.br/portal/alert-as/"
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)


@run_async
@bot_utils.send_typing_action
def cmd_alerts_CEP(update, context):
    """Fetch and send active high-risk alerts for given CEP (zip code)."""

    functionsLogger.debug("Getting alerts by CEP (zip code)...")

    cep = parse_CEP(update, context)
    try:
        if cep:
            city = viacep.get_cep_city(cep)

            # Include moderate alerts
            alerts = list(models.INMETBotDB.alertsCollection.find({"cities": city}))
            check_and_send_alerts_warning(update, context, alerts, city)
    except (pycep.excecoes.ExcecaoPyCEPCorreios, KeyError) as cepError:  # Invalid zip code
        functionsLogger.warning(f"{cepError} on cmd_alerts_CEP. Message text: \"{update.message.text}\"")


@run_async
@bot_utils.send_typing_action
def alerts_location(update, context):
    """Handle location messages by checking for alerts in that region.

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

                # Include moderate alerts
                alerts = list(models.INMETBotDB.alertsCollection.find({"cities": city}))
                check_and_send_alerts_warning(update, context, alerts, city)
                return None
            else:
                alertMessage = "❌ A localização indica uma região fora do Brasil."
        else:
            functionsLogger.error("Failed GET request to reverse geocoding API.")
            alertMessage = "❌ Não foi possível verificar a região 😔."

        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=alertMessage, parse_mode="markdown")


@bot_utils.send_typing_action
def cmd_alerts_map(update, context):
    """Take screenshot of the alerts map with Selenium and send to the user."""

    # Save the message so it can be deleted afterwards
    waitMessage = context.bot.send_message(chat_id=update.effective_chat.id, text=bot_messages.alertsMapMessage, parse_mode="markdown", disable_web_page_preview=True)

    alertsMapPath = parse_alerts.take_screenshot_alerts_map()
    send_alerts_map_screenshot(update, context, alertsMapPath, waitMessage)


@run_async
@bot_utils.send_upload_photo_action
def send_alerts_map_screenshot(update, context, alertsMapPath, waitMessage):
    """Send the alerts map screenshot."""

    context.bot.send_photo(chat_id=update.effective_chat.id, caption="Fonte: http://www.inmet.gov.br/portal/alert-as/", reply_to_message_id=update.message.message_id, photo=open(alertsMapPath, 'rb'), timeout=10000)

    context.bot.delete_message(chat_id=waitMessage.chat.id, message_id=waitMessage.message_id)

    os.remove(alertsMapPath)
    functionsLogger.info(f"Deleted {alertsMapPath}.")


@bot_utils.send_typing_action
def cmd_chat_subscribe_alerts(update, context):
    """Subscribe chat and/or CEP."""

    textArgs = update.message.text.split(' ')
    cep = parse_CEP(update, context, cepRequired=False)

    chat = models.create_chat_obj(update)
    subscribeResult = chat.subscribe_chat(cep)
    subscribeMessage = chat.get_subscribe_message(subscribeResult, textArgs, cep)

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=subscribeMessage, parse_mode="markdown")


@bot_utils.send_typing_action
def cmd_chat_unsubscribe_alerts(update, context):
    """Unsubscribe chat and/or CEP."""

    cep = parse_CEP(update, context, cepRequired=False)

    chat = models.create_chat_obj(update)
    unsubscribeResult = chat.unsubscribe_chat(cep)
    unsubscribeMessage = chat.get_unsubscribe_message(unsubscribeResult, cep=cep)

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=unsubscribeMessage, parse_mode="markdown")


@run_async
@bot_utils.send_typing_action
def cmd_chat_subscription_status(update, context):
    """Send chat's subscription status."""

    chat = models.create_chat_obj(update=update)

    subscriptionStatus = chat.check_subscription_status()
    subscriptionStatusMessage = chat.get_subscription_status_message(subscriptionStatus)

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=subscriptionStatusMessage, parse_mode="markdown")


@run_async
@bot_utils.send_typing_action
def cmd_chat_deactivate(update, context):
    """ Set chat's activated status to False. """

    chat = models.create_chat_obj(update=update)
    deactivateMessage = chat.activate_callback(chat.deactivate)

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=deactivateMessage, parse_mode="markdown")


@run_async
@bot_utils.send_typing_action
def cmd_chat_activate(update, context):
    """ Set chat's activated status to True. """

    chat = models.create_chat_obj(update=update)
    activateMessage = chat.activate_callback(chat.activate)

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=activateMessage, parse_mode="markdown")


@run_async
@bot_utils.send_typing_action
def cmd_chat_toggle_activated(update, context):
    """ Toggle chat's activated status """

    chat = models.create_chat_obj(update=update)
    toggleMessage = chat.activate_callback(chat.toggle_activated)

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=toggleMessage, parse_mode="markdown")


@run_async
@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo(update, context):
    """Send default Sorrizo Ronaldo video."""

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.sorrizoChegou, parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAPmXkSUcBDsVM300QABV4Oerb9PcUx3AAL8AAODXihGe5y1jndyb80YBA")


@run_async
@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo_will_rock_you(update, context):
    """Send "We Will Rock You" Sorrizo Ronaldo video variation."""

    context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=bot_messages.sorrizoQueen, parse_mode="markdown")
    context.bot.send_video(chat_id=update.effective_chat.id, video="BAACAgEAAxkBAAICZ15HDelLB1IH1i3hTB8DaKwWlyPMAAJ8AAPfLzhG0hgf8dxd_zQYBA")


@run_async
def error(update, context):
    """Log errors caused by Updates."""

    functionsLogger.warning('Update "%s" caused error "%s"', update, context.error)
