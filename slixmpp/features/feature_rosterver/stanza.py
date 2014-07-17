"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.xmlstream import ElementBase


class RosterVer(ElementBase):

    name = 'ver'
    namespace = 'urn:xmpp:features:rosterver'
    interfaces = set()
    plugin_attrib = 'rosterver'
