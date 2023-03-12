import traceback
import logging
import uuid
import hashlib
from functools import wraps
import telegram

# Salt used to hash usernames
SALT = str(uuid.uuid4())


IGNORED_USERS = []

decoratorsLogger = logging.getLogger(__name__)
decoratorsLogger.setLevel(logging.DEBUG)

# Decorator to ignore a user
def ignore_users_decorator(logger):
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            if update.message.from_user.id in IGNORED_USERS:
                logger.debug(f"Ignoring {update.message.from_user.id}")
                # context.bot.send_message(
                #     chat_id="-1001361751085",
                #     text=debugMessage,
                # )
                return
            else:
                return func(update, context, *args, **kwargs)

        return command_func

    return decorator


# Decorator to log user interaction
def log_command_decorator(logger):
    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            try:
                if update.message.from_user.username:
                    hashed_username = hashlib.sha512(
                        update.message.from_user.username.encode("utf-8")
                        + SALT.encode("utf-8")
                    ).hexdigest()
                else:
                    hashed_username = hashlib.sha512(
                        update.message.from_user.name.encode("utf-8")
                        + SALT.encode("utf-8")
                    ).hexdigest()

                debugMessage = f"\"'{update.message.text}' from `{hashed_username[:6]}` ({update.message.chat.type})\""

                logger.debug(debugMessage.replace("`", ""))

                # context.bot.send_message(
                #     chat_id="-1001361751085",
                #     text=debugMessage,
                #     parse_mode="markdown",
                # )

                return func(update, context, *args, **kwargs)
            except Exception as e:
                decoratorsLogger.error(e)
                # traceback.print_exc()

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


log_command = log_command_decorator(decoratorsLogger)
ignore_users = ignore_users_decorator(decoratorsLogger)
send_typing_action = send_action(telegram.ChatAction.TYPING)
send_upload_photo_action = send_action(telegram.ChatAction.UPLOAD_PHOTO)
send_upload_video_action = send_action(telegram.ChatAction.UPLOAD_VIDEO)
send_upload_document_action = send_action(telegram.ChatAction.UPLOAD_DOCUMENT)
