import logging
from alerts import parse_alerts

import requests
import pycep_correios as pycep
from telegram.ext.dispatcher import run_async

from models.db import INMETBotDB
from models.Alert import Alert
from models.Chat import Chat


from utils import viacep, bot_messages, bot_utils


alertsFunctionsLogger = logging.getLogger(__name__)
alertsFunctionsLogger.setLevel(logging.DEBUG)


@bot_utils.log_command
# @bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_alerts_map(update, context):
    """Take screenshot of the alerts map with Selenium and send to the user."""

    # Save the message so it can be deleted afterwards
    waitMessage = context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=bot_messages.alertsMapMessage,
        parse_mode="markdown",
        disable_web_page_preview=True,
    )

    alertsMapPath = parse_alerts.take_screenshot_alerts_map()
    send_alerts_map_screenshot(update, context, alertsMapPath, waitMessage)


@bot_utils.log_command
# @bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_subscribe_alerts(update, context):
    """Subscribe chat and/or CEP."""

    textArgs = update.message.text.split(" ")

    try:
        cep = bot_utils.parse_CEP(update, context, cepRequired=False)
    except Exception as error:
        alertsFunctionsLogger.error(
            f"Unknown error when parsing CEP for subscribed chat: {error}."
        )
        subscribeMessage = bot_messages.invalidZipCode.format(textArgs=textArgs[0])
    else:
        chat = Chat.create_chat_obj(update)
        subscribeResult = chat.subscribe_chat(cep)
        subscribeMessage = chat.get_subscribe_message(subscribeResult, textArgs, cep)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=subscribeMessage,
        parse_mode="markdown",
    )


@bot_utils.log_command
# @bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_unsubscribe_alerts(update, context):
    """Unsubscribe chat and/or CEP."""

    textArgs = update.message.text.split(" ")

    try:
        cep = bot_utils.parse_CEP(update, context, cepRequired=False)
    except Exception as error:
        alertsFunctionsLogger.error(
            f"Unknown error when parsing CEP for subscribed chat: {error}."
        )
        unsubscribeMessage = bot_messages.invalidZipCode.format(textArgs=textArgs[0])
    else:
        chat = Chat.create_chat_obj(update)
        unsubscribeResult = chat.unsubscribe_chat(cep)
        unsubscribeMessage = chat.get_unsubscribe_message(unsubscribeResult, cep)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=unsubscribeMessage,
        parse_mode="markdown",
    )


@run_async
# @bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_chat_subscription_status(update, context):
    """Send chat's subscription status."""

    chat = Chat.create_chat_obj(update=update)

    subscriptionStatus = chat.check_subscription_status()
    subscriptionStatusMessage = chat.get_subscription_status_message(subscriptionStatus)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=subscriptionStatusMessage,
        parse_mode="markdown",
    )


@run_async
# @bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_deactivate(update, context):
    """Set chat's activated status to False."""

    chat = Chat.create_chat_obj(update=update)
    deactivateMessage = chat.toggle_subscription_callback(chat.deactivate)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=deactivateMessage,
        parse_mode="markdown",
    )


@run_async
# @bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_activate(update, context):
    """Set chat's activated status to True."""

    chat = Chat.create_chat_obj(update=update)
    activateMessage = chat.toggle_subscription_callback(chat.activate)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=activateMessage,
        parse_mode="markdown",
    )


@run_async
# @bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_toggle_activated(update, context):
    """Toggle chat's activated status"""

    chat = Chat.create_chat_obj(update=update)
    toggleMessage = chat.toggle_subscription_callback(chat.toggle_activated)

    try:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=toggleMessage,
            parse_mode="markdown",
        )
    except Exception as error:
        alertsFunctionsLogger.error(f"Unexpected error: {error})")



@run_async
# @bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_alerts_brazil(update, context):
    """Fetch and send active high-risk alerts for Brazil."""

    alertsFunctionsLogger.debug("Getting alerts for Brazil...")

    try:
        cep = bot_utils.parse_CEP(update, context, cepRequired=False)
        if cep:
            return cmd_alerts_CEP(update, context)
    except:
        # No zip code provided
        pass

    # Ignore moderate alerts
    alerts = list(INMETBotDB.alertsCollection.find({"severity": {"$ne": "Moderate"}}))

    if list(alerts):
        return bot_utils.check_and_send_alerts_warning(update, context, alerts)
    else:
        alertMessage = bot_messages.noAlertsBrazil

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=alertMessage,
            parse_mode="markdown",
            disable_web_page_preview=True,
        )


@run_async
# @bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_alerts_CEP(update, context):
    """Fetch and send active high-risk alerts for given CEP (zip code)."""

    alertsFunctionsLogger.debug("Getting alerts by CEP (zip code)...")

    textArgs = update.message.text.split(" ")

    try:
        cep = bot_utils.parse_CEP(update, context, cepRequired=False)
        city = viacep.get_cep_city(cep)
        if not (cep or city):
            raise pycep.excecoes.ExcecaoPyCEPCorreios

        # Include moderate alerts
        alerts = list(INMETBotDB.alertsCollection.find({"cities": city}))
        bot_utils.check_and_send_alerts_warning(update, context, alerts, city)
    except (
        pycep.excecoes.ExcecaoPyCEPCorreios,
        KeyError,
        Exception,
    ) as cepError:  # Invalid zip code
        message = bot_messages.invalidZipCode.format(textArgs=textArgs[0])
        alertsFunctionsLogger.warning(
            f'{cepError} on cmd_alerts_CEP. Message text: "{update.message.text}"'
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=message,
            parse_mode="markdown",
        )

        chat = Chat.create_chat_obj(update=update)
        if chat.subscribed:
            checkingForSubscribed = context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text="*[🛠 BETA]* Irei checar os CEPs cadastrados no chat:",
                parse_mode="markdown",
            )

            # STUB:
            for cep in chat.CEPs:
                try:
                    city = viacep.get_cep_city(cep)
                    alertsFunctionsLogger.debug(f"- Checking {city}...")
                except Exception as error:
                    alertsFunctionsLogger.warning(f"Viacep error: {error}")
                    continue

                # Get alerts, by city, that weren't notified to this chat
                alerts = list(INMETBotDB.alertsCollection.find({"cities": city}))
                if alerts:
                    # Any alerts here are to be sent to the chat,
                    # since they affect a zip code and the chat hasn't been notified yet
                    alertCounter = 1
                    alertMessage = ""
                    alertsFunctionsLogger.info(f"-- Existing alert for {city}. --")
                    for alert in alerts:
                        if alertCounter >= bot_messages.MAX_ALERTS_PER_MESSAGE:
                            try:
                                print(
                                    chat.id,
                                )
                                context.bot.send_message(
                                    chat_id=chat.id,
                                    text=alertMessage,
                                    parse_mode="markdown",
                                    disable_web_page_preview=True,
                                )
                            except Exception as error:
                                alertsFunctionsLogger.error(
                                    f"ERRO: unable to send message to {chat.id} ({chat.title}): {error}. Removing chat from DB......"
                                )
                                INMETBotDB.subscribedChatsCollection.delete_one(
                                    {"chatID": chat.id}
                                )

                                alertMessage = ""
                                alertCounter = 1

                        alertObj = Alert(alertDict=alert)
                        alertMessage += alertObj.get_alert_message(city)
                        alertsFunctionsLogger.info(
                            f"-- Notifying chat {chat.id} about alert {alert['alertID']}... --"
                        )

                        INMETBotDB.alertsCollection.update_one(
                            {"alertID": alert["alertID"]},
                            {"$addToSet": {"notifiedChats": chat.id}},
                        )
                        alertCounter += 1

                    # "Footer" message after all alerts
                    alertMessage += f"\nMais informações em {bot_messages.ALERTAS_URL}."

                    try:
                        context.bot.send_message(
                            chat_id=chat.id,
                            text=alertMessage,
                            parse_mode="markdown",
                            disable_web_page_preview=True,
                        )
                    except Exception as error:
                        alertsFunctionsLogger.error(
                            f"ERRO: unable to send message to {chat.id} ({chat.title}): {error}. Removing chat from DB......"
                        )
                        INMETBotDB.subscribedChatsCollection.delete_one(
                            {"chatID": chat.id}
                        )

            context.bot.delete_message(
                chat_id=checkingForSubscribed.chat.id,
                message_id=checkingForSubscribed.message_id,
            )


@run_async
# @bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def alerts_location(update, context):
    """Handle location messages by checking for alerts in that region.

    Send message with current alerts, if any.
    """

    # Parse location from message
    location = update.message
    if location:
        latitude = location["location"]["latitude"]
        longitude = location["location"]["longitude"]

    # Create headers for request
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
    }
    # Request to location API
    response = requests.get(
        f"https://api.3geonames.org/{latitude},{longitude}.json",
        headers=headers,
        allow_redirects=False,
    )
    if response.status_code == 200:
        alertsFunctionsLogger.info("Successful GET request to reverse geocoding API!")

        # Get data from response
        responseData = response.json()
        # alertsFunctionsLogger.debug(f"reverseGeocode json: {responseData}")
        state = responseData["nearest"]["state"]

        if state == "BR":
            city = responseData["nearest"]["region"]

            # Include moderate alerts
            alerts = list(INMETBotDB.alertsCollection.find({"cities": city}))
            return bot_utils.check_and_send_alerts_warning(update, context, alerts, city)
        else:
            alertMessage = bot_messages.locationOutsideBrazil
    else:
        alertsFunctionsLogger.error("Failed GET request to reverse geocoding API.")
        alertMessage = bot_messages.unableToCheckAlertsLocation

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=alertMessage,
        parse_mode="markdown",
    )
