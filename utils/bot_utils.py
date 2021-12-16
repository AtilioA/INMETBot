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

import sys

sys.path.append(sys.path[0] + "/..")

SALT = str(uuid.uuid4())
utilsLogger = logging.getLogger(__name__)
utilsLogger.setLevel(logging.DEBUG)

MIN_VPR_IMAGES = 2
DEFAULT_VPR_IMAGES = 13  # 2 hours of images
MAX_VPR_IMAGES = 72  # 12 hours of images

IGNORED_USERS = [1528688653, 1149342586]


# Decorator to ignore a user
def ignore_users_decorator(logger):
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            if update.message.from_user.id in IGNORED_USERS:
                return
            else:
                return func(update, context, *args, **kwargs)

            debugMessage = f"Ignoring {update.message.from_user.id}"

            logger.debug(debugMessage)

            context.bot.send_message(
                chat_id="-1001361751085", text=debugMessage,
            )

            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


# Decorator to log user interaction
def log_command_decorator(logger):
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            if update.message.from_user.username:
                hashed_username = hashlib.sha512(update.message.from_user.username.encode('utf-8') + SALT.encode('utf-8')).hexdigest()
            else:
                hashed_username = hashlib.sha512(update.message.from_user.name.encode('utf-8') + SALT.encode('utf-8')).hexdigest()

            debugMessage = f"\"'{update.message.text}' from `{hashed_username[:6]}` ({update.message.chat.type})\""

            logger.debug(debugMessage)

            context.bot.send_message(
                chat_id="-1001361751085", text=debugMessage, parse_mode="markdown",
            )

            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


# Decorators to simulate user feedback
def send_action(action):
    """Send `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(
                chat_id=update.effective_message.chat_id, action=action
            )
            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


log_command = log_command_decorator(utilsLogger)
ignore_users = ignore_users_decorator(utilsLogger)
send_typing_action = send_action(telegram.ChatAction.TYPING)
send_upload_photo_action = send_action(telegram.ChatAction.UPLOAD_PHOTO)
send_upload_video_action = send_action(telegram.ChatAction.UPLOAD_VIDEO)
send_upload_document_action = send_action(telegram.ChatAction.UPLOAD_DOCUMENT)


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


def get_vpr_images_data(data, nImages, dayNow, nImagesForYesterday=None, dataYesterday=None):
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

def get_vpr_gif(data, nImages, dayNow, nImagesForYesterday=None, dataYesterday=None):
    vprResponse = get_vpr_images_data(data, nImages, dayNow, nImagesForYesterday, dataYesterday)

    create_gif_vpr_data(vprResponse, nImages)

    return gifFilename


def parse_n_images_input(update, context):
    """Parse input for VPR gifs. Input must exist and be numeric.

    Returns
    --------
    (nImages, nImagesMessage)

    nImages : int
        Number of images to be fetched.
    nImagesMessage : str
        Message to be sent by the bot.
    """

    def get_n_images_and_message(nImages=None):
        """Process nImages input and determine nImagesMessage for vpr_gif function."""

        if nImages:
            if nImages > MAX_VPR_IMAGES:
                nImagesMessage = f"❕O número máximo de imagens é {MAX_VPR_IMAGES} (12 horas de imagens)! Utilizarei-o no lugar de {nImages}."
                nImages = MAX_VPR_IMAGES
            elif nImages < MIN_VPR_IMAGES:
                nImagesMessage = f"❕O número mínimo de imagens é {MIN_VPR_IMAGES}! Utilizarei-o no lugar de {nImages}."
                nImages = MIN_VPR_IMAGES
            else:
                nImagesMessage = None
            return (nImages, nImagesMessage)

        nImagesMessage = f"""❕Não foi possível identificar o intervalo. Utilizarei o padrão, que é {DEFAULT_VPR_IMAGES} (exibe cerca de 2 horas de imagens).\nDica: você pode estipular quantas imagens buscar. Ex: `/nuvens 4` buscará as 4 últimas imagens."""  # noqa
        nImages = DEFAULT_VPR_IMAGES

        return (nImages, nImagesMessage)

    text = update.message.text

    try:
        nImages = context.args[0]
        try:
            nImages = int(float(nImages))
            nImages, nImagesMessage = get_n_images_and_message(nImages)
        except ValueError:
            context.bot.send_message(
                chat_id=update.message.chat.id,
                text=f"❌ Não entendi!\nExemplo:\n`/vpr_gif 3` ou `/nuvens 3`",
                reply_to_message_id=update.message.message_id,
                parse_mode="markdown",
            )
            return None
    except (IndexError, AttributeError):
        nImages, nImagesMessage = get_n_images_and_message(None)
        utilsLogger.warning(f'No input in parse_n_images_input. Message text: "{text}"')

    if nImagesMessage:
        context.bot.send_message(
            chat_id=update.message.chat.id,
            text=nImagesMessage,
            reply_to_message_id=update.message.message_id,
            parse_mode="markdown",
        )

    return nImages


def parse_CEP(update, context, cepRequired=True):
    """Parse CEP from user's text message."""

    text = update.message.text

    try:
        cep = (
            context.args[0].strip().replace("-", "")
        )  # Get string after "/alertas_CEP"
    except (TypeError, IndexError):  # No number after /command
        utilsLogger.warning(f'No input in parse_CEP. Message text: "{text}"')
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
