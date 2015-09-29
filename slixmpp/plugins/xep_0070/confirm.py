"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2015 Emmanuel Gil Peyrot
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import asyncio
import logging

from slixmpp.plugins import BasePlugin, register_plugin
from slixmpp import future_wrapper, Iq, Message
from slixmpp.exceptions import XMPPError, IqError, IqTimeout
from slixmpp.xmlstream import JID, register_stanza_plugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.plugins.xep_0070 import stanza, Confirm


log = logging.getLogger(__name__)


class XEP_0070(BasePlugin):

    """
    XEP-0070 Verifying HTTP Requests via XMPP
    """

    name = 'xep_0070'
    description = 'XEP-0070: Verifying HTTP Requests via XMPP'
    dependencies = {'xep_0030'}
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Iq, Confirm)
        register_stanza_plugin(Message, Confirm)

        self.xmpp.register_handler(
            Callback('Confirm',
                 StanzaPath('iq@type=get/confirm'),
                 self._handle_iq_confirm))

        self.xmpp.register_handler(
            Callback('Confirm',
                 StanzaPath('message/confirm'),
                 self._handle_message_confirm))

        #self.api.register(self._default_get_confirm,
        #        'get_confirm',
        #        default=True)

    def plugin_end(self):
        self.xmpp.remove_handler('Confirm')
        self.xmpp['xep_0030'].del_feature(feature='http://jabber.org/protocol/http-auth')

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature('http://jabber.org/protocol/http-auth')

    def ask_confirm(self, jid, id, url, method, *, ifrom=None, message=None):
        if message is None:
            stanza = self.xmpp.Iq()
            stanza['type'] = 'get'
        else:
            stanza = self.xmpp.Message()
        stanza['from'] = ifrom
        stanza['to'] = jid
        stanza['confirm']['id'] = id
        stanza['confirm']['url'] = url
        stanza['confirm']['method'] = method
        if message is not None:
            stanza['body'] = message.format(id=id, url=url, method=method)
            stanza.send()
        else:
            try:
                yield from stanza.send()
            except IqError:
                return False
            except IqTimeout:
                return False
            else:
                return True

    def _handle_iq_confirm(self, iq):
        emitter = iq['from']
        id = iq['confirm']['id']
        url = iq['confirm']['url']
        method = iq['confirm']['method']
        accept = self.api['get_confirm'](emitter, id, url, method)
        if not accept:
            raise XMPPError(etype='auth', condition='not-authorized')

        iq.reply().send()

    def _handle_message_confirm(self, message):
        emitter = message['from']
        id = message['confirm']['id']
        url = message['confirm']['url']
        method = message['confirm']['method']
        accept = self.api['get_confirm'](emitter, id, url, method)
        if not accept:
            raise XMPPError(etype='auth', condition='not-authorized')

        message.reply().send()

    #def _default_get_confirm(self, jid, id, url, method):
    #    return False
