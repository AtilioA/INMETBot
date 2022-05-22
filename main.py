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
    ping,
)

ROUTINES_INTERVAL = 15

# Enable logging
logging.basicConfig(
    format="%(asctime)s %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    filename="bot.log",
    level=logging.DEBUG,
)


try:
    schedule.every(ROUTINES_INTERVAL).minutes.do(delete_past_alerts_routine)
    schedule.every(ROUTINES_INTERVAL).minutes.do(parse_alerts_routine)
    schedule.every(ROUTINES_INTERVAL).minutes.do(notify_chats_routine)

    for i in range(12, 24):
        schedule.every().day.at(f"{i}:00").do(
            ping, URL="https://covid19nowbot.herokuapp.com/"
    )
except:
    logging.exception("Error in main routine.")
    pass


# Thread for running routines periodically
class RoutinesThread(Thread):
    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    updater.start_polling()

    # Start routines thread
    fRoutines = RoutinesThread()
    fRoutines.daemon = True
    fRoutines.start()

    # Run the bot until Ctrl-C is pressed
    updater.idle()


if __name__ == "__main__":
    main()
