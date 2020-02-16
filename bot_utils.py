import telegram
from functools import wraps

# Decorators to simulate user feedback
def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context,  *args, **kwargs)
        return command_func

    return decorator

send_typing_action = send_action(telegram.ChatAction.TYPING)
send_upload_photo_action = send_action(telegram.ChatAction.UPLOAD_PHOTO)
send_upload_video_action = send_action(telegram.ChatAction.UPLOAD_VIDEO)
send_upload_document_action = send_action(telegram.ChatAction.UPLOAD_DOCUMENT)


def determine_severity_emoji(severity):
    """ Determine emoji for alert message. """

    if severity == "Perigo Potencial":
        return "⚠️"  # Yellow alert
    elif severity == "Perigo":
        return "🔶"  # Orange alert
    else:
        return "🚨"  # Red alert


def get_alert_message(alert, location=None):
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


def is_group_or_channel(chat_id):
    """ Check if current chat is group or channel. """

    if update.effective_chat.id < 0:
        return True
    else:
        return False
