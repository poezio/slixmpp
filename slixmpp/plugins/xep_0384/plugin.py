"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Maxime “pep” Buquet <pep@bouah.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

import base64
import asyncio
from slixmpp.plugins.xep_0384.stanza import OMEMO_BASE_NS
from slixmpp.plugins.xep_0384.stanza import OMEMO_DEVICES_NS, OMEMO_BUNDLE_NS
from slixmpp.plugins.xep_0384.stanza import Devices, Device
from slixmpp.plugins.base import BasePlugin, register_plugin

log = logging.getLogger(__name__)

HAS_OMEMO = True
try:
    import omemo
    from slixmpp.plugins.xep_0384.session import SessionManager
except ImportError as e:
    HAS_OMEMO = False


def b64enc(data):
    return base64.b64encode(bytes(bytearray(data))).decode('ASCII')


def b64dec(data):
    return base64.b64decode(data.decode('ASCII'))


class XEP_0384(BasePlugin):

    """
    XEP-0384: OMEMO
    """

    name = 'xep_0384'
    description = 'XEP-0384 OMEMO'
    dependencies = {'xep_0163'}
    default_config = {
        'cache_dir': None,
    }

    backend_loaded = HAS_OMEMO

    device_ids = {}

    def plugin_init(self):
        if not self.backend_loaded:
            log.debug("xep_0384 cannot be loaded as the backend omemo library "
                      "is not available")
            return

        self._omemo = SessionManager(
            self.xmpp.boundjid,
            self.cache_dir,
        )
        self._device_id = self._omemo.get_own_device_id()

        self.xmpp.add_event_handler('pubsub_publish', self._get_device_list)

        asyncio.ensure_future(self._set_device_list())

    def plugin_end(self):
        if not self.backend_loaded:
            return

        self.xmpp.del_event_handler('pubsub_publish', self._get_device_list)
        self.xmpp['xep_0163'].remove_interest(OMEMO_DEVICES_NS)

    def session_bind(self, _jid):
        self.xmpp['xep_0163'].add_interest(OMEMO_DEVICES_NS)

    def _store_device_ids(self, jid, items):
        self.device_ids[jid] = []
        for item in items:
            device_ids = [int(d['id']) for d in item['devices']]
            self.device_ids[jid] = device_ids

            # XXX: There should only be one item so this is fine, but slixmpp
            # loops forever otherwise. ???
            break

    def _get_device_list(self, msg):
        if msg['pubsub_event']['items']['node'] != OMEMO_DEVICES_NS:
            return

        jid = msg['from'].bare
        items = msg['pubsub_event']['items']
        self._store_device_ids(jid, items)

        if jid == self.xmpp.boundjid.bare and \
           self._device_id not in self.device_ids[jid]:
            asyncio.ensure_future(self._set_device_list())

    async def _set_device_list(self):
        iq = await self.xmpp['xep_0060'].get_items(
            self.xmpp.boundjid.bare, OMEMO_DEVICES_NS,
        )
        jid = self.xmpp.boundjid.bare
        items = iq['pubsub']['items']
        self._store_device_ids(jid, items)

        # Verify that this device in the list and set it if necessary
        if self._device_id in self.device_ids[jid]:
            return

        self.device_ids[jid].append(self._device_id)

        devices = []
        for i in self.device_ids[jid]:
            d = Device()
            d['id'] = str(i)
            devices.append(d)
        payload = Devices()
        payload['devices'] = devices

        await self.xmpp['xep_0060'].publish(
            jid, OMEMO_DEVICES_NS, payload=payload,
        )

register_plugin(XEP_0384)
