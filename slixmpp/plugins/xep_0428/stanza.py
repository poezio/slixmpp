
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2020 Mathieu Pasquet <mathieui@mathieui.net>
# This file is part of Slixmpp.
# See the file LICENSE for copying permissio
from slixmpp.stanza import Message
from slixmpp.xmlstream import (
    ElementBase,
    register_stanza_plugin,
)


NS = 'urn:xmpp:fallback:0'


class Fallback(ElementBase):
    namespace = NS
    name = 'fallback'
    plugin_attrib = 'fallback'


def register_plugins():
    register_stanza_plugin(Message, Fallback)
