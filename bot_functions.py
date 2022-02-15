import time
import pprint
import os
import logging

import telegram
import arrow
import requests
import fgrequests
import pycep_correios as pycep
from telegram.ext.dispatcher import run_async

import models
from bot_routines import delete_past_alerts_routine, parse_alerts_routine, notify_chats_routine
from utils import viacep, bot_messages, bot_utils, parse_alerts


functionsLogger = logging.getLogger(__name__)
functionsLogger.setLevel(logging.DEBUG)


@bot_utils.send_typing_action
def send_instructions_message(update, context):
    """Reply to the last message with the instructions message."""

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=bot_messages.instructions,
        parse_mode="markdown",
    )


@run_async
@bot_utils.ignore_users
def catch_all_if_private(update, context):
    """Reply to any message not handled (if not sent to a group/channel)."""

    chat = models.create_chat_obj(update)

    if chat.type == "private":
        functionsLogger.debug(
            f"catch_all: {update.message.chat.type} to @{update.message.chat.username}"
        )
        return send_instructions_message(update, context)


@run_async
@bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_help(update, context):
    """Send the help message to the user."""

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=bot_messages.helpMessage,
        parse_mode="markdown",
        disable_web_page_preview=True,
    )


@run_async
@bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_start(update, context):
    """Send the start message to the user."""

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=bot_messages.welcomeMessage,
        parse_mode="markdown",
    )


@run_async
@bot_utils.ignore_users
@bot_utils.log_command
def cmd_vpr(update, context):
    """Fetch and send latest VPR satellite image to the user."""

    try:
        # "Guess" image from INMET's API
        APIBaseURL = "https://apisat.inmet.gov.br/"
        regiao = "BR"

        # Get current time
        utcNow = arrow.utcnow()
        dayNow = utcNow.format("YYYY-MM-DD")
        minutesNow = utcNow.format("mm")

        # Get round hours
        floorMinutes = int(minutesNow) // 10 * 10
        floorDate = utcNow.replace(minute=floorMinutes)

        # Create headers for requests
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }

        # We do this because retrieving hours from the API takes several seconds, so it is faster to guess endpoints (only three are possible)
        requestURLS = []
        for i in range(1, 4):
            tryDate = floorDate.shift(minutes=-i * 10)
            requestURLS.append(
                f"{APIBaseURL}GOES/{regiao}/VP/{dayNow}/{tryDate.format('HH:mm')}"
            )

        # Request all URLs, filter the most recent one that was successful
        response = list(
            filter(lambda x: x.status_code == 200, fgrequests.build(requestURLS))
        )
        # Get json from the response
        vprData = response[0].json()

        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id,
            action=telegram.ChatAction.UPLOAD_PHOTO,
        )

        # Load image from base64 to memory
        vprImage = bot_utils.loadB64ImageToMemory(vprData["base64"])

        hourLastImage = arrow.get(vprData['hora'], "HH:mm").to("-03:00").format("HH:mm")
        hourLastImageCaption = f" ({hourLastImage})."

        caption = bot_messages.lastAvailableImageCaption + hourLastImageCaption

        # Send image from memory
        context.bot.send_photo(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            photo=vprImage,
            caption=caption,
            timeout=20000,
        )
    # If no request was successful
    except IndexError:
        try:
            # Request all images from today
            response = requests.get(
                f"{APIBaseURL}GOES/{regiao}/VP/{dayNow}",
                headers=headers,
                allow_redirects=False,
            )

            if response.status_code == 200:
                # Get only the latest image
                data = response.json()[0]
                functionsLogger.info("Successful GET request to API VPR endpoint!")

                context.bot.send_chat_action(
                    chat_id=update.effective_message.chat_id,
                    action=telegram.ChatAction.UPLOAD_PHOTO,
                )

                # Load image from base64 to memory
                vprImage = bot_utils.loadB64ImageToMemory(data["base64"])

                # Send image from memory
                context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    reply_to_message_id=update.message.message_id,
                    photo=vprImage,
                    caption=bot_messages.lastAvailableImageCaption,
                    timeout=20000,
                )
        # If all else fails
        except IndexError:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text=bot_messages.unavailableImage,
            )


@bot_utils.send_upload_video_action
def send_vpr_video(update, context, vprVideoPath, nImages, waitMessage, nImagesMessage, gifTimeBoundariesDict):
    """Send the .mp4 file to the user and delete it."""

    timeBoundaries = ""
    if gifTimeBoundariesDict:
        timeBoundaries = f" (de {gifTimeBoundariesDict['firstImage']} até {gifTimeBoundariesDict['lastImage']})"

    caption = f"Últimas {nImages} imagens" + timeBoundaries
    context.bot.send_animation(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        caption=caption,
        animation=open(vprVideoPath, "rb"),
        timeout=20000,
    )

    context.bot.delete_message(
        chat_id=waitMessage.chat.id, message_id=waitMessage.message_id
    )
    context.bot.delete_message(
        chat_id=nImagesMessage.chat.id, message_id=nImagesMessage.message_id
    )

    os.remove(vprVideoPath)
    functionsLogger.info(f"Deleted {vprVideoPath}.")


@run_async
@bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_vpr_gif(update, context):
    """Create and send GIF made of recent VPR satellite images to the user."""

    nImages, nImagesMessage = bot_utils.parse_n_images_input(update, context)
    if nImages:
        # Save the message so it can be deleted afterwards
        waitMessage = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=bot_messages.waitMessageSearchGIF.format(nImages=nImages),
            parse_mode="markdown",
        )

        # Get images from INMET's API
        APIBaseURL = "https://apisat.inmet.gov.br/"
        regiao = "BR"

        utcNow = arrow.utcnow()
        dayNow = utcNow.format("YYYY-MM-DD")

        # Create headers for requests
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }
        response = requests.get(
            f"{APIBaseURL}/horas/GOES/{regiao}/VP/{dayNow}",
            headers=headers,
            allow_redirects=True,
        )
        if response.status_code == 200:
            functionsLogger.info("Successful GET request to API VPR endpoint!")
            data = response.json()

            # Get images from today + images from yesterday (if needed)
            nImagesForToday = len(data)
            dataYesterday = None
            nImagesForYesterday = None
            if nImages > nImagesForToday:
                nImagesForYesterday = nImages - nImagesForToday
                responseYesterday = requests.get(
                    f"{APIBaseURL}/horas/GOES/{regiao}/VP/{utcNow.shift(days=-1).format('YYYY-MM-DD')}",
                    headers=headers,
                    allow_redirects=True,
                )
                dataYesterday = responseYesterday.json()[:nImagesForYesterday]

            vprResponse = bot_utils.get_vpr_images_data(
                data, nImages, dayNow, nImagesForYesterday, dataYesterday
            )
            gifTimeBoundariesDict = {
                "firstImage": arrow.get(vprResponse[-1]['hora'], "HH:mm").to("-03:00").format("HH:mm"),
                "lastImage": arrow.get(vprResponse[0]['hora'], "HH:mm").to("-03:00").format("HH:mm")
            }
            gifFilename = bot_utils.create_gif_vpr_data(vprResponse, nImages)

            return send_vpr_video(update, context, gifFilename, nImages, waitMessage, nImagesMessage, gifTimeBoundariesDict)
        else:
            functionsLogger.error("Failed GET request to VPR API.")
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text=bot_messages.failedFetchImage,
                parse_mode="markdown",
            )
            if nImagesMessage:
                context.bot.delete_message(
                    chat_id=update.effective_chat.id, message_id=nImagesMessage
                )
            return None


@run_async
@bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_upload_photo_action
def cmd_acumulada(update, context):
    """Fetch and send accumulated precipitation within given interval satellite image to the user."""

    try:
        functionsLogger.debug("Getting acumulada images...")
        acumuladaWarnMessage = ""

        # Parse input
        try:
            inputInterval = int(context.args[0])
        except IndexError:
            functionsLogger.warning(
                f'No input in cmd_acumulada. Message text: "{update.message.text}"'
            )
            acumuladaWarnMessage = context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text=bot_messages.acumuladaWarnMissing.format(interval=1),
                parse_mode="markdown",
            )
            inputInterval = 1  # Use 1 day as default

        # Send uploading photo action
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id,
            action=telegram.ChatAction.UPLOAD_PHOTO,
        )

        # Request image from INMET's API
        brazilNow = arrow.utcnow().to("Brazil/East").shift(days=-1)
        dayNow = brazilNow.format("YYYY-MM-DD")
        APIBaseURL = "https://apiprec.inmet.gov.br/"

        # Create headers for requests
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"
        }
        response = requests.get(
            f"{APIBaseURL}{dayNow}", headers=headers, allow_redirects=False
        )
        if response.status_code == 200:
            functionsLogger.info("Successful GET request to INMET's APIPREC endpoint!")

            # Get data from response
            data = response.json()

            # Adjust input to available intervals
            availableIntervals = [1, 3, 5, 10, 15, 30, 90]
            caption = ""
            interval = inputInterval
            if interval in availableIntervals:
                caption = f"Precipitação acumulada nos últimos {interval} dias"
                indexInterval = availableIntervals.index(interval)
            else:
                # Get closest value to input if it isn't in the interval
                absolute_diff = lambda listValue: abs(listValue - interval)
                interval = min(availableIntervals, key=absolute_diff)

                # Warn user about input change
                acumuladaWarnMessage = context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    reply_to_message_id=update.message.message_id,
                    text=bot_messages.acumuladaWarn.format(
                        interval=interval, inputInterval=inputInterval
                    ),
                    parse_mode="markdown",
                )
            if interval == 1:
                caption = "Precipitação acumulada nas últimas 24 horas"

            # Get correct image dictionary from list inside json
            data = data[availableIntervals.index(interval)]

            # Load image from base64 string to memory
            acumuladaImage = bot_utils.loadB64ImageToMemory(data["base64"])

            # Send image from memory
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                photo=acumuladaImage,
                caption=caption,
                timeout=20000,
            )
        # If request has failed
        else:
            functionsLogger.error("Failed GET request to INMET's APIPREC endpoint.")
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                reply_to_message_id=update.message.message_id,
                text=bot_messages.failedFetchImage,
                parse_mode="markdown",
            )
    # If all else fails
    except ValueError:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=bot_messages.unavailableImage,
        )

    if acumuladaWarnMessage:
        # Only the current thread will sleep
        time.sleep(5)
        context.bot.delete_message(
            chat_id=acumuladaWarnMessage.chat.id,
            message_id=acumuladaWarnMessage.message_id,
        )


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
            alertObj = models.Alert(alertDict=alert)
            alertMessage += alertObj.get_alert_message(
                location=city, brazil=not (bool(city))
            )
            alertCounter += 1

            if alertCounter >= MAX_ALERTS_PER_MESSAGE:
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
        alertMessage = bot_messages.noAlertsCity.format(city=city, ALERTAS_URL=bot_messages.ALERTAS_URL)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=alertMessage,
        parse_mode="markdown",
        disable_web_page_preview=True,
    )

    return warned


@run_async
@bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_alerts_brazil(update, context):
    """Fetch and send active high-risk alerts for Brazil."""

    functionsLogger.debug("Getting alerts for Brazil...")

    try:
        cep = bot_utils.parse_CEP(update, context, cepRequired=False)
        if cep:
            return cmd_alerts_CEP(update, context)
    except:
        # No zip code provided
        pass

    # Ignore moderate alerts
    alerts = list(
        models.INMETBotDB.alertsCollection.find(
            {"severity": {"$ne": "Moderate"}}
        )
    )

    if list(alerts):
        return check_and_send_alerts_warning(update, context, alerts)
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
@bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_alerts_CEP(update, context):
    """Fetch and send active high-risk alerts for given CEP (zip code)."""

    functionsLogger.debug("Getting alerts by CEP (zip code)...")

    textArgs = update.message.text.split(" ")

    try:
        cep = bot_utils.parse_CEP(update, context, cepRequired=False)
        city = viacep.get_cep_city(cep)
        if not (cep or city):
            raise pycep.excecoes.ExcecaoPyCEPCorreios

        # Include moderate alerts
        alerts = list(models.INMETBotDB.alertsCollection.find({"cities": city}))
        check_and_send_alerts_warning(update, context, alerts, city)
    except (
        pycep.excecoes.ExcecaoPyCEPCorreios,
        KeyError,
        Exception,
    ) as cepError:  # Invalid zip code
        message = bot_messages.invalidZipCode.format(textArgs=textArgs[0])
        functionsLogger.warning(
            f'{cepError} on cmd_alerts_CEP. Message text: "{update.message.text}"'
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=message,
            parse_mode="markdown",
        )

        chat = models.create_chat_obj(update=update)
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
                    functionsLogger.debug(f"- Checking {city}...")
                except Exception as error:
                    functionsLogger.warning(f"Viacep error: {error}")
                    continue

                # Get alerts, by city, that weren't notified to this chat
                alerts = list(
                    models.INMETBotDB.alertsCollection.find({"cities": city})
                )
                if alerts:
                    print("tem alerta o carai")
                    # Any alerts here are to be sent to the chat,
                    # since they affect a zip code and the chat hasn't been notified yet
                    alertCounter = 1
                    alertMessage = ""
                    functionsLogger.info(f"-- Existing alert for {city}. --")
                    for alert in alerts:
                        if alertCounter >= MAX_ALERTS_PER_MESSAGE:
                            try:
                                print(chat.id,)
                                context.bot.send_message(
                                    chat_id=chat.id,
                                    text=alertMessage,
                                    parse_mode="markdown",
                                    disable_web_page_preview=True,
                                )
                            except:
                                functionsLogger.error(
                                    f"ERRO: não foi possível enviar mensagem para {chat.id} ({chat.title})."
                                )

                                alertMessage = ""
                                alertCounter = 1

                        alertObj = models.Alert(alertDict=alert)
                        alertMessage += alertObj.get_alert_message(city)
                        functionsLogger.info(
                            f"-- Notifying chat {chat.id} about alert {alert['alertID']}... --"
                        )

                        models.INMETBotDB.alertsCollection.update_one(
                            {"alertID": alert["alertID"]},
                            {"$addToSet": {"notifiedChats": chat.id}},
                        )
                        alertCounter += 1

                    # "Footer" message after all alerts
                    alertMessage += (
                        f"\nMais informações em {bot_messages.ALERTAS_URL}."
                    )

                    try:
                        context.bot.send_message(
                            chat_id=chat.id,
                            text=alertMessage,
                            parse_mode="markdown",
                            disable_web_page_preview=True,
                        )
                    except:
                        functionsLogger.error(
                            f"ERRO: não foi possível enviar mensagem para {chat.id} ({chat.title}). Removendo chat do BD..."
                        )
                        models.INMETBotDB.subscribedChatsCollection.delete_one(
                            {"chatID": chat.id}
                        )

            context.bot.delete_message(
                chat_id=checkingForSubscribed.chat.id, message_id=checkingForSubscribed.message_id
            )


@run_async
@bot_utils.ignore_users
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
        functionsLogger.info("Successful GET request to reverse geocoding API!")

        # Get data from response
        responseData = response.json()
        functionsLogger.debug(f"reverseGeocode json: {responseData}")
        state = responseData["nearest"]["state"]

        if state == "BR":
            city = responseData["nearest"]["region"]

            # Include moderate alerts
            alerts = list(models.INMETBotDB.alertsCollection.find({"cities": city}))
            return check_and_send_alerts_warning(update, context, alerts, city)
        else:
            alertMessage = bot_messages.locationOutsideBrazil
    else:
        functionsLogger.error("Failed GET request to reverse geocoding API.")
        alertMessage = bot_messages.unableCheckAlertsLocation

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=alertMessage,
        parse_mode="markdown",
    )


@bot_utils.log_command
@bot_utils.ignore_users
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


@run_async
@bot_utils.ignore_users
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
    functionsLogger.info(f"Deleted {alertsMapPath}.")


@bot_utils.log_command
@bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_subscribe_alerts(update, context):
    """Subscribe chat and/or CEP."""

    textArgs = update.message.text.split(" ")

    try:
        cep = bot_utils.parse_CEP(update, context, cepRequired=False)
    except Exception:
        subscribeMessage = bot_messages.invalidZipCode.format(textArgs=textArgs[0])
    else:
        chat = models.create_chat_obj(update)
        subscribeResult = chat.subscribe_chat(cep)
        subscribeMessage = chat.get_subscribe_message(subscribeResult, textArgs, cep)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=subscribeMessage,
        parse_mode="markdown",
    )


@bot_utils.log_command
@bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_unsubscribe_alerts(update, context):
    """Unsubscribe chat and/or CEP."""

    textArgs = update.message.text.split(" ")

    try:
        cep = bot_utils.parse_CEP(update, context, cepRequired=False)
    except Exception:
        unsubscribeMessage = bot_messages.invalidZipCode.format(textArgs=textArgs[0])
    else:
        chat = models.create_chat_obj(update)
        unsubscribeResult = chat.unsubscribe_chat(cep)
        unsubscribeMessage = chat.get_unsubscribe_message(unsubscribeResult, cep)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=unsubscribeMessage,
        parse_mode="markdown",
    )


@run_async
@bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_chat_subscription_status(update, context):
    """Send chat's subscription status."""

    chat = models.create_chat_obj(update=update)

    subscriptionStatus = chat.check_subscription_status()
    subscriptionStatusMessage = chat.get_subscription_status_message(subscriptionStatus)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=subscriptionStatusMessage,
        parse_mode="markdown",
    )


@run_async
@bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_deactivate(update, context):
    """ Set chat's activated status to False. """

    chat = models.create_chat_obj(update=update)
    deactivateMessage = chat.toggle_subscription_callback(chat.deactivate)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=deactivateMessage,
        parse_mode="markdown",
    )


@run_async
@bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_activate(update, context):
    """ Set chat's activated status to True. """

    chat = models.create_chat_obj(update=update)
    activateMessage = chat.toggle_subscription_callback(chat.activate)

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=activateMessage,
        parse_mode="markdown",
    )


@run_async
@bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_chat_toggle_activated(update, context):
    """ Toggle chat's activated status """

    chat = models.create_chat_obj(update=update)
    toggleMessage = chat.toggle_subscription_callback(chat.toggle_activated)

    try:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=toggleMessage,
            parse_mode="markdown",
        )
    except:
        pass


@run_async
@bot_utils.log_command
@bot_utils.ignore_users
@bot_utils.send_typing_action
def cmd_forecast(update, context):
    """Fetch and send weather forecast for the next 3 days for given CEP (zip code)."""

    functionsLogger.debug("Getting weather forecast by CEP (zip code)...")
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
            f"{APIBaseURL}/previsao/{IBGECode}", headers=headers, allow_redirects=False,
        )
        if response.status_code == 200:
            functionsLogger.info("Successful GET request to APIPREVMET3 endpoint!")
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
        functionsLogger.warning(
            f'{cepError} on cmd_forecast. Message text: "{update.message.text}"'
        )
        message = bot_messages.invalidZipCode.format(textArgs=textArgs[0])
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=message,
            parse_mode="markdown",
        )


@bot_utils.log_command
@bot_utils.send_typing_action
def broadcast_message_subscribed_chats(update, context, message):
    """Send message to all subscribed chats."""

    chats = list(models.INMETBotDB.subscribedChatsCollection.find())
    pprint.pprint(chats)
    for document in chats:
        time.sleep(2)
        context.bot.send_message(
            chat_id=document['chatID'],
            text=message,
            parse_mode="markdown",
        )


@run_async
@bot_utils.log_command
@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo(update, context):
    """Send default Sorrizo Ronaldo video."""

    # Send video to replied message if it exists
    replyID = None
    if update.message.reply_to_message:
        replyID = update.message.reply_to_message.message_id

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=bot_messages.sorrizoChegou,
        parse_mode="markdown",
    )
    context.bot.send_video(
        chat_id=update.effective_chat.id,
        video="BAACAgEAAxkBAAPmXkSUcBDsVM300QABV4Oerb9PcUx3AAL8AAODXihGe5y1jndyb80YBA",
        reply_to_message_id=replyID,
    )


@run_async
@bot_utils.log_command
@bot_utils.send_upload_video_action
def cmd_sorrizoronaldo_will_rock_you(update, context):
    """Send "We Will Rock You" Sorrizo Ronaldo video variation."""

    # Send video to replied message if it exists
    replyID = None
    if update.message.reply_to_message:
        replyID = update.message.reply_to_message.message_id

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=bot_messages.sorrizoQueen,
        parse_mode="markdown",
    )
    context.bot.send_video(
        chat_id=update.effective_chat.id,
        video="BAACAgEAAxkBAAICZ15HDelLB1IH1i3hTB8DaKwWlyPMAAJ8AAPfLzhG0hgf8dxd_zQYBA",
        reply_to_message_id=replyID,
    )


@run_async
@bot_utils.log_command
@bot_utils.send_typing_action
def cmd_update_alerts(update, context):
    """Update alerts from database. (DEBUGGING)"""

    delete_past_alerts_routine()
    parse_alerts_routine()
    notify_chats_routine()


@run_async
def error(update, context):
    """Log errors caused by Updates."""
    functionsLogger.error('Update "%s" caused error "%s"', update, context.error)
