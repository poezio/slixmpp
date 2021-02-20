import asyncio
import logging
from functools import partial

from slixmpp import Message, Iq, Presence, JID
from slixmpp.plugins import BasePlugin


class XEP_0100(BasePlugin):

    """
    XEP-0100: Gateway interaction (actually a little more than this XEP)
    """

    name = "xep_0100"
    description = "XEP-0100: Gateway interaction"
    dependencies = {
        "xep_0030",  # Service discovery
        "xep_0077",  # In band registration
    }

    default_config = {
        "component_name": "SliXMPP gateway",
        "name": "SliXMPP gateway",
        "type": "xmpp",
    }

    def plugin_init(self):
        if not self.xmpp.is_component:
            raise TypeError("Only components can be gateways")

        self.prompt_futures = dict()

        self.xmpp["xep_0030"].add_identity(
            name=self.component_name, category="gateway", itype=self.type
        )

        self.xmpp.client_roster.auto_authorize = True
        self.xmpp.client_roster.auto_subscribe = True

        self.xmpp.add_event_handler("user_register", self.on_user_register)
        self.xmpp.add_event_handler("user_unregister", self.on_user_unregister)

    def get_user(self, stanza):
        return self.xmpp["xep_0077"].api["user_get"](None, None, None, stanza)

    def on_user_register(self, iq: Iq):
        user_jid = iq["from"]
        user = self.get_user(iq)
        if user is None:  # This should not happen
            log.warning(
                f"{user_jid} has registered but cannot find him/her in user store"
            )
        else:
            log.debug(f"Send subscription request to {user}")
            self.xmpp.client_roster.subscribe(user_jid)

    def on_user_unregister(self, iq: Iq):
        user_jid = iq["from"]
        try:
            self.user_store.remove(user_jid)
        except KeyError:
            log.warning(
                f"{user_jid} has unregistered but cannot find him/her in user store"
            )
            return

        for ptype in "unsubscribe", "unsubscribed":
            self.send_presence(pto=user_jid.bare, ptype=ptype)


log = logging.getLogger(__name__)
