from twisted.web.resource import Resource
from twisted.web.static import File, Data
from twisted.python.filepath import FilePath



staticDir = FilePath(__file__).sibling('static')



class RootResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('static', File(staticDir.path, defaultType='text/plain'))
        # XXX: this kind of sucks
        self.putChild('', MainResource())
        self.putChild('login', MainResource())



class MainResource(Resource):
    def render_GET(self, request):
        data = staticDir.child('templates').child('main.html').getContent()
        return Data(data, 'text/html; charset=UTF-8').render_GET(request)
