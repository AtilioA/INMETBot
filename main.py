# Webserver to prevent the bot from sleeping
import webserver
import logging

from bot_config import updater
import bot_handlers

# Enable logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename='requests.log',
                    level=logging.DEBUG)


def main():
    updater.start_polling()
    # Run the bot until you press Ctrl-C
    updater.idle()

    app = webserver.web.application(webserver.urls, globals())
    app.run()


if __name__ == "__main__":
    main()
