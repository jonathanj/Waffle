import re
from datetime import datetime

from twisted.internet import task
from twisted.protocols.basic import Int32StringReceiver, StatefulStringProtocol
from twisted.python import log
from twisted.python.constants import Values, ValueConstant

from waffle.qt import adapters, types
from waffle.util import CommandDispatcherMixin, UnhandledCommand, splitEvery



class RequestType(Values):
    Invalid = ValueConstant(0)
    Sync = ValueConstant(1)
    RpcCall = ValueConstant(2)
    InitRequest = ValueConstant(3)
    InitData = ValueConstant(4)
    Heartbeat = ValueConstant(5)
    HeartbeatReply = ValueConstant(6)



def _splitIdentifier(s):
    a, b = s.split('/', 1)
    a = int(a)
    return a, b



def hasIdentifier(f):
    def _wrapper(self, identifier, *a, **kw):
        return f(self, _splitIdentifier(identifier), *a, **kw)
    return _wrapper



def userSetMetadata(name):
    def _wrapper(self, (networkId, nickname), value):
        return self.protocol.userSetMetadata(
            networkId, nickname, name, value)
    return hasIdentifier(_wrapper)



class QuasselSyncMessage(CommandDispatcherMixin):
    prefix = 'sync'


    def __init__(self, protocol):
        self.protocol = protocol


    #def sync_BufferSyncer_setLastSeenMsg(self, ignored, somethingId,
    #                                     messageId):
    #    pass


    #def sync_BufferSyncer_removeBuffer(self, ignored, bufferId):
    #    # XXX: when a buffer is removed, this should probably remove the tab on
    #    # the client.
    #    pass


    def sync_BufferSyncer_setMarkerLine(self, ignored, bufferId, messageId):
        self.protocol.markerUpdated(bufferId, messageId)


    def sync_BufferViewConfig_addBuffer(self, bufferViewId, bufferId, index):
        self.protocol.bufferAdded(int(bufferViewId), bufferId, index)


    def sync_BufferViewConfig_removeBuffer(self, bufferViewId, bufferId):
        self.protocol.bufferRemoved(int(bufferViewId), bufferId, False)


    def sync_BufferViewConfig_removeBufferPermanently(self, bufferViewId,
                                                      bufferId):
        self.protocol.bufferRemoved(int(bufferViewId), bufferId, True)


    def sync_BacklogManager_receiveBacklog(self, ignored, bufferId,
                                           startMessageId, endMessageId, limit,
                                           remaining, messages):
        # XXX: This kind of doesn't work because on the client it just appends
        # messages. Probably it should tell the client it's backlog and
        # probably the client should insert messages according to their
        # timestamp.
        messages.reverse()
        self.protocol.backlogReceived(messages)


    def sync_Network_setLatency(self, networkId, latency):
        self.protocol.latencyUpdated(int(networkId), latency)


    def sync_Network_addIrcChannel(self, networkId, bufferName):
        self.protocol.channelJoined(int(networkId), bufferName)


    def sync_Network_addIrcUser(self, networkId, host):
        self.protocol.userConnected(int(networkId), host)


    @hasIdentifier
    def sync_IrcChannel_addUserMode(self, (networkId, bufferName), nickname,
                                    mode):
        self.protocol.userModeAdded(networkId, bufferName, nickname, mode)


    @hasIdentifier
    def sync_IrcChannel_removeUserMode(self, (networkId, bufferName), nickname,
                                       mode):
        self.protocol.userModeRemoved(networkId, bufferName, nickname, mode)


    @hasIdentifier
    def sync_IrcChannel_setTopic(self, (networkId, bufferName), topic):
        self.protocol.topicChanged(networkId, bufferName, topic)


    @hasIdentifier
    def sync_IrcChannel_joinIrcUsers(self, (networkId, bufferName), nicknames,
                                     modes):
        userModes = zip(nicknames, modes)
        self.protocol.usersJoined(networkId, bufferName, userModes)


    #@hasIdentifier
    #def sync_IrcChannel_addChannelMode(self, (networkId, bufferName), mode,
    #                                   value):
    #    # 2012-08-29 13:50:56+0200 [QuasselClient,client] +Sync+ IrcChannel_addChannelMode: u'1/#testbot': (u'i', u'')
    #    pass


    #@hasIdentifier
    #def sync_IrcChannel_removeChannelMode(self, (networkId, bufferName), mode,
    #                                      value):
    #    # 2012-08-29 13:50:27+0200 [QuasselClient,client] +Sync+ IrcChannel_removeChannelMode: u'1/#testbot': (u'i', u'')
    #    pass


    @hasIdentifier
    def sync_IrcUser_partChannel(self, (networkId, nickname), bufferName):
        self.protocol.userParted(networkId, nickname, bufferName)


    @hasIdentifier
    def sync_IrcUser_quit(self, (networkId, nickname)):
        self.protocol.userQuit(networkId, nickname)


    sync_IrcUser_setNick = userSetMetadata('nick')
    sync_IrcUser_setAway = userSetMetadata('away')
    sync_IrcUser_setServer = userSetMetadata('server')
    sync_IrcUser_setRealName = userSetMetadata('realName')
    sync_IrcUser_setHost = userSetMetadata('host')
    sync_IrcUser_setUser = userSetMetadata('user')



class QuasselInitDataMessage(CommandDispatcherMixin):
    prefix = 'init'


    def __init__(self, protocol):
        self.protocol = protocol


    def init_Network(self, networkId, data):
        self.protocol.initializeNetwork(int(networkId), data)


    def init_BufferViewConfig(self, bufferViewId, bufferViewInfo):
        self.protocol.initializeBufferView(int(bufferViewId), bufferViewInfo)


    def init_BufferSyncer(self, objectName, bufferSyncerInfo):
        #2012-08-27 19:17:58+0200 [QuasselClient,client] +InitData+ BufferSyncer: u'': ({u'MarkerLines': [1, 18047, 2, 17372, 15, 18051], u'LastSeenMsg': [1, 18047, 2, 17372, 15, 18051]},)
        markerLines = splitEvery(2, bufferSyncerInfo[u'MarkerLines'])
        lastSeenMessages = splitEvery(2, bufferSyncerInfo[u'LastSeenMsg'])
        self.protocol.initializeBufferSyncer(
            list(markerLines), list(lastSeenMessages))



class QuasselRpcMessage(CommandDispatcherMixin):
    prefix = 'rpc'


    def __init__(self, protocol):
        self.protocol = protocol


    def rpc_2displayMsgMessage(self, messageInfo):
        self.protocol.privmsgReceived(messageInfo)


    def rpc___objectRenamed__(self, objectType, newObj, oldObj):
        #2012-08-29 11:33:17+0200 [QuasselClient,client] +RpcCall+ __objectRenamed__: ('IrcUser', u'1/korpse1', u'1/korpse')
        assert objectType == u'IrcUser', objectType
        self.protocol.objectRenamed(
            objectType, _splitIdentifier(oldObj), _splitIdentifier(newObj))



class QuasselMessage(CommandDispatcherMixin):
    prefix = 'message'

    _rpcFunctionMangleRe = re.compile(r'[()]')


    def __init__(self, protocol):
        self.protocol = protocol
        self._syncMessageHandler = QuasselSyncMessage(self.protocol)
        self._initMessageHandler = QuasselInitDataMessage(self.protocol)
        self._rpcMessageHandler = QuasselRpcMessage(self.protocol)


    def message_Heartbeat(self, timestamp):
        return RequestType.HeartbeatReply, [
            adapters.QTime(datetime.now().time())]


    def message_HeartbeatReply(self, timestamp):
        #return RequestType.HeartbeatReply, [
        #    adapters.QTime(datetime.now().time())]
        pass


    def message_InitData(self, className, objectName, *args):
        print '+InitData+ %s: %r: %r' % (className, objectName, args)
        return self._initMessageHandler.dispatch(className, objectName, *args)


    def message_Sync(self, className, objectName, functionName, *args):
        print '+Sync+ %s_%s: %r: %r' % (className, functionName, objectName, args)
        return self._syncMessageHandler.dispatch(
            '%s_%s' % (className, functionName), objectName, *args)


    def message_RpcCall(self, functionName, *args):
        print '+RpcCall+ %s: %r' % (functionName, args)
        functionName = self._rpcFunctionMangleRe.sub('', functionName)
        return self._rpcMessageHandler.dispatch(
            functionName, *args)



class QuasselClient(Int32StringReceiver, StatefulStringProtocol):
    state = 'login'

    _heartbeat = None
    heartbeatInterval = 120


    def __init__(self, username, password):
        self.username = username
        self.password = password


    def connectionMade(self):
        now = datetime.now().strftime('%b %d %Y %H:%M:%S').decode('ascii')
        self._sendQVariant(
            adapters.QVariantMap({
                u'ClientDate': adapters.QString(now),
                u'UseSsl': adapters.Bool(False),
                u'ClientVersion': adapters.QString(u"v0.6.1 (dist-<a href='http://git.quassel-irc.org/?p=quassel.git;a=commit;h=611ebccdb6a2a4a89cf1f565bee7e72bcad13ffb'>611ebcc</a>)"),
                u'UseCompression': adapters.Bool(False),
                u'MsgType': adapters.QString(u'ClientInit'),
                u'ProtocolVersion': adapters.Int(10)}))


    def stringReceived(self, data):
        #print '<-', len(data), repr(data)
        data = adapters.QVariant.parse(types.QVariant.parse(data))
        print '<=', data
        return StatefulStringProtocol.stringReceived(self, data)


    def connectionLost(self, reason):
        self._stopHeartbeat()
        Int32StringReceiver.connectionLost(self, reason)


    def sendInput(self, bufferInfo, message):
        if not message:
            return

        if message[0] == u'/':
            parts = message.split(u' ')
            parts[0] = parts[0].upper()
        else:
            parts = [u'/SAY', message]

        message = u' '.join(parts)

        self._sendRequest(
            RequestType.RpcCall.value,
            adapters.QString('2sendInput(BufferInfo,QString)'),
            adapters.UserType('BufferInfo', adapters.BufferInfo(bufferInfo)),
            adapters.QString(message))


    def privmsgReceived(self, messageInfo):
        self.web.sendJSON(u'message', messageInfo)


    def backlogReceived(self, messages):
        self.web.sendJSON(u'backlog', messages)


    def userModeAdded(self, networkId, bufferName, nickname, mode):
        self.web.sendJSON(u'userModeAdded',
            {u'networkId': networkId,
             u'bufferName': bufferName,
             u'nickname': nickname,
             u'mode': mode})


    def userModeRemoved(self, networkId, bufferName, nickname, mode):
        self.web.sendJSON(u'userModeRemoved',
            {u'networkId': networkId,
             u'bufferName': bufferName,
             u'nickname': nickname,
             u'mode': mode})


    def topicChanged(self, networkId, bufferName, topic):
        self.web.sendJSON(u'topicChanged',
            {u'networkId': networkId,
             u'bufferName': bufferName,
             u'topic': topic})


    def latencyUpdated(self, networkId, latency):
        self.web.sendJSON(u'latencyUpdated',
            {u'networkId': networkId,
             u'latency': latency})


    def objectRenamed(self, objectType, old, new):
        self.web.sendJSON(u'objectRenamed',
            {u'type': objectType,
             u'old': old,
             u'new': new})


    def userSetMetadata(self, networkId, nickname, key, value):
        self.web.sendJSON(u'userSetMetadata',
            {u'networkId': networkId,
             u'nickname': nickname,
             u'key': key,
             u'value': value})


    def userConnected(self, networkId, host):
        self.web.sendJSON(u'userConnected',
            {u'networkId': networkId,
             u'host': host})


    def userQuit(self, networkId, nickname):
        self.web.sendJSON(u'userQuit',
            {u'networkId': networkId,
             u'nickname': nickname})


    def userParted(self, networkId, nickname, bufferName):
        self.web.sendJSON(u'userParted',
            {u'networkId': networkId,
             u'nickname': nickname,
             u'bufferName': bufferName})


    def usersJoined(self, networkId, bufferName, userModes):
        self.web.sendJSON(u'usersJoined',
            {u'networkId': networkId,
             u'bufferName': bufferName,
             u'userModes': userModes})


    def channelJoined(self, networkId, bufferName):
        self.web.sendJSON(u'channelJoined',
            {u'networkId': networkId,
             u'bufferName': bufferName})


    def bufferAdded(self, bufferViewId, bufferId, index):
        self.web.sendJSON(u'bufferAdded',
            {u'bufferViewId': bufferViewId,
             u'bufferId': bufferId,
             u'index': index})


    def bufferRemoved(self, bufferViewId, bufferId, permanent=False):
        self.web.sendJSON(u'bufferRemoved',
            {u'bufferViewId': bufferViewId,
             u'bufferId': bufferId,
             u'permanent': permanent})


    def markerUpdated(self, bufferId, messageId):
        self.web.sendJSON(u'markerUpdated',
            {u'bufferId': bufferId,
             u'messageId': messageId})


    def initializeNetwork(self, networkId, networkInfo):
        self.web.sendJSON('initializeNetwork', [networkId, networkInfo])

        #List<QVariant<?>> reqPackedFunc = new LinkedList<QVariant<?>>();
        #reqPackedFunc.add(new QVariant<Integer>(RequestType.Sync.getValue(), QVariantType.Int));
        #reqPackedFunc.add(new QVariant<String>("BufferSyncer", QVariantType.String));
        #reqPackedFunc.add(new QVariant<String>("", QVariantType.String));
        #reqPackedFunc.add(new QVariant<String>("requestPurgeBufferIds", QVariantType.String));
        #sendQVariantList(reqPackedFunc);	


    def initializeBufferView(self, bufferViewId, bufferViewInfo):
        self.web.sendJSON(
            'initializeBufferView', [bufferViewId, bufferViewInfo])


    def initializeBufferSyncer(self, markerLines, lastSeenMessages):
        self.web.sendJSON('initializeBufferSyncer',
            {u'markerLines': markerLines,
             u'lastSeenMessages': lastSeenMessages})


    def _sendQVariant(self, value):
        self.sendString(
            types.QVariant.build(
                adapters.QVariant(value).serialize()))


    def _sendRequest(self, requestType, *args):
        self._sendQVariant(
            adapters.QVariantList(
                [adapters.Int(requestType)] + list(args)))


    def _sendInitRequest(self, className, objectName):
        self._sendRequest(
            RequestType.InitRequest.value,
            adapters.QString(className),
            adapters.QString(objectName))


    def _createHeartbeat(self):
        """
        Create the heartbeat L{LoopingCall}.
        """
        return task.LoopingCall(self._sendHeartbeat)


    def _sendHeartbeat(self):
        self._sendRequest(
            RequestType.Heartbeat.value,
            adapters.QTime(datetime.now().time()))


    def _stopHeartbeat(self):
        if self._heartbeat is not None:
            self._heartbeat.stop()
            self._heartbeat = None


    def _startHeartbeat(self):
        self._stopHeartbeat()
        if self.heartbeatInterval is None:
            return
        self._heartbeat = self._createHeartbeat()
        self._heartbeat.start(self.heartbeatInterval, now=False)


    def proto_login(self, data):
        assert data[u'MsgType'] == u'ClientInitAck'
        self._sendQVariant(
            adapters.QVariantMap({
                u'MsgType': adapters.QString(u'ClientLogin'),
                u'User': adapters.QString(self.username),
                u'Password': adapters.QString(self.password)}))
        return 'loginAck'


    def proto_loginAck(self, data):
        assert data[u'MsgType'] == u'ClientLoginAck'
        return 'sessionInit'


    def proto_sessionInit(self, data):
        assert data[u'MsgType'] == u'SessionInit'
        data = data.get(u'SessionState')

        for bufferInfo in data.get('BufferInfos'):
            self.web.sendJSON('initializeBuffer', bufferInfo)

        self._messageHandler = QuasselMessage(self)
        for networkId in data.get(u'NetworkIds', []):
            self._sendInitRequest(u'Network', unicode(networkId))

        for bufferInfo in data.get('BufferInfos', []):
            self.requestBacklog(bufferInfo.get(u'id'), -1, -1, 50)

        self._sendInitRequest(u'BufferSyncer', u'');
        ##self._sendInitRequest(u'BufferViewManager', u'');
        self._sendInitRequest(u'BufferViewConfig', u'0');

        self._startHeartbeat()
        return 'message'


    def proto_message(self, data):
        requestType = RequestType.lookupByValue(data.pop(0))
        # XXX: QuasselDroid does some message buffering until all network inits
        # have happened, do we need this?
        try:
            self._messageHandler.dispatch(requestType.name, *data)
        except UnhandledCommand:
            log.err(None)
        return 'message'


    def requestBacklog(self, bufferId, startMessageId, endMessageId, limit):
        self._sendRequest(
            RequestType.Sync.value,
            adapters.QString('BacklogManager'),
            adapters.QString(''),
            adapters.QString('requestBacklog'),
            adapters.UserType('BufferId', adapters.Int(bufferId)),
            adapters.UserType('MsgId', adapters.Int(startMessageId)),
            adapters.UserType('MsgId', adapters.Int(endMessageId)),
            adapters.Int(limit),
            adapters.Int(0))


    def hideBuffer(self, bufferId):
        self._sendRequest(
            RequestType.Sync.value,
            adapters.QString('BufferViewConfig'),
            adapters.QString('0'),
            adapters.QString('requestRemoveBuffer'),
            adapters.UserType('BufferId', adapters.Int(bufferId)))


    def unhideBuffer(self, bufferId, index):
        self._sendRequest(
            RequestType.Sync.value,
            adapters.QString('BufferViewConfig'),
            adapters.QString('0'),
            adapters.QString('requestAddBuffer'),
            adapters.UserType('BufferId', adapters.Int(bufferId)),
            adapters.Int(index))
