"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2019 Mathieu Pasquet
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.xmlstream import ElementBase, register_stanza_plugin


class Reactions(ElementBase):
    name = 'reactions'
    plugin_attrib = 'reactions'
    namespace = 'urn:xmpp:reactions:0'
    interfaces = {'to'}


class Reaction(ElementBase):
    name = 'reaction'
    namespace = 'urn:xmpp:reactions:0'
    interfaces = {'value'}

    def get_value(self) -> str:
        return self.xml.text

    def set_value(self, value: str):
        self.xml.text = value


register_stanza_plugin(Reactions, Reaction, iterable=True)
