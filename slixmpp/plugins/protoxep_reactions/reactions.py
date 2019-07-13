"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2019 Mathieu Pasquet
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""
from typing import Iterable

from slixmpp.plugins import BasePlugin
from slixmpp.stanza import Message
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.matcher import MatchXMLMask
from slixmpp.xmlstream.handler import Callback

from slixmpp.plugins.protoxep_reactions import stanza


class XEP_Reactions(BasePlugin):
    name = 'protoxep_reactions'
    description = 'XEP-XXXX: Message Reactions'
    dependencies = {'xep_0030'}
    stanza = stanza

    def plugin_init(self):
        self.xmpp.register_handler(
            Callback(
                'Reaction received',
                MatchXMLMask('<message><reactions xmlns="urn:xmpp:reactions:0"/></message>'),
                self._handle_reactions,
            )
        )
        self.xmpp['xep_0030'].add_feature('urn:xmpp:reactions:0')
        register_stanza_plugin(Message, stanza.Reactions)

    def plugin_end(self):
        self.xmpp.remove_handler('Reaction received')
        self.xmpp['xep_0030'].remove_feature('urn:xmpp:reactions:0')

    def _handle_reactions(self, message: Message):
        self.xmpp.event('reactions', message)

    @staticmethod
    def set_reactions(message: Message, to_id: str, reactions: Iterable[str]):
        """
        Add reactions to a Message object.
        """
        reactions_stanza = stanza.Reactions()
        reactions_stanza['to'] = to_id
        for reaction in reactions:
            reaction_stanza = stanza.Reaction()
            reaction_stanza['value'] = reaction
            reactions_stanza.append(reaction_stanza)
        message.append(reactions_stanza)
