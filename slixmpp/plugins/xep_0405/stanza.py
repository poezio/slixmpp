"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2020 Mathieu Pasquet <mathieui@mathieui.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permissio
"""

from slixmpp import JID
from slixmpp.stanza import Iq
from slixmpp.xmlstream import (
    ElementBase,
    register_stanza_plugin,
)

from slixmpp.plugins.xep_0369.stanza import (
    Join,
    Leave,
)

NS = 'urn:xmpp:mix:pam:2'


class ClientJoin(ElementBase):
    namespace = NS
    name = 'client-join'
    plugin_attrib = 'client_join'
    interfaces = {'channel'}


class ClientLeave(ElementBase):
    namespace = NS
    name = 'client-leave'
    plugin_attrib = 'client_leave'
    interfaces = {'channel'}


def register_plugins():
    register_stanza_plugin(Iq, ClientJoin)
    register_stanza_plugin(ClientJoin, Join)

    register_stanza_plugin(Iq, ClientLeave)
    register_stanza_plugin(ClientLeave, Leave)
