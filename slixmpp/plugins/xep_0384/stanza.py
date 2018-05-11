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


class Devices(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'list'
    plugin_attrib = 'devices'
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


class Encrypted(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'encrypted'
    plugin_attrib = 'omemo_encrypted'
    interfaces = set()


class Header(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'header'
    plugin_attrib = name
    interfaces = {'sid'}


class Key(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'key'
    plugin_attrib = name
    interfaces = {'rid', 'prekey'}


class IV(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'iv'
    plugin_attrib = name
    interfaces = set()


class Payload(ElementBase):
    namespace = OMEMO_BASE_NS
    name = 'payload'
    plugin_attrib = name
    interfaces = set()


register_stanza_plugin(Message, Encrypted)
register_stanza_plugin(Encrypted, Header)
register_stanza_plugin(Header, Key)
register_stanza_plugin(Header, IV)
register_stanza_plugin(Encrypted, Payload)

register_stanza_plugin(EventItem, Devices)
register_stanza_plugin(Devices, Device, iterable=True)
