import web

urls = ('/', 'index')
class index:
    def GET(self):
        i = web.input(name=None)
        return render.index(i.name)
render = web.template.render('templates/')
