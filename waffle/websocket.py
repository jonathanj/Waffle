import json

from twisted.internet import reactor
from twisted.internet.defer import maybeDeferred
from twisted.internet.protocol import Factory, Protocol, ClientCreator

from waffle.quassel.protocol import QuasselClient



class WaffleProtocol(Protocol):
    def sendJSON(self, messageType, data):
        print '=json=>', repr(messageType), repr(data)
        self.transport.write(json.dumps({u'type': messageType, u'data': data}))


    def event_auth(self, data):
        def _connectedToCore(protocol):
            protocol.web = self
            self.quassel = protocol
            return u'auth', {
                u'authToken': u'AUTH'}

        username = data.get(u'username')
        password = data.get(u'password')
        cc = ClientCreator(reactor, QuasselClient, username, password)
        d = cc.connectTCP('bombard.jsphere.com', 4242)
        d.addCallback(_connectedToCore)
        return d


    def event_sendInput(self, data):
        message = data.get(u'message')
        bufferInfo = data.get(u'bufferInfo')
        return self.quassel.sendInput(bufferInfo, message)


    def event_hideBuffer(self, data):
        bufferId = data.get(u'bufferId')
        return self.quassel.hideBuffer(bufferId)


    def event_unhideBuffer(self, data):
        bufferId = data.get(u'bufferId')
        index = data.get(u'index')
        return self.quassel.unhideBuffer(bufferId, index)


    def dataReceived(self, data):
        def _sendReply(reply):
            if reply is not None:
                messageType, data = reply
                return self.sendJSON(messageType, data)

        data = json.loads(data)
        event = data.get(u'type').encode('ascii')

        print '@@@', self, repr(data)
        meth = getattr(self, 'event_%s' % (event,))
        d = maybeDeferred(meth, data.get(u'data'))
        d.addCallback(_sendReply)



WaffleFactory = Factory
WaffleFactory.protocol = WaffleProtocol
