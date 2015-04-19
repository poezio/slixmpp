import asyncio
import uuid
import logging

from slixmpp import Message, Iq
from slixmpp.exceptions import XMPPError
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins import BasePlugin
from slixmpp.plugins.xep_0047 import stanza, Open, Close, Data, IBBytestream


log = logging.getLogger(__name__)


class XEP_0047(BasePlugin):

    name = 'xep_0047'
    description = 'XEP-0047: In-band Bytestreams'
    dependencies = set(['xep_0030'])
    stanza = stanza
    default_config = {
        'block_size': 4096,
        'max_block_size': 8192,
        'auto_accept': False,
    }

    def plugin_init(self):
        self._streams = {}
        self._preauthed_sids = {}

        register_stanza_plugin(Iq, Open)
        register_stanza_plugin(Iq, Close)
        register_stanza_plugin(Iq, Data)
        register_stanza_plugin(Message, Data)

        self.xmpp.register_handler(Callback(
            'IBB Open',
            StanzaPath('iq@type=set/ibb_open'),
            self._handle_open_request))

        self.xmpp.register_handler(Callback(
            'IBB Close',
            StanzaPath('iq@type=set/ibb_close'),
            self._handle_close))

        self.xmpp.register_handler(Callback(
            'IBB Data',
            StanzaPath('iq@type=set/ibb_data'),
            self._handle_data))

        self.xmpp.register_handler(Callback(
            'IBB Message Data',
            StanzaPath('message/ibb_data'),
            self._handle_data))

        self.api.register(self._authorized, 'authorized', default=True)
        self.api.register(self._authorized_sid, 'authorized_sid', default=True)
        self.api.register(self._preauthorize_sid, 'preauthorize_sid', default=True)
        self.api.register(self._get_stream, 'get_stream', default=True)
        self.api.register(self._set_stream, 'set_stream', default=True)
        self.api.register(self._del_stream, 'del_stream', default=True)

    def plugin_end(self):
        self.xmpp.remove_handler('IBB Open')
        self.xmpp.remove_handler('IBB Close')
        self.xmpp.remove_handler('IBB Data')
        self.xmpp.remove_handler('IBB Message Data')
        self.xmpp['xep_0030'].del_feature(feature='http://jabber.org/protocol/ibb')

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature('http://jabber.org/protocol/ibb')

    def _get_stream(self, jid, sid, peer_jid, data):
        return self._streams.get((jid, sid, peer_jid), None)

    def _set_stream(self, jid, sid, peer_jid, stream):
        self._streams[(jid, sid, peer_jid)] = stream

    def _del_stream(self, jid, sid, peer_jid, data):
        if (jid, sid, peer_jid) in self._streams:
            del self._streams[(jid, sid, peer_jid)]

    def _accept_stream(self, iq):
        receiver = iq['to']
        sender = iq['from']
        sid = iq['ibb_open']['sid']

        if self.api['authorized_sid'](receiver, sid, sender, iq):
            return True
        return self.api['authorized'](receiver, sid, sender, iq)

    def _authorized(self, jid, sid, ifrom, iq):
        if self.auto_accept:
            return True
        return False

    def _authorized_sid(self, jid, sid, ifrom, iq):
        if (jid, sid, ifrom) in self._preauthed_sids:
            del self._preauthed_sids[(jid, sid, ifrom)]
            return True
        return False

    def _preauthorize_sid(self, jid, sid, ifrom, data):
        self._preauthed_sids[(jid, sid, ifrom)] = True

    def open_stream(self, jid, block_size=None, sid=None, use_messages=False,
                    ifrom=None, timeout=None, callback=None):
        if sid is None:
            sid = str(uuid.uuid4())
        if block_size is None:
            block_size = self.block_size

        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = jid
        iq['from'] = ifrom
        iq['ibb_open']['block_size'] = block_size
        iq['ibb_open']['sid'] = sid
        iq['ibb_open']['stanza'] = 'message' if use_messages else 'iq'

        stream = IBBytestream(self.xmpp, sid, block_size,
                              iq['from'], iq['to'], use_messages)

        stream_future = asyncio.Future()

        def _handle_opened_stream(iq):
            log.debug('IBB stream (%s) accepted by %s', stream.sid, iq['from'])
            stream.self_jid = iq['to']
            stream.peer_jid = iq['from']
            stream.stream_started = True
            self.api['set_stream'](stream.self_jid, stream.sid, stream.peer_jid, stream)
            stream_future.set_result(stream)
            if callback is not None:
                callback(stream)
            self.xmpp.event('ibb_stream_start', stream)
            self.xmpp.event('stream:%s:%s' % (stream.sid, stream.peer_jid), stream)

        iq.send(timeout=timeout, callback=_handle_opened_stream)

        return stream_future

    def _handle_open_request(self, iq):
        sid = iq['ibb_open']['sid']
        size = iq['ibb_open']['block_size'] or self.block_size

        log.debug('Received IBB stream request from %s', iq['from'])

        if not sid:
            raise XMPPError(etype='modify', condition='bad-request')

        if not self._accept_stream(iq):
            raise XMPPError(etype='cancel', condition='not-acceptable')

        if size > self.max_block_size:
            raise XMPPError('resource-constraint')

        stream = IBBytestream(self.xmpp, sid, size,
                              iq['to'], iq['from'])
        stream.stream_started = True
        self.api['set_stream'](stream.self_jid, stream.sid, stream.peer_jid, stream)
        iq.reply().send()

        self.xmpp.event('ibb_stream_start', stream)
        self.xmpp.event('stream:%s:%s' % (sid, stream.peer_jid), stream)

    def _handle_data(self, stanza):
        sid = stanza['ibb_data']['sid']
        stream = self.api['get_stream'](stanza['to'], sid, stanza['from'])
        if stream is not None and stanza['from'] == stream.peer_jid:
            stream._recv_data(stanza)
        else:
            raise XMPPError('item-not-found')

    def _handle_close(self, iq):
        sid = iq['ibb_close']['sid']
        stream = self.api['get_stream'](iq['to'], sid, iq['from'])
        if stream is not None and iq['from'] == stream.peer_jid:
            stream._closed(iq)
            self.api['del_stream'](stream.self_jid, stream.sid, stream.peer_jid)
        else:
            raise XMPPError('item-not-found')
