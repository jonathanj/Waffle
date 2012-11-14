from twisted.application import strports
from twisted.application.service import Application
from twisted.web.server import Site

from txws import WebSocketFactory

from waffle import web, websocket



application = Application('waffle')

service = strports.service(
    'ssl:port=8443:'
    'privateKey=server.key:'
    'certKey=server.crt:sslmethod=TLSv1_METHOD',
    Site(web.RootResource()))
service.setServiceParent(application)

service = strports.service(
    'ssl:port=8076:'
    'privateKey=server.key:'
    'certKey=server.crt:sslmethod=TLSv1_METHOD',
    WebSocketFactory(websocket.WaffleFactory()))
service.setServiceParent(application)
