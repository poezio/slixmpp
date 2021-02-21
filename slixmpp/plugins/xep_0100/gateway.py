import asyncio
import logging
from functools import partial
import typing

from slixmpp import Message, Iq, Presence, JID
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.plugins import BasePlugin


class XEP_0100(BasePlugin):

    """
    XEP-0100: Gateway interaction

    Does not cover the deprecated Agent Information and 'jabber:iq:gateway' protocols

    Events:

    ::

        legacy_login                -- Jabber user got online or just registered
        legacy_logout               -- Jabber user got offline or just unregistered
        legacy_presence_unavailable -- Jabber user sent an unavailable presence to a legacy contact
        gateway_message             -- Jabber user sent a direct message to the gateway component
        legacy_message              -- Jabber user sent a message to the legacy network


    Config:

    ::

        component_name -- Name of the entity
        type           -- Type of the gateway identity. Should be the name of the legacy service


    API:

    ::

        async legacy_contact_add(jid, node, ifrom, presence: Presence)
            Add contact on the legacy service. Should raise LegacyError if anything goes wrong in
            the process.
        legacy_contact_remove(jid, node, ifrom, iq: Iq)
            Remove a contact.

    """

    name = "xep_0100"
    description = "XEP-0100: Gateway interaction"
    dependencies = {
        "xep_0030",  # Service discovery
        "xep_0077",  # In band registration
    }

    default_config = {
        "component_name": "SliXMPP gateway",
        "type": "xmpp",
    }

    def plugin_init(self):
        if not self.xmpp.is_component:
            raise TypeError("Only components can be gateways")

        self.prompt_futures = dict()

        self.xmpp["xep_0030"].add_identity(
            name=self.component_name, category="gateway", itype=self.type
        )

        self.api.register(self._legacy_contact_remove, "legacy_contact_remove")
        self.api.register(self._legacy_contact_add, "legacy_contact_add")

        # Without that BaseXMPP sends unsub/unavailable on sub requests and we don't want that
        self.xmpp.client_roster.auto_authorize = True
        self.xmpp.client_roster.auto_subscribe = False

        self.xmpp.add_event_handler("user_register", self.on_user_register)
        self.xmpp.add_event_handler("user_unregister", self.on_user_unregister)

        self.xmpp.add_event_handler("got_online", self.on_got_online)

        self.xmpp.add_event_handler(
            "presence_unavailable", self.on_presence_unavailable
        )

        self.xmpp.add_event_handler("presence_subscribe", self.on_presence_subscribe)

        self.xmpp.register_handler(
            Callback(
                "roster_remove",
                StanzaPath("/iq@type=set/roster/item@subscription=remove"),
                self._handle_roster_remove,
            )
        )

        self.xmpp.add_event_handler("message", self.on_message)

    def get_user(self, stanza):
        return self.xmpp["xep_0077"].api["user_get"](None, None, None, stanza)

    def send_presence(self, pto, ptype=None, pstatus=None, pfrom=None):
        self.xmpp.send_presence(
            pfrom=self.xmpp.boundjid.bare,
            ptype=ptype,
            pto=pto,
            pstatus=pstatus,
        )

    def on_user_register(self, iq: Iq):
        user_jid = iq["from"]
        user = self.get_user(iq)
        if user is None:  # This should not happen
            log.warning(
                f"{user_jid} has registered but cannot find him/her in user store"
            )
        else:
            log.debug(f"Sending subscription request to {user_jid}")
            self.xmpp.event("legacy_login", iq)
            self.xmpp.client_roster.subscribe(user_jid)

    def on_user_unregister(self, iq: Iq):
        user_jid = iq["from"]
        log.debug(f"Sending subscription request to {user_jid}")
        self.xmpp.event("legacy_logout", iq)
        self.xmpp.client_roster.unsubscribe(iq["from"])

    def on_got_online(self, presence: Presence):
        user_jid = presence["from"]
        user = self.get_user(presence)
        if user is None:  # This should not happen
            log.warning(f"{user_jid} has gotten online but (s)he is not in user store")
        else:
            self.xmpp.event("legacy_login", presence)
            self.send_presence(pto=user_jid.bare)

    def on_presence_unavailable(self, presence: Presence):
        user_jid = presence["from"]
        user = self.get_user(presence)
        if user is None:  # This should not happen
            log.warning(f"{user_jid} has gotten offline but (s)he is not in user store")
            return

        if presence["to"] == self.xmpp.boundjid.bare:
            self.xmpp.event("legacy_logout", presence)
            self.send_presence(pto=user_jid.bare)
        else:
            self.xmpp.event("legacy_presence_unavailable", presence)

    async def _legacy_contact_add(self, jid, node, ifrom, presence: Presence):
        pass

    async def on_presence_subscribe(self, presence: Presence):
        user_jid = presence["from"]
        user = self.get_user(presence)
        if user is None:
            return

        if presence["to"] == self.xmpp.boundjid.bare:
            return

        try:
            await self.api["legacy_contact_add"](None, None, None, presence)
        except LegacyError:
            self.xmpp.send_presence(
                pfrom=presence["to"],
                ptype="unsubscribed",
                pto=user_jid,
            )
            return
        self.xmpp.send_presence(
            pfrom=presence["to"],
            ptype="subscribed",
            pto=user_jid,
        )
        self.xmpp.send_presence(
            pfrom=presence["to"],
            pto=user_jid,
        )
        self.xmpp.send_presence(
            pfrom=presence["to"],
            ptype="subscribe",
            pto=user_jid,
        )  # TODO: handle resulting subscribed presences

    def _legacy_contact_remove(self, jid, node, ifrom, iq: Iq):
        pass

    def _handle_roster_remove(self, iq: Iq):
        log.debug("Received remove subscription")
        self.api["legacy_contact_remove"](None, None, None, iq)

    def on_message(self, msg: Message):
        if msg["type"] == "groupchat":
            return  # groupchat messages are out of scope of XEP-0100

        if msg["to"] == self.xmpp.boundjid.bare:
            # It may be useful to exchange direct messages with the component
            self.xmpp.event("gateway_message", msg)
            return

        user = self.get_user(msg)
        if user is None:
            return

        self.xmpp.event("legacy_message", msg)

    def transform_legacy_message(
        self,
        jabber_user_jid: typing.Union[JID, str],
        legacy_contact_id: str,
        body: str,
        mtype: typing.Optional[str] = None,
    ):
        """
        Transform a legacy message to an XMPP message
        """
        # Should escaping legacy IDs to valid JID local parts be handled here?
        # Maybe by internal API stuff?
        self.xmpp.send_message(
            mfrom=f"{legacy_contact_id}@{self.xmpp.boundjid.bare}",
            mto=JID(jabber_user_jid).bare,
            mbody=body,
            mtype=mtype,
        )


class LegacyError(Exception):
    pass


log = logging.getLogger(__name__)
