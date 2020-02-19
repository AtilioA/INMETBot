# Webserver to prevent the bot from sleeping
import webserver
import logging
import time
import schedule
import parse_alerts
from datetime import timedelta
from threading import Thread

from bot_config import updater
import bot_handlers
from bot_routines import parse_alerts_routine, notify_chats_routine

PARSE_ALERTS_INTERVAL = 20

# Enable logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='requests.log',
                    level=logging.DEBUG)


# Thread for the web server
class WebServerThread(Thread):
    def run(self):
        app = webserver.web.application(webserver.urls, globals())
        app.run()


# Thread for checking alerts periodically
class CheckAlertsThread(Thread):
    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)


# To guarantee a stable execution schedule
def run_threaded(job_function):
    jobThread = Thread(target=job_function)
    jobThread.start()
schedule.every(PARSE_ALERTS_INTERVAL).minutes.do(run_threaded, parse_alerts_routine)
schedule.every(PARSE_ALERTS_INTERVAL + 1).minutes.do(run_threaded, notify_chats_routine)


def main():
    updater.start_polling()

    # Start threads
    fCheckAlert = CheckAlertsThread()
    fCheckAlert.daemon = True
    fCheckAlert.start()

    fWebServer = WebServerThread()
    fWebServer.daemon = True
    fWebServer.start()

    # Run the bot until Ctrl-C is pressed
    updater.idle()


if __name__ == "__main__":
    main()
