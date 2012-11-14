class Message extends Backbone.Model
    defaults:
        'marked': false


    getNick: =>
        @get('sender').split('!', 1)[0]


    getTimestamp: =>
        return new XDate(@get('timestamp') * 1000)


    setFlag: (flag) =>
        flags = @get('flags')
        flags[flag] = true
        @set('flags', flags)


    getFlag: (flag) =>
        flags = @get('flags')
        return flags[flag]



class MessageView extends Backbone.View
    tagName: 'div'
    className: 'msg'
    templates:
        plain:        _.template $('#message-template').html()
        #notice:       _.template $('#message-template').html()
        action:       _.template $('#message-action-template').html()
        nick:         _.template $('#message-nick-template').html()
        mode:         _.template $('#message-mode-template').html()
        join:         _.template $('#message-join-template').html()
        part:         _.template $('#message-part-template').html()
        quit:         _.template $('#message-quit-template').html()
        kick:         _.template $('#message-kick-template').html()
        #kill:         _.template $('#message-template').html()
        #server:       _.template $('#message-template').html()
        #info:         _.template $('#message-template').html()
        #error:        _.template $('#message-template').html()
        #daychange:    _.template $('#message-template').html()
        topic:        _.template $('#message-topic-template').html()
        #netsplitjoin: _.template $('#message-template').html()
        #netsplitquit: _.template $('#message-template').html()
        #invite:       _.template $('#message-template').html()


    initialize: ->
        @model.on 'change:marked', @updateMarker


    render: =>
        json = @model.toJSON()
        json.nick = @model.getNick()
        json.timestamp = @model.getTimestamp()

        messageType = @model.get('type')
        template = @templates[messageType]
        if not template?
            template = @templates['plain']
        @$el.html template json

        # XXX: it's actually a lot more involved than just this.  parts, joins,
        # quits, kills, netsplits, nick changes, topic changes, etc.  all come
        # through as regular messages. probably there should be different
        # templates for all these types.
        flags = _.without(
            _.set @model.get('flags'), 'self')
        classes = ('is-msg-flag-' + flag for flag in flags)
        classes.push 'is-msg-type-' + messageType
        @$el.addClass classes.join(' ')
        return @


    updateMarker: (model, value, options) =>
        console.log 'MessageView.updateMarker'
        console.log value
        if value
            @$el.addClass 'is-msg-marker'
        else
            @$el.removeClass 'is-msg-marker'



class Messages extends Backbone.Collection
    model: Message



# u'Karl!Karl@Karl.Illuminatus': {u'away': True,
#                                 u'awayMessage': u'',
#                                 u'channels': [u'#code'],
#                                 u'host': u'Karl.Illuminatus',
#                                 u'idleTime': 1345734167000.0,
#                                 u'ircOperator': u'',
#                                 u'lastAwayMessage': 0,
#                                 u'loginTime': 1345734167000.0,
#                                 u'nick': u'Karl',
#                                 u'realName': u'Karl',
#                                 u'server': u'kore.shadowfire.org',
#                                 u'suserHost': u'',
#                                 u'user': u'Karl',
#                                 u'userModes': u'',
#                                 u'whoisServiceReply': u''},

class NetworkUser extends Backbone.Model
    defaults:
        channels: []
        nick: ''



class NetworkUsers extends Backbone.Collection
    model: NetworkUser


    initialize: ->
        @_byNick = {}
        @on 'add', @addUser
        @on 'remove', @removeUser
        @on 'change:nick', @nickChanged


    _addUser: (model) =>
        @_byNick[model.get('nick')] = model


    addUser: (model, collection) =>
        @_addUser model


    _removeUser: (nick) =>
        delete @_byNick[nick]


    removeUser: (model, collection) =>
        @_removeUser model.get 'nick'


    nickChanged: (model, value) =>
        @_removeUser model.previous 'nick'
        @_addUser model


    # XXX: is there a reason not to use the nickname as the key?
    getByNick: (nick) =>
        return @_byNick[nick]



class BufferUser extends Backbone.Model
    initialize: ->
        @get('networkUser').on 'change:nick', @nickChanged


    nickChanged: (model, value) =>
        console.log 'nickChanged', model, value
        @set 'id', value


    addMode: (mode) =>
        modes = _.union @get('modes'), [mode]
        @set 'modes', modes


    removeMode: (mode) =>
        modes = _.without @get('modes'), mode
        @set 'modes', modes



class BufferUserView extends Backbone.View
    tagName: 'li'
    template: _.template $('#user-template').html()


    initialize: ->
        @model.on 'change', @render


    render: =>
        user = @model.toJSON()
        user.prefixes = @modesToPrefixes user.modes
        @$el.html @template user
        return @



class BufferUsers extends Backbone.Collection
    model: BufferUser


    comparator: (user) ->
        return user.id



class BufferUsersView extends Backbone.View
    tagName: 'ul'


    initialize: ->
        @model.on 'add', @render
        @model.on 'remove', @render


    render: =>
        @$el.empty()
        @model.each (model) =>
            view = new BufferUserView
                model: model
            # XXX: this isn't great, and neither is giving "network" to the
            # users view.
            view.modesToPrefixes = (modes) =>
                return (@model.buffer.network.modesToPrefixes modes).join('')
            @$el.append view.render().el
        return @



class Buffer extends Backbone.Model
    defaults:
        focus: false
        hidden: false


    initialize: ->
        @messages = new Messages
        # XXX: FIXME: TODO: There should be one of these on network, to track
        # global movements of users, while this should track channel movements
        # (modes, etc.) of users.
        # A number of things only specify networkId and nickname.
        @users = new BufferUsers
        @users.buffer = @
        @users.on 'add', @addUser
        @users.on 'remove', @removeUser


    addUser: (model, collection) =>
        networkUser = model.get('networkUser')
        channels = networkUser.get('channels')
        networkUser.set 'channels', _.union(channels, [@get('name')])


    removeUser: (model, collection) =>
        networkUser = model.get('networkUser')
        channels = networkUser.get('channels')
        networkUser.set 'channels', _.without(channels, @get('name'))


    updateMarker: (messageId) =>
        console.log 'updateMarker'
        console.log messageId
        if @_markedMessage?
            console.log 'remove old marker'
            @_markedMessage.set 'marked', false

        message = @messages.get messageId
        #console.log message
        if message?
            console.log 'QWFQWF'
            message.set 'marked', true
            @_markedMessage = message



class BufferTabView extends Backbone.View
    template: _.template $('#buffer-tab-template').html()

    events:
        'click': 'focused'
        'click button.close': 'hideBuffer'


    initialize: ->
        @_unreadCounts = {}
        @model.on 'change:hidden change:silent', @hiddenChanged
        @model.on 'change:focus', @focusChanged
        @model.messages.on 'add', @addMessage


    render: =>
        bufferType = @model.get('type')
        switch bufferType
            when 'status' then name = '<status>'
            when 'channel' then name = @model.get('name')
            when 'query' then name = @model.get('name')
            else
                throw new Error("Unknown buffer type: #{ bufferType }")

        @setElement @template
            id: @model.id
            name: name

        return @


    focused: (event) =>
        console.log 'FOCUSED!!!'
        @model.set 'focus', true


    hideBuffer: (event) =>
        @model.protocol.send 'hideBuffer',
            bufferId: @model.id
        return false


    focusChanged: (model, value) =>
        if value
            # XXX: this sucks
            @_updateUnreadCount 'plain', 0
            @_updateUnreadCount 'highlight', 0


    hiddenChanged: (model, value) =>
        if value
            @$el.hide()
        else
            @$el.show()


    removeBuffer: (model, collection) =>
        console.log 'BufferTabView.removeBuffer'
        @remove()


    _updateUnreadCount: (type, count) =>
        # XXX: this whole thing sucks
        if count?
            @_unreadCounts[type] = count
        else
            if not @_unreadCounts[type]?
                @_unreadCounts[type] = 0
            @_unreadCounts[type] += 1
        @$(".is-#{ type }-count").text(@_unreadCounts[type])


    addMessage: (model, collection) =>
        # If we get a message and we're hidden then unhide us.
        if @model.get 'hidden'
            @model.set 'hidden', false
            @model.protocol.send 'unhideBuffer',
                bufferId: @model.id
                index: collection.length

        if not model.getFlag 'backlog'
            if model.getFlag 'highlight'
                @_updateUnreadCount 'highlight'
            @_updateUnreadCount 'plain'



class BufferView extends Backbone.View
    template: _.template $('#buffer-template').html()

    events:
        'submit form': 'keypress'


    initialize: ->
        @model.on 'change:topic', @topicChanged
        @model.on 'change:focus', @focusChanged
        #@model.on 'remove', @removeBuffer
        @model.messages.on 'add', @addMessage


    render: =>
        console.log 'BufferView.render'
        @setElement @template
            id: @model.id

        view = new BufferUsersView
            model: @model.users
        @$('.buffer-userlist').html view.render().el
        return @


    #removeBuffer: (model, collection) =>
    #    console.log 'BufferView.removeBuffer'
    #    @remove()


    addMessage: (model, collection) =>
        console.log 'XXX!!! addMessage'
        view = new MessageView
            model: model
        @$('.buffer-content').append view.render().el


    focusChanged: (model, value) =>
        console.log 'view:focusChanged', model.get('name'), value
        if not value
            # XXX: update last seen and marker
            console.log 'updateMarkerAndLastSeenKTHX'


    topicChanged: (model, value) =>
        # XXX: this should probably go into some kind of BufferInfoView that is
        # rerendered under some conditions, this way we can put other
        # information here for different kinds of buffers like query buffers.
        console.log 'XXX!!! topicChanged'
        @$('.buffer-topic').text(value)


    keypress: (event) =>
        console.log 'keypress'
        console.log event
        bufferInput = @$('.buffer-input')
        message = bufferInput.val()
        @model.protocol.send 'sendInput',
            message: message
            bufferInfo: @model.toJSON()

        bufferInput.val ''
        return false



class Buffers extends Backbone.Collection
    model: Buffer


    initialize: ->
        @_byName = {}
        @on 'change:focus', @focusChanged
        @on 'add', @addBuffer
        @on 'remove', @removeBuffer


    comparator: (model) ->
        return model.get('name')


    addBuffer: (model, collection) =>
        @_byName[model.get('name')] = model


    removeBuffer: (model, collection) =>
        delete @_byName[model.get('name')]


    focusChanged: (model, value) =>
        console.log 'buffers:focusChanged', model.get('name'), value
        @_previouslyFocused?.set 'focus', false
        @_previouslyFocused = model


    getByName: (name) =>
        return @_byName[name]



class Network extends Backbone.Model
    defaults:
        latency: 0


    initialize: ->
        @on 'change:features', @_updateFeatures

        @users = new NetworkUsers
        @users.on 'remove', @removeUser

        @buffers = new Buffers
        @buffers.on 'add', @addBuffer


    _updateFeatures: (model, value, options) =>
        @_prefixMapping = @_buildPrefixMapping value.PREFIX


    _buildPrefixMapping: (feature) ->
        ###
        Build a mapping of channel user mode to prefix.
        ###
        [modes, symbols] = feature.substr(1).split(')')
        return _.toMapping _.zip(modes, symbols)


    removeUser: (model, collection) =>
        # When a user leaves the network, remove their BufferUser from all the
        # buffers we know they were in.
        nickname = model.get('nick')
        for bufferName in model.get('channels')
            buffer = @buffers.getByName bufferName
            bufferUser = buffer.users.get nickname
            buffer.users.remove [bufferUser]


    addBuffer: (model, collection) =>
        model.messages.on 'add', @processMessage


    processMessage: (model, collection) =>
        @checkForHighlight model


    checkForHighlight: (message) =>
        if message.get('type') != 'plain'
            return

        myNick = @get 'myNick'
        if myNick.length <= 0
            return

        nickMatch = new RegExp('\\b' + myNick + '\\b')
        if nickMatch.test message.get('content')
            message.setFlag('highlight')


    isSelf: (nickname) =>
        # XXX: case insensitive comparison, probably should comply with the
        # "CASEMAPPING" feature.
        return @get('myNick') == nickname


    modesToPrefixes: (modes) =>
        return _.values _.pick(@_prefixMapping, modes)



class NetworkInfoView extends Backbone.View
    template: _.template $('#network-info-template').html()


    initialize: ->
        @model.on 'change', @render


    render: =>
        @$el.html @template @model.toJSON()
        return @



class NetworkView extends Backbone.View
    template: _.template $('#network-template').html()


    initialize: ->
        @model.buffers.on 'add', @addBuffer


    render: =>
        console.log 'NetworkView.render'
        @$el.empty()

        view = new NetworkInfoView
            model: @model
        @$el.append view.render().el

        console.log @model.toJSON()
        @$el.append @template @model.toJSON()
        return @


    addBuffer: (model, collection) =>
        console.log 'NetworkView.addBuffer'
        bufferTabView = new BufferTabView
            model: model
        @$('.buffer-tabs').append bufferTabView.render().el

        bufferView = new BufferView
            model: model
        @$('.buffer-contents').append bufferView.render().el



class Client extends Backbone.Collection
    model: Network


    getBufferById: (id) =>
        network = @find (network) =>
            return network.buffers.get id
        return network.buffers.get id



class ClientView extends Backbone.View
    initialize: (@client) ->
        @client.on 'add', @addNetwork
        console.log 'NIENIENIEN'
        console.dir @model


    # XXX: should this be here?
    addNetwork: (model, collection) =>
        console.log 'ClientView.addNetwork'
        view = new NetworkView
            model: model
        @$el.append view.render().el



class App
    templates:
        errorAlert: _.template $('#error-alert-template').html()


    connect: (options) =>
        d = $.Deferred()
        console.log 'connect'
        console.log options
        # XXX: remove stale view elements
        # XXX: clean up old event handler views and stuff
        @_eventHandler = new EventHandler options.events
        self = @
        ws = $.websocket options.url,
            open: ->
                console.log 'open'
                self._eventHandler.protocol = ws
                ws.send 'auth',
                    username: options.username
                    password: options.password

            close: ->
                console.log 'close'
                # XXX: remove stale view elements
                self.errorAlert
                    heading: 'Connection closed'
                    content: 'The WebSocket connection was closed.'
                    button: 'Reconnect'
                    click: ->
                        self.connect options

            error: ->
                console.log 'error'
                # XXX: remove stale view elements
            #    self.errorAlert
            #        heading: 'Connection error'
            #        content: 'An error occurred while establishing a WebSocket connection.'
            #        button: 'Reconnect'
            #        click: ->
            #            self.connect options
            events: @_eventHandler

        return d


    errorAlert: (info) =>
        console.log 'errorAlert'
        node = $(@templates.errorAlert info)
        if info.click?
            $('.btn-primary', node).bind 'click', info.click
        $('#notifications').append node



class AppView extends Backbone.View
    el: $('#app')


    replaceView: (view) ->
        view.render()
        if @currentView
            @currentView.remove()
        @currentView = view
        @$el.empty()
        @$el.append view.el



class EventHandler
    constructor: (@handler) ->
        @_maxBufferId = 0


    auth: (e) =>
        console.log 'event:auth'
        #console.log e
        @client = new Client
        window.router.client = @client
        console.log @handler
        @handler.authenticated?()


    initializeBufferView: (e) =>
        console.log 'event:initializeBufferView'
        console.log e
        [bufferViewId, data] = e.data

        bufferIds = _.union(
            data.BufferList,
            data.TemporarilyRemovedBuffers,
            data.RemovedBuffers)
        @_maxBufferId = _.max(bufferIds)

        for bufferId in data.TemporarilyRemovedBuffers
            buffer = @client.getBufferById bufferId
            buffer.set 'hidden', true

        for bufferId in data.RemovedBuffers
            buffer = @client.getBufferById bufferId
            buffer.set 'silent', true


        #data.TemporarilyRemovedBuffers
        #2012-08-29 16:50:46+0200 [QuasselClient,client] =json=> 'initializeBufferView' [0, {u'networkId': 0, u'RemovedBuffers': [], u'minimumActivity': 0, u'addNewBuffersAutomatically': True, u'TemporarilyRemovedBuffers': [17], u'sortAlphabetically': True, u'bufferViewName': u'All Chats', u'hideInactiveBuffers': False, u'BufferList': [2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], u'allowedBufferTypes': 15, u'disableDecoration': False}]


    _addBuffer: (bufferInfo) =>
        network = @client.get bufferInfo.networkId
        if not network
            network = new Network
                id: bufferInfo.networkId
            @client.add [network]

        buffer = network.buffers.get bufferInfo.id
        if not buffer
            console.log 'addBuffer'
            buffer = new Buffer bufferInfo
            # XXX:
            buffer.protocol = @protocol
            buffer.network = network
            network.buffers.add [buffer]


    initializeBuffer: (e) =>
        console.log 'event:initializeBuffer'
        #console.log e
        @_addBuffer e.data


    # XXX: this name does not reflect what kind of users it operates on
    _addUsers: (buffer, userModes) =>
        users = []
        for [nickname, modes] in userModes
            networkUser = buffer.network.users.getByNick nickname
            user = new BufferUser
                id: nickname
                networkUser: networkUser
                modes: modes.split ''
            users.push user
        buffer.users.add users


    initializeNetwork: (e) =>
        console.log 'event:initializeNetwork'
        #console.log e
        [networkId, data] = e.data

        # XXX: crap out if this network doesn't exist
        network = @client.get networkId
        network.set
            name: data.networkName
            myNick: data.myNick
            features: data.Supports
            latency: data.latency

        users = []
        for host, info of data.IrcUsersAndChannels.users
            info.id = host
            user = new NetworkUser info
            users.push user
        network.users.add users

        for channel, info of data.IrcUsersAndChannels.channels
            # XXX: check return value
            buffer = network.buffers.getByName channel
            buffer.set 'topic', info.topic
            @_addUsers buffer, _.mappingItems(info.UserModes)


    initializeBufferSyncer: (e) =>
        console.log 'event:initializeBufferSyncer'
        for [bufferId, messageId] in e.data.markerLines
            buffer = @client.getBufferById bufferId
            buffer.updateMarker messageId

        # XXX: update lastSeenMessages stuff



    _addMessage: (messageInfo, backlog=false) =>
        network = @client.get messageInfo.bufferInfo.networkId
        buffer = network.buffers.get messageInfo.bufferInfo.id
        # XXX: this buffer might not exist yet if it's a new query or
        # something?
        if buffer?
            msg = buffer.messages.get messageInfo.id
            # XXX: crap out if this message exists
            if not msg
                msg = new Message messageInfo
                if backlog
                    msg.setFlag 'backlog'
                buffer.messages.add [msg]
        else if messageInfo.bufferInfo.type == 'query'
            console.error(
                '_addMessage failed, no such buffer', messageInfo.bufferInfo.id)
            console.dir messageInfo
            @_addBuffer messageInfo.bufferInfo
            @_addMessage messageInfo


    message: (e) =>
        console.log 'event:message'
        console.log e
        @_addMessage e.data


    backlog: (e) =>
        console.log 'event:backlog'
        for messageInfo in e.data
            @_addMessage messageInfo, true


    userModeAdded: (e) =>
        console.log 'event:userModeAdded'
        console.log e

        network = @client.get e.data.networkId
        buffer = network.buffers.getByName e.data.bufferName
        user = buffer.users.get e.data.nickname
        user.addMode e.data.mode


    userModeRemoved: (e) =>
        console.log 'event:userModeRemoved'
        console.log e

        modeInfo = e.data
        network = @client.get modeInfo.networkId
        buffer = network.buffers.getByName modeInfo.bufferName
        user = buffer.users.get e.data.nickname
        user.removeMode e.data.mode


    topicChanged: (e) =>
        console.log 'event:topicChanged'
        console.log e

        network = @client.get e.data.networkId
        buffer = network.buffers.getByName e.data.bufferName
        buffer.set 'topic', e.data.topic


    objectRenamed: (e) =>
        console.log 'event:objectRenamed'
        console.log e
        # XXX: check e.data.type
        # XXX: we just assume that networkId is the same, we should probably
        # check that.
        [networkId, oldNickname] = e.data.old
        [networkId, newNickname] = e.data.new
        network = @client.get networkId
        user = network.users.getByNick oldNickname
        user.set 'nick', newNickname


    userSetMetadata: (e) =>
        console.log 'event:userSetMetadata'
        console.log e
        network = @client.get e.data.networkId
        user = network.users.getByNick e.data.nickname
        user.set e.data.key, e.data.value


    userConnected: (e) =>
        console.log 'event:userConnected'
        console.log e
        network = @client.get e.data.networkId
        nick = e.data.host.split('!', 1)
        user = new NetworkUser
            id: e.data.host
            nick: nick
        network.users.add [user]


    userQuit: (e) =>
        console.log 'event:userQuit'
        console.log e
        network = @client.get e.data.networkId
        networkUser = network.users.getByNick e.data.nickname
        network.users.remove [networkUser]


    usersJoined: (e) =>
        console.log 'event:usersJoined'
        console.log e

        network = @client.get e.data.networkId
        buffer = network.buffers.getByName e.data.bufferName
        @_addUsers buffer, e.data.userModes


    userParted: (e) =>
        console.log 'event:userParted'
        console.log e

        network = @client.get e.data.networkId
        buffer = network.buffers.getByName e.data.bufferName

        if false#network.isSelf e.data.nickname
            console.log 'self leaving'
            # XXX: this a bit sledgehammerish, we probably want to not destroy
            # the buffer view.
            network.buffers.remove [buffer]
        else
            console.log 'other leaving'
            user = buffer.users.get e.data.nickname
            buffer.users.remove [user]


    latencyUpdated: (e) =>
        #console.log 'event:latencyUpdated'
        #console.log e
        network = @client.get e.data.networkId
        network.set 'latency', e.data.latency


    channelJoined: (e) =>
        console.log 'event:channelJoined'
        console.log e
        @_addBuffer
            id: @_maxBufferId + 1
            networkId: e.data.networkId
            name: e.data.bufferName
            type: 'channel'


    bufferAdded: (e) =>
        console.log 'event:bufferAdded'
        console.log e
        buffer = @client.getBufferById e.data.bufferId
        # XXX: do something with the index?
        buffer.set
            silent: false
            hidden: false


    bufferRemoved: (e) =>
        console.log 'event:bufferRemoved'
        console.log e
        buffer = @client.getBufferById e.data.bufferId
        if e.data.permanent
            buffer.set
                silent: true
        else
            buffer.set
                hidden: true


    markerUpdated: (e) =>
        console.log 'event:markerUpdated'
        console.log e
        buffer = @client.getBufferById e.data.bufferId
        #console.log buffer
        buffer.updateMarker e.data.messageId



class LoginView extends Backbone.View
    template: _.template $('#login-template').html()

    events:
        'click .js-connect':       'connect'
        'click .js-clear-storage': 'clearStorage'


    initialize: (@appView) ->
        @app = @appView.app


    render: =>
        creds = $.totalStorage 'credentials'
        creds ?= {}
        console.log 'creds', creds
        @setElement @template()
        @$('form').populateForm creds
        return @


    connect: ->
        creds = @$('form').serializeForm()
        if creds.store
            $.totalStorage 'credentials', creds

        window.router._connect creds
        return false


    clearStorage: ->
        $.totalStorage 'credentials', null
        alert 'cleared'
        return false




class WaffleRouter extends Backbone.Router
    routes:
        '': 'chat'
        'connect': 'connect'
        'login': 'login'


    _connect: (creds) ->
        @appView.app.connect
            # XXX: don't hardcode this
            url: 'wss://callisto.jsphere.com:8076'
            username: creds.username[0]
            password: creds.password[0]
            events:
                authenticated: ->
                    console.log 'AUTHENTICATED!!!!'
                    window.router.navigate '/', trigger: true
                rejected: ->
                    console.log 'REJECTED!!!!'


    connect: ->
        console.log 'route:connect'
        creds = $.totalStorage 'credentials'
        if not creds?
            window.router.navigate 'login', trigger: true
            return

        @_connect creds


    chat: ->
        console.log 'route:chat'
        if not @client?
            console.log 'QWFQWFYAURSNYAURNS uh oh'
            @navigate 'connect',
                trigger: true
                replace: true
            return

        view = new ClientView @client
        @appView.replaceView view


    login: ->
        console.log 'route:login'
        view = new LoginView @appView
        @appView.replaceView view



$(document).ready ->
    _.mixin
        set: (s) ->
            (k for k, v of s when v)

        mappingItems: (o) ->
            return _.zip(_.keys(o), _.values(o))

        toMapping: (pairs) ->
            o = {}
            for [k, v] in pairs
                o[k] = v
            return o

    $.fn.serializeForm = ->
       o = {}
       for x in @serializeArray()
           if o[x.name]?
               o[x.name] = []
           o[x.name] = [x.value ? '']
       return o


    $.fn.populateForm = (data) ->
        form = @
        for key, values of data
            form.find("[name='#{ key }']").val(values)
        return @


    app = new App
    appView = new AppView
    appView.app = app
    window.router = new WaffleRouter
    router.appView = appView
    Backbone.history.start pushState: true



###
Factory factory function for DOM node generation.

The returned factory accepts the tag name, mapping of attributes and an array of children. The attributes parameter may be omitted and the children may be a single value.

Returns a jQuery object wrapping a DOM node.

Examples:

D = DOMBuilder()

node = D 'div', class: 'foo', [
    D 'strong', 'Title',
    D 'span', [
        D 'em', 'hello ',
        D 'small', 'world']]


<div class="foo">
    <strong>Title</strong>
    <span>
        <em>hello</em>
        <small>world</small>
    </span>
</div>
###
DOMBuilder = (doc=document) ->
    (tagName, attrs, children) ->
        node = $(doc.createElement tagName)
        if attrs?
            if _.isObject attrs and not _.isElement attrs
                node.attr attrs
            else if not children?
                children = attrs

        if children?
            if not _.isArray children
                children = [children]

            for child in children
                if _.isNumber child
                    child = child.toString()
                if _.isString child
                    child = doc.createTextNode child
                node.append child

        return node
