"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.xmlstream import ElementBase


class Session(ElementBase):

    """
    """

    name = 'session'
    namespace = 'urn:ietf:params:xml:ns:xmpp-session'
    interfaces = set()
    plugin_attrib = 'session'
