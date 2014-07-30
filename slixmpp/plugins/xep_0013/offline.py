"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permissio
"""

import logging

import slixmpp
from slixmpp.stanza import Message, Iq
from slixmpp.exceptions import XMPPError
from slixmpp.xmlstream.handler import Collector
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins import BasePlugin
from slixmpp.plugins.xep_0013 import stanza


log = logging.getLogger(__name__)


class XEP_0013(BasePlugin):

    """
    XEP-0013 Flexible Offline Message Retrieval
    """

    name = 'xep_0013'
    description = 'XEP-0013: Flexible Offline Message Retrieval'
    dependencies = set(['xep_0030'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Iq, stanza.Offline)
        register_stanza_plugin(Message, stanza.Offline)

    def get_count(self, **kwargs):
        return self.xmpp['xep_0030'].get_info(
                node='http://jabber.org/protocol/offline',
                local=False,
                **kwargs)

    def get_headers(self, **kwargs):
        return self.xmpp['xep_0030'].get_items(
                node='http://jabber.org/protocol/offline',
                local=False,
                **kwargs)

    def view(self, nodes, ifrom=None, timeout=None, callback=None,
             timeout_callback=None):
        if not isinstance(nodes, (list, set)):
            nodes = [nodes]

        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['from'] = ifrom
        offline = iq['offline']
        for node in nodes:
            item = stanza.Item()
            item['node'] = node
            item['action'] = 'view'
            offline.append(item)

        collector = Collector(
            'Offline_Results_%s' % iq['id'],
            StanzaPath('message/offline'))
        self.xmpp.register_handler(collector)

        def wrapped_cb(iq):
            results = collector.stop()
            if iq['type'] == 'result':
                iq['offline']['results'] = results
            callback(iq)
        iq.send(timeout=timeout, callback=wrapped_cb,
                       timeout_callback=timeout_callback)

    def remove(self, nodes, ifrom=None, timeout=None, callback=None,
               timeout_callback=None):
        if not isinstance(nodes, (list, set)):
            nodes = [nodes]

        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['from'] = ifrom
        offline = iq['offline']
        for node in nodes:
            item = stanza.Item()
            item['node'] = node
            item['action'] = 'remove'
            offline.append(item)

        iq.send(timeout=timeout, callback=callback,
                timeout_callback=timeout_callback)

    def fetch(self, ifrom=None, timeout=None, callback=None,
              timeout_callback=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['from'] = ifrom
        iq['offline']['fetch'] = True

        collector = Collector(
            'Offline_Results_%s' % iq['id'],
            StanzaPath('message/offline'))
        self.xmpp.register_handler(collector)

        def wrapped_cb(iq):
            results = collector.stop()
            if iq['type'] == 'result':
                iq['offline']['results'] = results
            callback(iq)
        iq.send(timeout=timeout, callback=wrapped_cb,
                timeout_callback=timeout_callback)

    def purge(self, ifrom=None, timeout=None, callback=None,
              timeout_callback=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['from'] = ifrom
        iq['offline']['purge'] = True
        iq.send(timeout=timeout, callback=callback,
                timeout_callback=timeout_callback)
