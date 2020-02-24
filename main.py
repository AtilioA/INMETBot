import os
from utils import webserver
import logging
import time
import schedule
from threading import Thread
# Webserver to prevent the bot from sleeping
from bottle import route, run

from bot_config import updater
import bot_handlers  # noqa (ignore linter warning)
from bot_routines import parse_alerts_routine, delete_past_alerts_routine, notify_chats_routine

ROUTINES_INTERVAL = 30

# Enable logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='requests.log',
                    level=logging.DEBUG)


@route('/')
def index():
    return '200'


# Thread for running routines periodically
class RoutinesThread(Thread):
    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)


schedule.every(ROUTINES_INTERVAL).minutes.do(parse_alerts_routine)
schedule.every(ROUTINES_INTERVAL).minutes.do(delete_past_alerts_routine)
schedule.every(ROUTINES_INTERVAL).minutes.do(notify_chats_routine)


def main():
    updater.start_polling()

    # Start threads
    fCheckAlert = RoutinesThread()
    fCheckAlert.daemon = True
    fCheckAlert.start()

    port = os.environ.get('PORT', 2832)
    run(host='0.0.0.0', port=int(port))

    # Run the bot until Ctrl-C is pressed
    updater.idle()


if __name__ == "__main__":
    main()
