import os
import logging
from io import BytesIO
import uuid
import base64
from functools import wraps
import imageio
import telegram
from PIL import Image

import sys
sys.path.append(sys.path[0] + "/..")

utilsLogger = logging.getLogger(__name__)
utilsLogger.setLevel(logging.DEBUG)

MIN_VPR_IMAGES = 2
DEFAULT_VPR_IMAGES = 9  # 2 hours of images
MAX_VPR_IMAGES = 48  # 12 hours of images


# Decorators to simulate user feedback
def send_action(action):
    """Send `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context, *args, **kwargs)
        return command_func

    return decorator


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
    bytesIOImage.name = 'image.jpeg'
    image.save(bytesIOImage, 'JPEG')
    bytesIOImage.seek(0)

    return bytesIOImage


def get_vpr_gif(data, nImages):
    readImages = []
    for entry in reversed(data[:nImages]):
        loadedImg = loadB64ImageToMemory(entry['base64'])
        readImages.append(imageio.imread(loadedImg))

    uniqueID = uuid.uuid4().hex
    gifFilename = os.path.join("tmp", f"VPR_{uniqueID}.mp4")

    kargs = {'fps': 10, 'macro_block_size': None}
    imageio.mimsave(f'{gifFilename}', readImages, 'MP4', **kargs)


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

        nImagesMessage = f"""❕Não foi possível identificar o intervalo. Utilizarei o padrão, que é {DEFAULT_VPR_IMAGES} (exibe 2 horas de imagens).\nDica: você pode estipular quantas imagens buscar. Ex: `/nuvens 4` buscará as 4 últimas imagens."""  # noqa
        nImages = DEFAULT_VPR_IMAGES

        return (nImages, nImagesMessage)

    text = update.message.text

    try:
        nImages = context.args[0]
        try:
            nImages = int(float(nImages))
            nImages, nImagesMessage = get_n_images_and_message(nImages)
        except ValueError:
            context.bot.send_message(chat_id=update.message.chat.id, text=f"❌ Não entendi!\nExemplo:\n`/vpr_gif 3` ou `/nuvens 3`",
                                     reply_to_message_id=update.message.message_id, parse_mode="markdown")
            return None
    except (IndexError, AttributeError):
        nImages, nImagesMessage = get_n_images_and_message(None)
        utilsLogger.warning(f"No input in parse_n_images_input. Message text: \"{text}\"")

    if nImagesMessage:
        context.bot.send_message(chat_id=update.message.chat.id, text=nImagesMessage,
                                 reply_to_message_id=update.message.message_id, parse_mode="markdown")

    return nImages
