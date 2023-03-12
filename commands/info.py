from telegram.ext.dispatcher import run_async

from utils import bot_messages, bot_utils, decorators


@run_async
# @decorators.ignore_users
@decorators.log_command
@decorators.send_typing_action
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
# @decorators.ignore_users
@decorators.log_command
@decorators.send_typing_action
def cmd_start(update, context):
    """Send the start message to the user."""

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.message.message_id,
        text=bot_messages.welcomeMessage,
        parse_mode="markdown",
    )
