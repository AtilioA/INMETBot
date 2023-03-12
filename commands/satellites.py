
import time
import os
import logging

import telegram
import arrow
import requests
import fgrequests
from telegram.ext.dispatcher import run_async

from utils import bot_messages, bot_utils


satellitesFunctionsLogger = logging.getLogger(__name__)
satellitesFunctionsLogger.setLevel(logging.DEBUG)

@run_async
# @bot_utils.ignore_users
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

        hourLastImage = arrow.get(vprData["hora"], "HH:mm").to("-03:00").format("HH:mm")
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
                satellitesFunctionsLogger.info("Successful GET request to API VPR endpoint!")

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
def send_vpr_video(
    update,
    context,
    vprVideoPath,
    nImages,
    waitMessage,
    nImagesMessage,
    gifTimeBoundariesDict,
):
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
    satellitesFunctionsLogger.info(f"Deleted {vprVideoPath}.")


@run_async
# @bot_utils.ignore_users
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
            satellitesFunctionsLogger.info("Successful GET request to API VPR endpoint!")
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
                "firstImage": arrow.get(vprResponse[-1]["hora"], "HH:mm")
                .to("-03:00")
                .format("HH:mm"),
                "lastImage": arrow.get(vprResponse[0]["hora"], "HH:mm")
                .to("-03:00")
                .format("HH:mm"),
            }
            gifFilename = bot_utils.create_gif_vpr_data(vprResponse, nImages)

            return send_vpr_video(
                update,
                context,
                gifFilename,
                nImages,
                waitMessage,
                nImagesMessage,
                gifTimeBoundariesDict,
            )
        else:
            satellitesFunctionsLogger.error("Failed GET request to VPR API.")
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
# @bot_utils.ignore_users
@bot_utils.log_command
@bot_utils.send_upload_photo_action
def cmd_acumulada(update, context):
    """Fetch and send accumulated precipitation within given interval satellite image to the user."""

    try:
        satellitesFunctionsLogger.debug("Getting acumulada images...")
        acumuladaWarnMessage = ""

        # Parse input
        try:
            inputInterval = int(context.args[0])
        except IndexError:
            satellitesFunctionsLogger.warning(
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
            satellitesFunctionsLogger.info("Successful GET request to INMET's APIPREC endpoint!")

            # Get data from response
            data = response.json()

            # Adjust input to available intervals
            availableIntervals = [1, 3, 5, 10, 15, 30, 90]
            caption = ""
            interval = inputInterval
            if interval in availableIntervals:
                caption = f"Precipitação acumulada nos últimos {interval} dias"
                # indexInterval = availableIntervals.index(interval)
            else:
                # Get closest value to input if it isn't in the interval
                absoluteDiff = lambda listValue: abs(listValue - interval)
                interval = min(availableIntervals, key=absoluteDiff)

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
            satellitesFunctionsLogger.error("Failed GET request to INMET's APIPREC endpoint.")
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
