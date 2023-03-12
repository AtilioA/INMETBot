import pprint
import os
import logging

import requests

import pycep_correios as pycep
from telegram.ext.dispatcher import run_async

from models.Alert import Alert
from models.Chat import Chat

from utils import viacep, bot_messages, bot_utils

utilsFunctionsLogger = logging.getLogger(__name__)
utilsFunctionsLogger.setLevel(logging.DEBUG)


@run_async
# @bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_upload_photo_action
def send_alerts_map_screenshot(update, context, alertsMapPath, waitMessage):
    """Send the alerts map screenshot."""

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        caption=f"Fonte: {bot_messages.ALERTAS_URL}",
        reply_to_message_id=update.message.message_id,
        photo=open(alertsMapPath, "rb"),
        timeout=20000,
    )

    context.bot.delete_message(
        chat_id=waitMessage.chat.id, message_id=waitMessage.message_id
    )

    os.remove(alertsMapPath)
    utilsFunctionsLogger.info(f"Deleted {alertsMapPath}.")


@run_async
@bot_utils.log_command
# @bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_forecast(update, context):
    """Fetch and send weather forecast for the next 3 days for given CEP (zip code)."""

    utilsFunctionsLogger.debug("Getting weather forecast by CEP (zip code)...")
    textArgs = update.message.text.split(" ")

    try:
        cep = bot_utils.parse_CEP(update, context)
        IBGECode = viacep.get_cep_IBGE(cep)

        APIBaseURL = f"https://apiprevmet3.inmet.gov.br"

        # Create headers for requests
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }
        response = requests.get(
            f"{APIBaseURL}/previsao/{IBGECode}",
            headers=headers,
            allow_redirects=False,
        )
        if response.status_code == 200:
            utilsFunctionsLogger.info("Successful GET request to APIPREVMET3 endpoint!")
            # pprint.pprint(response.json()[IBGECode])

            data = response.json()[IBGECode]

            for date in data.keys():
                pprint.pprint(date)

                forecastMessage = bot_messages.createForecastMessage(date, data[date])
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    reply_to_message_id=update.message.message_id,
                    text=forecastMessage,
                    parse_mode="markdown",
                )
    except (
        pycep.excecoes.ExcecaoPyCEPCorreios,
        KeyError,
        Exception,
    ) as cepError:  # Invalid zip code
        utilsFunctionsLogger.warning(
            f'{cepError} on cmd_forecast. Message text: "{update.message.text}"'
        )
        message = bot_messages.invalidZipCode.format(textArgs=textArgs[0])
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=message,
            parse_mode="markdown",
        )


# Note that this shouldn't really be under commands/
def check_and_send_alerts_warning(update, context, alerts, city=None):
    """Check for alerts and send message to the user. Limits search to city if passed as input.

    Returns
    --------
    warned : bool
        True if any alert was sent, False otherwise.
    """

    warned = False
    alertMessage = ""
    alertCounter = 0

    if alerts:
        for alert in alerts:
            alertObj = Alert(alertDict=alert)
            alertMessage += alertObj.get_alert_message(
                location=city, brazil=not (bool(city))
            )
            alertCounter += 1

            if alertCounter >= bot_messages.MAX_ALERTS_PER_MESSAGE:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    reply_to_message_id=update.message.message_id,
                    text=alertMessage,
                    parse_mode="markdown",
                    disable_web_page_preview=True,
                )
                alertMessage = ""
                alertCounter = 0
        warned = True

        # "Footer" message after all alerts
        alertMessage += bot_messages.moreInfoAlertAS
    elif not city:
        alertMessage = bot_messages.noAlertsBrazil
    else:
        alertMessage = bot_messages.noAlertsCity.format(
            city=city, ALERTAS_URL=bot_messages.ALERTAS_URL
        )

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=alertMessage,
        parse_mode="markdown",
        disable_web_page_preview=True,
    )

    return warned
