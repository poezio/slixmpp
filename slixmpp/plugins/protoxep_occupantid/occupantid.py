"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2019 Mathieu Pasquet
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""
from slixmpp.plugins import BasePlugin
from slixmpp.stanza import Message, Presence
from slixmpp.xmlstream import register_stanza_plugin

from slixmpp.plugins.protoxep_occupantid import stanza


class XEP_OccupantID(BasePlugin):
    name = 'protoxep_occupantid'
    description = 'XEP-XXXX: Anonymous unique occupant identifiers for MUCs'
    dependencies = set()
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, stanza.OccupantID)
        register_stanza_plugin(Presence, stanza.OccupantID)
