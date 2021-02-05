
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2020 Mathieu Pasquet <mathieui@mathieui.net>
# This file is part of Slixmpp.
# See the file LICENSE for copying permissio
from slixmpp.stanza import Message, Iq
from slixmpp.xmlstream import (
    ElementBase,
    register_stanza_plugin,
)
from slixmpp.plugins.xep_0422.stanza import ApplyTo
from slixmpp.plugins.xep_0421.stanza import OccupantId
from slixmpp.plugins.xep_0424.stanza import Retract, Retracted


NS = 'urn:xmpp:message-moderate:0'


class Moderate(ElementBase):
    namespace = NS
    name = 'moderate'
    plugin_attrib = 'moderate'
    interfaces = {'reason'}
    sub_interfaces = {'reason'}


class Moderated(ElementBase):
    namespace = NS
    name = 'moderated'
    plugin_attrib = 'moderated'
    interfaces = {'reason', 'by'}
    sub_interfaces = {'reason'}


def register_plugins():
    register_stanza_plugin(Iq, ApplyTo)
    register_stanza_plugin(ApplyTo, Moderate)
    register_stanza_plugin(Moderate, Retract)

    register_stanza_plugin(Message, Moderated)
    register_stanza_plugin(ApplyTo, Moderated)
    register_stanza_plugin(Moderated, Retract)
    register_stanza_plugin(Moderated, Retracted)
    register_stanza_plugin(Moderated, OccupantId)
