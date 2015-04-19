import asyncio
import socket
import logging

from slixmpp.stanza import Iq
from slixmpp.exceptions import XMPPError


log = logging.getLogger(__name__)


class IBBytestream(object):

    def __init__(self, xmpp, sid, block_size, jid, peer, use_messages=False):
        self.xmpp = xmpp
        self.sid = sid
        self.block_size = block_size
        self.use_messages = use_messages

        if jid is None:
            jid = xmpp.boundjid
        self.self_jid = jid
        self.peer_jid = peer

        self.send_seq = -1
        self.recv_seq = -1

        self.stream_started = False
        self.stream_in_closed = False
        self.stream_out_closed = False

        self.recv_queue = asyncio.Queue()

    @asyncio.coroutine
    def send(self, data, timeout=None):
        if not self.stream_started or self.stream_out_closed:
            raise socket.error
        if len(data) > self.block_size:
            data = data[:self.block_size]
        self.send_seq = (self.send_seq + 1) % 65535
        seq = self.send_seq
        if self.use_messages:
            msg = self.xmpp.Message()
            msg['to'] = self.peer_jid
            msg['from'] = self.self_jid
            msg['id'] = self.xmpp.new_id()
            msg['ibb_data']['sid'] = self.sid
            msg['ibb_data']['seq'] = seq
            msg['ibb_data']['data'] = data
            msg.send()
        else:
            iq = self.xmpp.Iq()
            iq['type'] = 'set'
            iq['to'] = self.peer_jid
            iq['from'] = self.self_jid
            iq['ibb_data']['sid'] = self.sid
            iq['ibb_data']['seq'] = seq
            iq['ibb_data']['data'] = data
            yield from iq.send(timeout=timeout)
        return len(data)

    @asyncio.coroutine
    def sendall(self, data, timeout=None):
        sent_len = 0
        while sent_len < len(data):
            sent_len += yield from self.send(data[sent_len:self.block_size], timeout=timeout)

    @asyncio.coroutine
    def sendfile(self, file, timeout=None):
        while True:
            data = file.read(self.block_size)
            if not data:
                break
            yield from self.send(data, timeout=timeout)

    def _recv_data(self, stanza):
        new_seq = stanza['ibb_data']['seq']
        if new_seq != (self.recv_seq + 1) % 65535:
            self.close()
            raise XMPPError('unexpected-request')
        self.recv_seq = new_seq

        data = stanza['ibb_data']['data']
        if len(data) > self.block_size:
            self.close()
            raise XMPPError('not-acceptable')

        self.recv_queue.put_nowait(data)
        self.xmpp.event('ibb_stream_data', self)

        if isinstance(stanza, Iq):
            stanza.reply().send()

    def recv(self, *args, **kwargs):
        return self.read()

    def read(self):
        if not self.stream_started or self.stream_in_closed:
            raise socket.error
        return self.recv_queue.get_nowait()

    def close(self, timeout=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = self.peer_jid
        iq['from'] = self.self_jid
        iq['ibb_close']['sid'] = self.sid
        self.stream_out_closed = True
        def _close_stream(_):
            self.stream_in_closed = True
        future = iq.send(timeout=timeout, callback=_close_stream)
        self.xmpp.event('ibb_stream_end', self)
        return future

    def _closed(self, iq):
        self.stream_in_closed = True
        self.stream_out_closed = True
        iq.reply().send()
        self.xmpp.event('ibb_stream_end', self)

    def makefile(self, *args, **kwargs):
        return self

    def connect(*args, **kwargs):
        return None

    def shutdown(self, *args, **kwargs):
        return None
