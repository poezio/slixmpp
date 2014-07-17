"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.xmlstream import ElementBase


class PreApproval(ElementBase):

    name = 'sub'
    namespace = 'urn:xmpp:features:pre-approval'
    interfaces = set()
    plugin_attrib = 'preapproval'
