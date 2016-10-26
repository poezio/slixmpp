"""
    slixmpp: The Slick XMPP Library
    Copyright (C) 2016 Emmanuel Gil Peyrot
    This file is part of slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp import Message
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.plugins.xep_0333 import stanza, Markable, Received, Displayed, Acknowledged

log = logging.getLogger(__name__)

class XEP_0333(BasePlugin):

    name = 'xep_0333'
    description = 'XEP-0333: Chat Markers'
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, Markable)
        register_stanza_plugin(Message, Received)
        register_stanza_plugin(Message, Displayed)
        register_stanza_plugin(Message, Acknowledged)

        self.xmpp.register_handler(
            Callback('Received Chat Marker',
                StanzaPath('message/received'),
                self._handle_received))
        self.xmpp.register_handler(
            Callback('Displayed Chat Marker',
                StanzaPath('message/displayed'),
                self._handle_displayed))
        self.xmpp.register_handler(
            Callback('Acknowledged Chat Marker',
                StanzaPath('message/acknowledged'),
                self._handle_acknowledged))

    def _handle_received(self, message):
        self.xmpp.event('marker_received', message)
        self.xmpp.event('marker', message)

    def _handle_displayed(self, message):
        self.xmpp.event('marker_displayed', message)
        self.xmpp.event('marker', message)

    def _handle_acknowledged(self, message):
        self.xmpp.event('marker_acknowledged', message)
        self.xmpp.event('marker', message)
