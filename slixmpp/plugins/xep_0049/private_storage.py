"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp import Iq
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins.xep_0049 import stanza, PrivateXML


log = logging.getLogger(__name__)


class XEP_0049(BasePlugin):

    name = 'xep_0049'
    description = 'XEP-0049: Private XML Storage'
    dependencies = set([])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Iq, PrivateXML)

    def register(self, stanza):
        register_stanza_plugin(PrivateXML, stanza, iterable=True)

    def store(self, data, ifrom=None, timeout=None, callback=None,
              timeout_callback=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['from'] = ifrom

        if not isinstance(data, list):
            data = [data]

        for elem in data:
            iq['private'].append(elem)

        return iq.send(timeout=timeout, callback=callback,
                       timeout_callback=timeout_callback)

    def retrieve(self, name, ifrom=None, timeout=None, callback=None,
                 timeout_callback=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['from'] = ifrom
        iq['private'].enable(name)
        return iq.send(timeout=timeout, callback=callback,
                timeout_callback=timeout_callback)
