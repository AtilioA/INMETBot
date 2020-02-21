# Webserver to prevent the bot from sleeping
import web
import webserver
import logging
import time
import schedule
from threading import Thread

from bot_config import updater
import bot_handlers  # noqa (ignore linter warning)
from bot_routines import parse_alerts_routine, delete_past_alerts_routine, notify_chats_routine

ROUTINES_INTERVAL = 30

# Enable logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='requests.log',
                    level=logging.DEBUG)


# Thread for the web server
class WebServerThread(Thread):
    def run(self):
        app = web.application(webserver.urls, globals())
        app.run()


# Thread for running routines periodically
class RoutinesThread(Thread):
    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)


# To guarantee a stable execution schedule
# def run_threaded(job_function):
#     jobThread = Thread(target=job_function)
#     jobThread.start()


schedule.every(ROUTINES_INTERVAL).minutes.do(parse_alerts_routine)
schedule.every(ROUTINES_INTERVAL).minutes.do(delete_past_alerts_routine)
schedule.every(ROUTINES_INTERVAL).minutes.do(notify_chats_routine)


def main():
    updater.start_polling()

    # Start threads
    fCheckAlert = RoutinesThread()
    fCheckAlert.daemon = True
    fCheckAlert.start()

    fWebServer = WebServerThread()
    fWebServer.daemon = True
    fWebServer.start()

    # Run the bot until Ctrl-C is pressed
    updater.idle()


if __name__ == "__main__":
    main()
