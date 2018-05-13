"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Maxime “pep” Buquet <pep@bouah.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp.jid import JID
from slixmpp.plugins.xep_0384.stanza import OMEMO_BASE_NS
from slixmpp.plugins.xep_0384.stanza import OMEMO_DEVICES_NS, OMEMO_BUNDLE_NS
from slixmpp.plugins.base import BasePlugin, register_plugin

log = logging.getLogger(__name__)

HAS_OMEMO = True
try:
    import omemo
except ImportError as e:
    HAS_OMEMO = False


class XEP_0384(BasePlugin):

    """
    XEP-0384: OMEMO
    """

    name = 'xep_0384'
    description = 'XEP-0384 OMEMO'
    dependencies = {'xep_0163'}
    backend_loaded = HAS_OMEMO

    device_ids = {}

    def plugin_init(self):
        if not self.backend_loaded:
            log.debug("xep_0384 cannot be loaded as the backend omemo library "
                      "is not available")
            return

        self.xmpp.add_event_handler('pubsub_publish', self.device_list)

    def plugin_end(self):
        if not self.backend_loaded:
            return

        self.xmpp.del_event_handler('pubsub_publish', self.device_list)
        self.xmpp['xep_0163'].remove_interest(OMEMO_DEVICES_NS)

    def session_bind(self, _jid):
        self.xmpp['xep_0163'].add_interest(OMEMO_DEVICES_NS)

    def device_list(self, msg):
        if msg['pubsub_event']['items']['node'] != OMEMO_DEVICES_NS:
            return

        jid = JID(msg['from']).bare
        items = msg['pubsub_event']['items']
        for item in items:
            device_ids = [d['id'] for d in item['devices']]
            if jid not in self.device_ids:
                self.device_ids[jid] = device_ids
            self.xmpp.event('omemo_device_ids', (jid, device_ids))

            # XXX: There should only be one item so this is fine, but slixmpp
            # loops forever otherwise. ???
            return


register_plugin(XEP_0384)
