import web

# Webserver to prevent the bot from sleeping
urls = ('/', 'index')
class index:
    def GET(self):
        return "200"
