#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 Maxime “pep” Buquet <pep@bouah.net>
#
# Distributed under terms of the MIT license.

"""
    OMEMO Plugin
"""

import logging

from slixmpp.jid import JID
from slixmpp.plugins.xep_0060.stanza.pubsub_event import EventItem
from slixmpp.plugins.base import BasePlugin, register_plugin
from slixmpp.xmlstream import register_stanza_plugin, ElementBase


log = logging.getLogger(__name__)

OMEMO_BASE_NS = 'eu.siacs.conversations.axolotl'
OMEMO_DEVICES_NS = OMEMO_BASE_NS + '.devicelist'
OMEMO_BUNDLE_NS = OMEMO_BASE_NS + '.bundle'


class ItemList(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'list'
    plugin_attrib = name
    interfaces = set()


class Device(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'device'
    plugin_attrib = name
    interfaces = {'id'}

    def get_payload(self):
        children = list(self.xml)
        if len(children) > 0:
            return children[0]


class XEP_0384(BasePlugin):

    """
    XEP-0384: OMEMO
    """

    name = 'xep_0384'
    description = 'XEP-0384 OMEMO'
    dependencies = {'xep_0163'}

    device_ids = {}

    def plugin_init(self):
        self.xmpp.add_event_handler('pubsub_publish', self.device_list)

    def plugin_end(self):
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
            device_ids = [d['id'] for d in item['list']]
            if jid not in self.device_ids:
                self.device_ids[jid] = device_ids
            self.xmpp.event('omemo_device_ids', (jid, device_ids))

            # XXX: There should only be one item so this is fine, but slixmpp
            # loops forever otherwise. ???
            return


register_stanza_plugin(EventItem, ItemList)
register_stanza_plugin(ItemList, Device, iterable=True)
register_plugin(XEP_0384)
