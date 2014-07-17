"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.xmlstream import ElementBase, register_stanza_plugin


class Reachability(ElementBase):
    name = 'reach'
    namespace = 'urn:xmpp:reach:0'
    plugin_attrib = 'reach'
    interfaces = set()


class Address(ElementBase):
    name = 'addr'
    namespace = 'urn:xmpp:reach:0'
    plugin_attrib = 'address'
    plugin_multi_attrib = 'addresses'
    interfaces = set(['uri', 'desc'])
    lang_interfaces = set(['desc'])
    sub_interfaces = set(['desc'])


register_stanza_plugin(Reachability, Address, iterable=True)
