import logging
from functools import wraps
import telegram
import models
from scrap_satelites import MIN_VPR_IMAGES, DEFAULT_VPR_IMAGES, MAX_VPR_IMAGES

utilsLogger = logging.getLogger(__name__)
utilsLogger.setLevel(logging.DEBUG)


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


def is_group_or_channel(chat_id):
    """ Check if chat_id represents a group or channel. """

    if chat_id < 0:
        return True
    else:
        return False


# MESSAGES
def determine_severity_emoji(severity):
    """ Determine emoji for alert message and return it. """

    if severity == "Perigo Potencial":
        return "⚠️"  # Yellow alert
    elif severity == "Perigo":
        return "🔶"  # Orange alert
    else:
        return "🚨"  # Red alert


def get_alert_message(alert, location=None):
    """ Create alert message string from alert object and return it. """

    severityEmoji = determine_severity_emoji(alert.severity)
    area = ','.join(alert.area)
    formattedStartDate = alert.startDate.strftime("%d/%m/%Y %H:%M")
    formattedEndDate = alert.endDate.strftime("%d/%m/%Y %H:%M")

    if location:
        header = f"{severityEmoji} *{alert.event[:-1]} para {location}.*"
    else:
        header = f"{severityEmoji} *{alert.event}*"

    messageString = f"""
{header}

        *Áreas afetadas*: {area}.
        *Vigor*: De {formattedStartDate} a {formattedEndDate}.
        {alert.description}
"""
    return messageString


def parse_n_images_input(update, context, text):
    """ Parse input for VPR gifs. Input must exist and be numeric.

        Return:
            Number of images if successful, None otherwise.
    """

    try:
        nImages = text.split(' ')[1]
        if nImages.isnumeric():
            nImages, nImagesMessage = get_n_images_and_message(nImages)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Não entendi!\nExemplo:\n`/vpr_gif 3` ou `/nuvens 3`", reply_to_message_id=update.message.message_id, parse_mode="markdown")
            return None
    except IndexError as indexE:
        nImages, nImagesMessage = get_n_images_and_message(None)
        utilsLogger.warning(f"{indexE} in parse_n_images_input. Message text: \"{text}\"")

    if nImagesMessage:
        context.bot.send_message(chat_id=update.effective_chat.id, text=nImagesMessage, reply_to_message_id=update.message.message_id, parse_mode="markdown")

    return nImages


def get_n_images_and_message(nImages=None):
    if nImages:
        nImages = int(nImages)
        if nImages > MAX_VPR_IMAGES:
            nImagesMessage = f"❕O número máximo de imagens é {MAX_VPR_IMAGES}! Utilizarei-o no lugar de {nImages}."
            nImages = MAX_VPR_IMAGES
        elif nImages < MIN_VPR_IMAGES:
            nImagesMessage = f"❕O número mínimo de imagens é {MIN_VPR_IMAGES}! Utilizarei-o no lugar de {nImages}."
            nImages = MIN_VPR_IMAGES
        else:
            nImagesMessage = None
    else:
        nImagesMessage = f"""❕Não foi possível identificar o intervalo. Utilizarei o padrão, que é {DEFAULT_VPR_IMAGES} (exibe 2 horas de imagens).
Dica: você pode estipular quantas imagens buscar. Ex: `/nuvens 4` buscará as 4 últimas imagens."""
        nImages = DEFAULT_VPR_IMAGES

    return (nImages, nImagesMessage)


def get_subscribe_message(update, cep, textArgs):
    # Check if chat is subscribed and cep was given
    if models.is_subscribed(update.effective_chat.id) and not cep:
        if is_group_or_channel(update.effective_chat.id):
            subscribeMessage = f"❕O grupo já está inscrito.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva o grupo com /desinscrever."
        else:
            subscribeMessage = f"❕Você já está inscrito.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva-se com /desinscrever."
    elif models.is_subscribed(update.effective_chat.id) and cep:
        subscribed = models.subscribe_chat(update.effective_chat.id, cep)
        if subscribed:
            subscribeMessage = f"🔔 Inscrevi o CEP {cep}.\nDesinscreva CEPs: `/desinscrever {cep}`."
        else:
            subscribeMessage = f"❕O CEP {cep} já está inscrito.\nDesinscreva CEPs: `{textArgs[0]} {cep}`.\nDesinscreva o grupo com /desinscrever."
    elif not models.is_subscribed(update.effective_chat.id) and cep:
        if is_group_or_channel(update.effective_chat.id):
            utilsLogger.debug("Subscribing group")
            models.subscribe_chat(update.effective_chat.id, cep)
            subscribeMessage = f"🔔 Inscrevi o grupo e o CEP {cep}.\nDesinscreva o grupo com /desinscrever."
        else:
            utilsLogger.debug("Subscribing private")
            models.subscribe_chat(update.effective_chat.id, cep)
            subscribeMessage = f"🔔 Inscrevi você e o CEP {cep}.\nDesinscreva-se com /desinscrever."
    else:  # Chat not subscribed and cep not given
        if is_group_or_channel(update.effective_chat.id):
            utilsLogger.debug("Subscribing group")
            models.subscribe_chat(update.effective_chat.id, cep)
            subscribeMessage = f"🔔 Inscrevi o grupo.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva o grupo com /desinscrever."
        else:
            utilsLogger.debug("Subscribing private")
            models.subscribe_chat(update.effective_chat.id, cep)
            subscribeMessage = f"🔔 Inscrevi você.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva-se com /desinscrever."

    return subscribeMessage


def get_unsubscribe_message(update, cep, textArgs):
    # Check if chat is subscribed and cep was given
    if models.is_subscribed(update.effective_chat.id) and not cep:
        models.unsubscribe_chat(update.effective_chat.id, cep)
        if is_group_or_channel(update.effective_chat.id):
            unsubscribed = models.unsubscribe_chat(update.effective_chat.id, cep)
            unsubscribeMessage = "🔕 O grupo foi desinscrito dos alertas.\nInscreva o grupo com /inscrever."
        else:
            unsubscribed = models.unsubscribe_chat(update.effective_chat.id, cep)
            unsubscribeMessage = "🔕 Você foi desinscrito dos alertas.\nInscreva-se com /inscrever."
    elif models.is_subscribed(update.effective_chat.id) and cep:
        unsubscribed = models.unsubscribe_chat(update.effective_chat.id, cep)
        if unsubscribed:
            unsubscribeMessage = f"🔕 Desinscrevi o CEP {cep}."
        else:
            unsubscribeMessage = f"❌ O CEP {cep} não está inscrito.\nAdicione CEPs: `/inscrever {cep}`"
    else:  # Chat not subscribed
        if is_group_or_channel(update.effective_chat.id):
            unsubscribeMessage = "❌ O grupo não está inscrito nos alertas.\nInscreva-o com /inscrever."
        else:
            unsubscribeMessage = "❌ Você não está inscrito nos alertas.\nInscreva-se com /inscrever."
