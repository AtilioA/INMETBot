# Webserver to prevent the bot from sleeping
import web
from utils import webserver
import logging
import time
import schedule
from threading import Thread

from bot_config import updater
import bot_handlers  # noqa (ignore linter warning)
from bot_routines import parse_alerts_routine, delete_past_alerts_routine, notify_chats_routine

# ROUTINES_INTERVAL = 60

# Enable logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='requests.log',
                    level=logging.DEBUG)


urls = ('/', 'index')


class index:
    def GET(self):
        return "Hello, world!"


# Thread for the web server
class WebServerThread(Thread):
    def run(self):
        app = web.application(urls, globals())
        app.run()


# Thread for running routines periodically
class RoutinesThread(Thread):
    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)


schedule.every().hour.do(parse_alerts_routine)
schedule.every().hour.do(delete_past_alerts_routine)
schedule.every().hour.do(notify_chats_routine)


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
