# Webserver to prevent the bot from sleeping
import webserver

from bot_config import updater
import bot_handlers

updater.start_polling()

if __name__ == "__main__":
    app = webserver.web.application(webserver.urls, globals())
    app.run()
