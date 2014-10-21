#coding=utf-8
from uliweb import expose, functions
from uliweb.utils.common import log
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin

@expose('/')
def index():
    return {}

@expose('/test')
def test():
    return 'ok'

class ChatNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    nicknames = {}

    def initialize(self):
#        self.logger = app.logger
        self.log("Socketio session started")

    def log(self, message):
        log.info("[{0}] {1}".format(self.socket.sessid, message))

    def on_join(self, room):
        self.room = room
        self.join(room)
        return True

    def on_nickname(self, nickname):
        self.log('Nickname: {0}'.format(nickname))
        self.nicknames[nickname] = self.socket
        self.session['nickname'] = nickname
        self.broadcast_event('announcement', '%s has connected' % nickname)
        self.broadcast_event('nicknames', self.nicknames.keys())
        self.room = 'main_room'
        self.join('main_room')

    def recv_disconnect(self):
        # Remove nickname from the list.
        self.log('Disconnected')
        nickname = self.session.get('nickname')
        if nickname:
            del self.nicknames[nickname]
        self.broadcast_event('announcement', '%s has disconnected' % nickname)
        self.broadcast_event('nicknames', self.nicknames.keys())
        self.disconnect(silent=True)
        return True

    def on_user_message(self, nickname, msg):
        self.log('User message: {0}'.format(msg))
        print nickname
        if nickname == "All":   # 群聊
            self.emit_to_room(self.room, 'msg_to_room',
                              self.session['nickname'], msg)
        else:                   # 私聊
            pkt = dict(type="event",
                       name="announcement",
                       args=msg,
                       endpoint=self.ns_name)
        
            client_sock = self.nicknames[nickname]
            client_sock.send_packet(pkt)

        return True


@expose('/socket.io/<path:path>')
def socketio(path):
    try:
        socketio_manage(request.environ, {'/chat': ChatNamespace}, request)
    except:
        log.exception("Exception while handling socketio connection")
    return response
    
