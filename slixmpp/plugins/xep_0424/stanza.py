
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2020 Mathieu Pasquet <mathieui@mathieui.net>
# This file is part of Slixmpp.
# See the file LICENSE for copying permissio
from slixmpp.stanza import Message
from slixmpp.xmlstream import (
    ElementBase,
    register_stanza_plugin,
)
from slixmpp.plugins.xep_0422.stanza import ApplyTo
from slixmpp.plugins.xep_0359 import OriginID


NS = 'urn:xmpp:message-retract:0'


class Retract(ElementBase):
    namespace = NS
    name = 'retract'
    plugin_attrib = 'retract'


class Retracted(ElementBase):
    namespace = NS
    name = 'retracted'
    plugin_attrib = 'retracted'
    interfaces = {'stamp'}


def register_plugins():
    register_stanza_plugin(ApplyTo, Retract)
    register_stanza_plugin(Message, Retracted)

    register_stanza_plugin(Retracted, OriginID)
