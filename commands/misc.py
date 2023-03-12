import time
import pprint
import logging

from telegram.ext.dispatcher import run_async

from models.db import INMETBotDB
from models.Alert import Alert
from models.Chat import Chat

from bot_routines import (
    delete_past_alerts_routine,
    parse_alerts_routine,
)

from utils import bot_messages, bot_utils


miscFunctionsLogger = logging.getLogger(__name__)
miscFunctionsLogger.setLevel(logging.DEBUG)


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
# @bot_utils.ignore_users
def catch_all_if_private(update, context):
    """Reply to any message not handled (if not sent to a group/channel)."""

    chat = Chat.create_chat_obj(update)

    if chat.type == "private":
        miscFunctionsLogger.debug(
            f"catch_all: {update.message.chat.type} to @{update.message.chat.username}"
        )
        return send_instructions_message(update, context)


@bot_utils.log_command
@bot_utils.send_typing_action
def broadcast_message_subscribed_chats(update, context, message):
    """Send message to all subscribed chats."""

    chats = list(INMETBotDB.subscribedChatsCollection.find())
    pprint.pprint(chats)
    for document in chats:
        time.sleep(2)
        context.bot.send_message(
            chat_id=document["chatID"],
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

    miscFunctionsLogger.info("Updating alerts...")
    delete_past_alerts_routine()
    parse_alerts_routine()


@run_async
def error(update, context):
    """Log errors caused by Updates."""
    miscFunctionsLogger.error('Update "%s" caused error "%s"', update, context.error)
