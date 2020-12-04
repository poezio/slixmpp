"""
    slixmpp: The Slick XMPP Library
    Copyright (C) 2020 Emmanuel Gil Peyrot
    This file is part of slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from typing import Iterable, Tuple, Optional

from slixmpp import JID, Message
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.plugins.xep_0353 import stanza, Propose, Retract, Accept, Proceed, Reject

log = logging.getLogger(__name__)

class XEP_0353(BasePlugin):

    name = 'xep_0353'
    description = 'XEP-0353: Jingle Message Initiation'
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, Propose)
        register_stanza_plugin(Message, Retract)
        register_stanza_plugin(Message, Accept)
        register_stanza_plugin(Message, Proceed)
        register_stanza_plugin(Message, Reject)

        self.xmpp.register_handler(
            Callback('Indicating Intent to Start a Session',
                StanzaPath('message/propose'),
                self._handle_propose))
        self.xmpp.register_handler(
            Callback('Disavowing Intent to Start a Session',
                StanzaPath('message/retract'),
                self._handle_retract))
        self.xmpp.register_handler(
            Callback('Accepting Intent to Start a Session',
                StanzaPath('message/accept'),
                self._handle_accept))
        self.xmpp.register_handler(
            Callback('Proceed',
                StanzaPath('message/proceed'),
                self._handle_accept))
        self.xmpp.register_handler(
            Callback('Rejecting Intent to Start a Session',
                StanzaPath('message/reject'),
                self._handle_reject))

    def _handle_propose(self, message):
        self.xmpp.event('jingle_message_propose', message)

    def _handle_retract(self, message):
        self.xmpp.event('jingle_message_retract', message)

    def _handle_accept(self, message):
        self.xmpp.event('jingle_message_accept', message)

    def _handle_proceed(self, message):
        self.xmpp.event('jingle_message_proceed', message)

    def _handle_reject(self, message):
        self.xmpp.event('jingle_message_reject', message)

    def propose(self, mto: JID, sid: str, descriptions: Iterable[Tuple[str, str]], *, mfrom: Optional[JID] = None):
        msg = self.xmpp.Message()
        msg['to'] = mto
        msg['from'] = mfrom
        msg['jingle_propose']['id'] = sid
        msg['jingle_propose']['descriptions'] = descriptions

    def retract(self, mto: JID, sid: str, *, mfrom: Optional[JID] = None):
        msg = self.xmpp.Message()
        msg['to'] = mto
        msg['from'] = mfrom
        msg['jingle_retract']['id'] = sid

    def accept(self, mto: JID, sid: str, *, mfrom: Optional[JID] = None):
        msg = self.xmpp.Message()
        msg['to'] = mto
        msg['from'] = mfrom
        msg['jingle_accept']['id'] = sid

    def proceed(self, mto: JID, sid: str, *, mfrom: Optional[JID] = None):
        msg = self.xmpp.Message()
        msg['to'] = mto
        msg['from'] = mfrom
        msg['jingle_proceed']['id'] = sid

    def reject(self, mto: JID, sid: str, *, mfrom: Optional[JID] = None):
        msg = self.xmpp.Message()
        msg['to'] = mto
        msg['from'] = mfrom
        msg['jingle_reject']['id'] = sid
