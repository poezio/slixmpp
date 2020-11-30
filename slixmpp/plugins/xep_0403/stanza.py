"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2020 Nathanael "Mathieu Pasquet <mathieui@mathieui.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permissio
"""

from xml.etree import ElementTree as ET
from slixmpp import JID
from slixmpp.stanza import (
    Presence,
)
from slixmpp.xmlstream import (
    register_stanza_plugin,
    ElementBase,
)

from slixmpp.plugins.xep_0060.stanza import (
    Item,
    EventItem,
)

NS = 'urn:xmpp:mix:presence:0'

class MIXPresence(ElementBase):
    namespace = NS
    name = 'mix'
    plugin_attrib = 'mix'
    interfaces = {'jid', 'nick'}
    sub_interfaces = {'jid', 'nick'}

    def set_jid(self, jid: JID):
        jids = self.xml.findall('{%s}jid' % self.namespace)
        for jid_item in jids:
            self.xml.remove(jid_item)
        if bool(jid):
            element = ET.Element('{%s}jid' % self.namespace)
            element.text = str(jid)
            self.xml.append(element)


def register_plugins():
    register_stanza_plugin(Presence, MIXPresence)
    register_stanza_plugin(Item, Presence)
    register_stanza_plugin(EventItem, Presence)
