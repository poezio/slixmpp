"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2020 Mathieu Pasquet <mathieui@mathieui.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""
from typing import Optional

from slixmpp import JID, Message
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.plugins import BasePlugin
from slixmpp.plugins.xep_0425 import stanza


class XEP_0425(BasePlugin):
    '''XEP-0425: Message Moderation'''

    name = 'xep_0425'
    description = 'Message Moderation'
    dependencies = {'xep_0424', 'xep_0421'}
    stanza = stanza
    namespace = stanza.NS

    def plugin_init(self) -> None:
        stanza.register_plugins()

    def session_bind(self, jid):
        self.xmpp.plugin['xep_0030'].add_feature(feature=stanza.NS)

    def plugin_end(self):
        self.xmpp.plugin['xep_0030'].remove_feature(feature=stanza.NS)

    async def moderate(self, room: JID, id: str, reason: str = '', *,
                       ifrom: Optional[JID] = None, **iqkwargs):
        iq = self.xmpp.make_iq_set(ito=room.bare, ifrom=ifrom)
        iq['apply_to']['id'] = id
        iq['apply_to']['moderate']['reason'] = reason
        await iq.send(**iqkwargs)
