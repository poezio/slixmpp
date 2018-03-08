"""
    slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Emmanuel Gil Peyrot
    This file is part of slixmpp.

    See the file LICENSE for copying permission.
"""

import asyncio
import logging

from slixmpp import Iq
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.plugins.xep_0363 import stanza, Request, Slot, Put, Get, Header

log = logging.getLogger(__name__)

class XEP_0363(BasePlugin):

    name = 'xep_0363'
    description = 'XEP-0363: HTTP File Upload'
    dependencies = {'xep_0030'}
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Iq, Request)
        register_stanza_plugin(Iq, Slot)
        register_stanza_plugin(Slot, Put)
        register_stanza_plugin(Slot, Get)
        register_stanza_plugin(Put, Header)

        self.xmpp.register_handler(
                Callback('HTTP Upload Request',
                         StanzaPath('iq@type=get/http_upload_request'),
                         self._handle_request))

    def plugin_end(self):
        self.xmpp.remove_handler('HTTP Upload Request')
        self.xmpp.remove_handler('HTTP Upload Slot')
        self.xmpp['xep_0030'].del_feature(feature=Request.namespace)

    def session_bind(self, jid):
        self.xmpp.plugin['xep_0030'].add_feature(Request.namespace)

    def _handle_request(self, iq):
        self.xmpp.event('http_upload_request', iq)

    @asyncio.coroutine
    def find_upload_service(self, ifrom=None, timeout=None, callback=None,
                            timeout_callback=None):
        infos = [self.xmpp['xep_0030'].get_info(self.xmpp.boundjid.domain)]
        iq_items = yield from self.xmpp['xep_0030'].get_items(
                self.xmpp.boundjid.domain, timeout=timeout)
        items = iq_items['disco_items']['items']
        infos += [self.xmpp['xep_0030'].get_info(item[0]) for item in items]
        info_futures, _ = yield from asyncio.wait(infos, timeout=timeout)
        for future in info_futures:
            info = future.result()
            for identity in info['disco_info']['identities']:
                if identity[0] == 'store' and identity[1] == 'file':
                    return info

    def request_slot(self, jid, filename, size, content_type=None, ifrom=None,
                     timeout=None, callback=None, timeout_callback=None):
        iq = self.xmpp.Iq()
        iq['to'] = jid
        iq['from'] = ifrom
        iq['type'] = 'get'
        request = iq['http_upload_request']
        request['filename'] = filename
        request['size'] = str(size)
        request['content-type'] = content_type
        return iq.send(timeout=timeout, callback=callback,
                       timeout_callback=timeout_callback)
