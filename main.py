# Webserver to prevent the bot from sleeping
from utils import webserver
import os
import logging
import time
import schedule
from threading import Thread

from bot_config import updater
import bot_handlers  # noqa (ignore linter warning)
from bot_routines import (
    parse_alerts_routine,
    delete_past_alerts_routine,
    notify_chats_routine,
)

# ROUTINES_INTERVAL = 60

# Enable logging
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    filename="bot.log",
    level=logging.DEBUG,
)


# Thread for running routines periodically
class RoutinesThread(Thread):
    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(60)


schedule.every().hour.do(parse_alerts_routine)
schedule.every().hour.do(delete_past_alerts_routine)
schedule.every().hour.do(notify_chats_routine)


def main():
    updater.start_polling()

    # Start routines thread
    fCheckAlert = RoutinesThread()
    fCheckAlert.daemon = True
    fCheckAlert.start()

    # Start web server
    port = os.environ.get("PORT", 2832)
    webserver.run(host="0.0.0.0", port=int(port))

    # Run the bot until Ctrl-C is pressed
    updater.idle()


if __name__ == "__main__":
    main()
