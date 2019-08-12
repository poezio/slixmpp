"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2019 Mathieu Pasquet
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.xmlstream import ElementBase


class OccupantID(ElementBase):
    name = 'occupant-id'
    plugin_attrib = 'occupant-id'
    namespace = 'urn:xmpp:occupant-id:0'
    interfaces = {'id'}
