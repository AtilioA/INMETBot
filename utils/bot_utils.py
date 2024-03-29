import os
import logging
from io import BytesIO
import uuid
import base64
import hashlib
from functools import wraps
import imageio
import telegram
from PIL import Image
import arrow
import fgrequests
import pycep_correios as pycep

from utils import bot_messages
from models.Alert import Alert


utilsLogger = logging.getLogger(__name__)
utilsLogger.setLevel(logging.DEBUG)

# Minimum number of images to be fetched from the API when creating GIFs
MIN_VPR_IMAGES = 2
DEFAULT_VPR_IMAGES = 13  # ~2 hours of images
MAX_VPR_IMAGES = 72  # ~12 hours of images



def loadB64ImageToMemory(base64String):
    # Decode Base64 image
    base64data = base64String[21:]  # Remove string header
    image = Image.open(BytesIO(base64.b64decode(base64data)))

    # Save image to memory
    bytesIOImage = BytesIO()
    bytesIOImage.name = "image.jpeg"
    image.save(bytesIOImage, "JPEG")
    bytesIOImage.seek(0)

    return bytesIOImage


def get_vpr_images_data(
    data, nImages, dayNow, nImagesForYesterday=None, dataYesterday=None
):
    regiao = "BR"
    APIBaseURL = "https://apisat.inmet.gov.br"

    URLsToBeRequested = []

    for hourToday in data[:nImages]:
        URLsToBeRequested.append(
            f"{APIBaseURL}/GOES/{regiao}/VP/{dayNow}/{hourToday['sigla']}"
        )

    if dataYesterday:
        nImages = nImages + nImagesForYesterday

        for hour in dataYesterday[:nImagesForYesterday]:
            URLsToBeRequested.append(
                f"{APIBaseURL}/GOES/{regiao}/VP/{arrow.utcnow().shift(days=-1).format('YYYY-MM-DD')}/{hour['sigla']}"
            )

    responses = list(
        filter(lambda x: x.status_code == 200, fgrequests.build(URLsToBeRequested))
    )
    responseData = [entry.json() for entry in responses]

    return responseData


def create_gif_vpr_data(data, nImages):
    readImages = []
    for entry in reversed(data[:nImages]):
        loadedImg = loadB64ImageToMemory(entry["base64"])
        readImages.append(imageio.imread(loadedImg))

    uniqueID = uuid.uuid4().hex
    gifFilename = os.path.join("tmp", f"VPR_{uniqueID}.mp4")

    kargs = {"fps": 10, "macro_block_size": None}
    imageio.mimsave(f"{gifFilename}", readImages, "MP4", **kargs)

    return gifFilename


# Unused
def get_vpr_gif(data, nImages, dayNow, nImagesForYesterday=None, dataYesterday=None):
    vprResponse = get_vpr_images_data(
        data, nImages, dayNow, nImagesForYesterday, dataYesterday
    )

    return create_gif_vpr_data(vprResponse, nImages)


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


def parse_n_images_input(update, context):
    """Parse input for VPR gifs. Input must exist and be numeric.

    Returns
    --------
    (nImages, nImagesText)

    nImages : int
        Number of images to be fetched.
    nImagesText : str
        Message to be sent by the bot.
    """

    def get_n_images_and_message(nImages=None):
        """Process nImages input and determine nImagesText for vpr_gif function."""

        if nImages:
            if nImages > MAX_VPR_IMAGES:
                nImagesText = f"❕O número máximo de imagens é {MAX_VPR_IMAGES} (12 horas de imagens)! Utilizarei-o no lugar de {nImages}."
                nImages = MAX_VPR_IMAGES
            elif nImages < MIN_VPR_IMAGES:
                nImagesText = f"❕O número mínimo de imagens é {MIN_VPR_IMAGES}! Utilizarei-o no lugar de {nImages}."
                nImages = MIN_VPR_IMAGES
            else:
                nImagesText = None
            return (nImages, nImagesText)

        # TODO: Move to bot_messages.py
        nImagesText = f"""❕Não foi possível identificar o intervalo. Utilizarei o padrão, que é {DEFAULT_VPR_IMAGES} (exibe cerca de 2 horas de imagens).\nDica: você pode estipular quantas imagens buscar. Ex: `/nuvens 4` buscará as 4 últimas imagens."""
        nImages = DEFAULT_VPR_IMAGES

        return (nImages, nImagesText)

    text = update.message.text

    try:
        nImagesMessage = None
        nImages = context.args[0]
        try:
            nImages = int(float(nImages))
            nImages, nImagesText = get_n_images_and_message(nImages)
        except ValueError:
            context.bot.send_message(
                chat_id=update.message.chat.id,
                text=f"❌ Não entendi!\nExemplo:\n`/vpr_gif 3` ou `/nuvens 3`",
                reply_to_message_id=update.message.message_id,
                parse_mode="markdown",
            )
            return None
    except (IndexError, AttributeError):
        nImages, nImagesText = get_n_images_and_message(None)
        utilsLogger.warning(f'No input in parse_n_images_input. Message text: "{text}"')

    if nImagesText:
        nImagesMessage = context.bot.send_message(
            chat_id=update.message.chat.id,
            text=nImagesText,
            reply_to_message_id=update.message.message_id,
            parse_mode="markdown",
        )

    return (nImages, nImagesMessage)


def enforce_CEP(update, context, cepRequired=True):
    """Parse CEP from user's text message."""

    text = update.message.text

    try:
        cep = (
            context.args[0].strip().replace("-", "")
        )  # Get string after "/alertas_CEP"
    except (TypeError, IndexError):  # No number after /command
        utilsLogger.warning(f'No input in enforce_CEP. Message text: "{text}"')
        message = f"❌ *CEP não informado*!\nExemplo:\n`{text.split(' ')[0]} 29075-910`"
    else:
        if cep and not pycep.validar_cep(cep):
            message = f"❌ *CEP inválido/não existe*!\nExemplo:\n`{text.split(' ')[0]} 29075-910`"
            utilsLogger.warning(f"CEP inválido: {cep}")
            # return message
            raise Exception
        else:
            return cep

    if cepRequired:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_to_message_id=update.message.message_id,
            text=message,
            parse_mode="markdown",
        )
        return None
