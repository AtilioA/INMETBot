# Webserver to prevent the bot from sleeping
import webserver

from bot_config import updater
from bot_functions import *
from bot_handlers import *

updater.start_polling()

if __name__ == "__main__":
    app = webserver.web.application(webserver.urls, globals())
    app.run()
