"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Maxime “pep” Buquet <pep@bouah.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp import Message
from slixmpp.plugins.xep_0060.stanza.pubsub_event import EventItem
from slixmpp.xmlstream import register_stanza_plugin, ElementBase

OMEMO_BASE_NS = 'eu.siacs.conversations.axolotl'
OMEMO_DEVICES_NS = OMEMO_BASE_NS + '.devicelist'
OMEMO_BUNDLE_NS = OMEMO_BASE_NS + '.bundle'


class ItemList(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'list'
    plugin_attrib = 'list'
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


register_stanza_plugin(EventItem, ItemList)
register_stanza_plugin(ItemList, Device, iterable=True)
