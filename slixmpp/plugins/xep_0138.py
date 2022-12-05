import logging
import zlib

from slixmpp.stanza import StreamFeatures
from slixmpp.xmlstream import register_stanza_plugin, ElementBase, StanzaBase, tostring
from slixmpp.xmlstream.matcher import *
from slixmpp.xmlstream.handler import *
from slixmpp.plugins import BasePlugin, register_plugin

log = logging.getLogger(__name__)

class Compression(ElementBase):
    name = 'compression'
    namespace = 'http://jabber.org/features/compress'
    interfaces = {'methods'}
    plugin_attrib = 'compression'
    plugin_tag_map = {}
    plugin_attrib_map = {}

    def get_methods(self):
        methods = []
        for method in self.xml.findall('{%s}method' % self.namespace):
            methods.append(method.text)
        return methods


class Compress(StanzaBase):
    name = 'compress'
    namespace = 'http://jabber.org/protocol/compress'
    interfaces = {'method'}
    sub_interfaces = interfaces
    plugin_attrib = 'compress'
    plugin_tag_map = {}
    plugin_attrib_map = {}

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()

    def set_method(self, method):
        self._set_sub_text('{}method', text=method)

class Compressed(StanzaBase):
    name = 'compressed'
    namespace = 'http://jabber.org/protocol/compress'
    interfaces = set()
    plugin_tag_map = {}
    plugin_attrib_map = {}

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()

class CompressFailure(StanzaBase):
    name = 'failure'
    namespace = 'http://jabber.org/protocol/compress'
    conditions = {'setup-failed', 'unsupported-method'}

    def setup(self, xml):
        StanzaBase.setup(self, xml)
        self.xml.tag = self.tag_name()

    def get_condition(self):
        """Return the condition element's name."""
        for child in self.xml:
            return child.tag.split('}', 1)[-1]

class XEP_0138(BasePlugin):
    """
    XEP-0138: Compression
    """
    name = "xep_0138"
    description = "XEP-0138: Compression"
    dependencies = {"xep_0030"}

    def plugin_init(self):
        self.xep = '0138'
        self.description = 'Stream Compression (Generic)'

        self.compression_methods = {'zlib': True}

        register_stanza_plugin(StreamFeatures, Compression)
        self.xmpp.register_stanza(CompressFailure)
        self.xmpp.register_stanza(Compress)
        self.xmpp.register_stanza(Compressed)

        self.xmpp.register_handler(
                Callback('Compressed',
                    StanzaPath('compressed'),
                    self._handle_compressed,
                    instream=True))

        self.xmpp.register_handler(
                Callback('CompressFailure',
                    StanzaPath('failure'),
                    self._handle_failure,
                    instream=True))

        self.xmpp.register_feature('compression',
                self._handle_compression,
                restart=True,
                order=self.config.get('order', 5))

        self.stats = {
            'rx-compress': 0,
            'tx-compress': 0,
            'rx-real': 0,
            'tx-real': 0,
        }
        self.xmpp.add_event_handler('disconnected', lambda _: log.debug("Compression stats %r" % self.stats))

    def register_compression_method(self, name, handler):
        self.compression_methods[name] = handler

    def _handle_compression(self, features):
        for method in features['compression']['methods']:
            if method in self.compression_methods:
                log.info('Attempting to use %s compression' % method)
                c = Compress(self.xmpp)
                c.set_method(method)
                str_data = tostring(c.xml, stream=self.xmpp, top_level=True)
                self.xmpp.send(c)

                return True
        return False

    def _decorate_transport(self, transport):
        compressor = zlib.compressobj()
        decompressor = zlib.decompressobj(zlib.MAX_WBITS)

        orig_recv = self.xmpp.data_received
        def zlib_recv(data):
            #log.debug('zlib: received %s' % data)
            plain = decompressor.decompress(decompressor.unconsumed_tail + data)
            log.debug("zlib: decompressed %d bytes into %d" % (len(data), len(plain)))
            self.stats['rx-compress'] += len(data)
            self.stats['rx-real'] += len(plain)
            orig_recv(plain)
        self.xmpp.data_received = zlib_recv

        orig_write = transport.write
        def zlib_write(data):
            compressed = compressor.compress(data) + compressor.flush(zlib.Z_SYNC_FLUSH)
            log.debug("zlib: compressed %d bytes into %d" % (len(data), len(compressed)))
            #log.debug('zlib: sent %s' % compressed)
            self.stats['tx-compress'] += len(compressed)
            self.stats['tx-real'] += len(data)
            return orig_write(compressed)
        transport.write = zlib_write

        return transport

    def _handle_compressed(self, stanza):
        self.xmpp.features.add('compression')
        log.debug('Stream Compressed!')
        self.xmpp.event_when_connected = 'zlib_enabled'
        self.xmpp.connection_made(self._decorate_transport(self.xmpp.transport))

    def _handle_failure(self, stanza):
        # TODO - feature processing needs a restart
        print("failure %s" % stanza.get_condition())

xep_0138 = XEP_0138
register_plugin(XEP_0138)
