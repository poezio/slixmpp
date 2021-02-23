import unittest

from slixmpp.roster import RosterItem
from slixmpp import JID
from slixmpp.test import SlixTest


class TestStreamGateway(SlixTest):
    def setUp(self):
        self.stream_start(
            mode="component",
            plugins=["xep_0077", "xep_0100"],
            jid="aim.shakespeare.lit",
            server="shakespeare.lit",
            plugin_config={
                "xep_0100": {"component_name": "AIM Gateway", "type": "aim"}
            },
        )

    def next_sent(self):
        self.wait_for_send_queue()
        sent = self.xmpp.socket.next_sent(timeout=0.5)
        if sent is None:
            return None
        xml = self.parse_xml(sent)
        self.fix_namespaces(xml, "jabber:component:accept")
        sent = self.xmpp._build_stanza(xml, "jabber:component:accept")
        return sent

    def testDisco(self):
        # https://xmpp.org/extensions/xep-0100.html#example-3
        self.recv(
            """
            <iq type='get'
                from='romeo@montague.lit/orchard'
                to='aim.shakespeare.lit'
                id='disco1'>
            <query xmlns='http://jabber.org/protocol/disco#info'/>
            </iq>
            """
        )
        self.send(
            """
            <iq type="result"
                from="aim.shakespeare.lit"
                to="romeo@montague.lit/orchard"
                id="disco1">
            <query xmlns="http://jabber.org/protocol/disco#info">
                <identity category="gateway" type="aim" name="AIM Gateway" />
                <feature var="jabber:iq:register" />
                <feature var="jabber:x:data" />
                <feature var="jabber:iq:oob" />
                <feature var="jabber:x:oob" />
            </query>
            </iq>
            """
        )

    def testRegister(self):
        event_result = {}

        def legacy_login(iq):
            event_result["user"] = iq["from"]

        self.xmpp.add_event_handler("legacy_login", legacy_login)

        # Jabber User sends IQ-set qualified by the 'jabber:iq:register' namespace to Gateway,
        # containing information required to register.
        # https://xmpp.org/extensions/xep-0100.html#example-7
        self.recv(
            """
            <iq type='set'
                from='romeo@montague.lit/orchard'
                to='aim.shakespeare.lit'
                id='reg2'>
            <query xmlns='jabber:iq:register'>
                <username>RomeoMyRomeo</username>
                <password>ILoveJuliet</password>
            </query>
            </iq>
            """
        )
        # Gateway verifies that registration information provided by Jabber User is valid
        # (using whatever means appropriate for the Legacy Service) and informs Jabber User of success [A1].
        # https://xmpp.org/extensions/xep-0100.html#example-8
        self.send(
            """
            <iq type='result'
                from='aim.shakespeare.lit'
                to='romeo@montague.lit/orchard'
                id='reg2'/>
            """
        )
        # Gateway sends subscription request to Jabber User (i.e., by sending a presence stanza
        # of type "subscribe" to Jabber User's bare JID).
        # https://xmpp.org/extensions/xep-0100.html#example-11
        sent = self.next_sent()
        self.check(
            sent, "/presence@type=subscribe@from=aim.shakespeare.lit", "stanzapath"
        )
        self.assertTrue(
            sent["to"] == "romeo@montague.lit"
        )  # cannot use stanzapath because of @
        # Jabber User's client SHOULD approve the subscription request (i.e., by sending a presence stanza
        # of type "subscribed" to Gateway).
        self.recv(
            """
            <presence type='subscribed'
                      from='romeo@montague.lit'
                      to='aim.shakespeare.lit'/>
            """
        )
        # Jabber User sends subscription request to Gateway (i.e., by sending a presence stanza
        # of type "subscribe" to Gateway).
        self.recv(
            """
            <presence type='subscribe'
                      from='romeo@montague.lit'
                      to='aim.shakespeare.lit'/>
            """
        )
        # Gateway sends approves subscription request (i.e., by sending a presence stanza of type
        # "subscribed" to Jabber User's bare JID).
        sent = self.next_sent()
        self.check(
            sent, "/presence@type=subscribed@from=aim.shakespeare.lit", "stanzapath"
        )
        self.assertTrue(
            sent["to"] == "romeo@montague.lit"
        )  # cannot use stanzapath because of @
        self.assertTrue(
            self.xmpp.client_roster["romeo@montague.lit"]["subscription"] == "both"
        )
        self.assertTrue(event_result["user"] == "romeo@montague.lit/orchard")

    def testBadCredentials(self):
        def raise_v(*a, **kwa):
            raise ValueError("Not good")

        self.xmpp["xep_0077"].api.register(raise_v, "user_validate")
        self.recv(
            """
            <iq type='set'
                from='romeo@montague.lit/orchard'
                to='aim.shakespeare.lit'
                id='reg2'>
            <query xmlns='jabber:iq:register'>
                <username>RomeoMyRomeo</username>
                <password>ILoveJuliet</password>
            </query>
            </iq>
            """
        )
        # xmlns="jabber:client" in error substanza, bug in XEP-0077 plugin or OK?
        self.send(
            """
            <iq type='error'
                from='aim.shakespeare.lit'
                to='romeo@montague.lit/orchard'
                id='reg2'>
            <query xmlns='jabber:iq:register'>
                <username>RomeoMyRomeo</username>
                <password>ILoveJuliet</password>
            </query>
            <error code='406' type='modify' xmlns="jabber:client">
                <not-acceptable
                    xmlns='urn:ietf:params:xml:ns:xmpp-stanzas'/>
                <text xmlns="urn:ietf:params:xml:ns:xmpp-stanzas">Not good</text>
            </error>
            </iq>
            """,
            use_values=False,
        )

    def testLogin(self):
        event_result = {}

        def legacy_login(presence):
            event_result["user"] = presence["from"]

        self.xmpp.add_event_handler("legacy_login", legacy_login)

        self.xmpp["xep_0077"].api["user_validate"](
            None,
            None,
            JID("romeo@montague.lit"),
            {"username": "RomeoMyRomeo", "password": "ILoveJuliet"},
        )

        # Jabber User sends available presence broadcast to Server or sends
        # directed presence to Gateway or a Legacy User.
        # https://xmpp.org/extensions/xep-0100.html#example-26
        self.recv(
            """
            <presence from='romeo@montague.lit/orchard'
                    to='juliet@aim.shakespeare.lit'/>
            <presence from='romeo@montague.lit/orchard'
                    to='aim.shakespeare.lit'/>
            """
        )
        # Gateway sends presence stanza to Jabber User expressing availability.
        # https://xmpp.org/extensions/xep-0100.html#example-27
        self.send(
            """
            <presence from='aim.shakespeare.lit'
                      to='romeo@montague.lit'>
            <priority>0</priority>
            </presence>
            """
        )
        self.assertTrue(event_result["user"] == "romeo@montague.lit/orchard")

    def testLogout(self):
        self.add_user()
        event_result = {}

        def legacy_logout(presence):
            event_result["user"] = presence["from"]

        self.xmpp.add_event_handler("legacy_logout", legacy_logout)
        # Jabber User sends available presence broadcast to Server or sends
        # directed presence to Gateway or a Legacy User.
        # https://xmpp.org/extensions/xep-0100.html#example-26
        self.recv(
            """
            <presence type='unavailable'
                    from='romeo@montague.lit/orchard'
                    to='aim.shakespeare.lit'/>
            """
        )
        # Gateway sends presence stanza to Jabber User expressing availability.
        # https://xmpp.org/extensions/xep-0100.html#example-27
        self.send(
            """
            <presence from='aim.shakespeare.lit'
                      to='romeo@montague.lit'>
            <priority>0</priority>
            </presence>
            """
        )
        self.assertTrue(event_result["user"] == "romeo@montague.lit/orchard")

    def testAddContact(self):
        self.add_user()
        # Had to lowercase capuletnurse everywhere
        # Jabber User sends presence stanza of type "subscribe" to Legacy User.
        self.recv(
            """
            <presence type='subscribe'
                      from='romeo@montague.lit'
                      to='capuletnurse@aim.shakespeare.lit'/>
            """
        )
        # If Legacy User approves subscription request, Gateway sends presence stanza of
        # type "subscribed" to Jabber User on behalf of Legacy User. [A1]
        self.send(
            """
            <presence type='subscribed'
                      from='capuletnurse@aim.shakespeare.lit'
                      to='romeo@montague.lit'/>
            """
        )
        # Had to remove the resource here
        self.send(
            """
            <presence from='capuletnurse@aim.shakespeare.lit'
                      to='romeo@montague.lit'/>
            """
        )
        self.send(
            """
            <presence type='subscribe'
                      from='capuletnurse@aim.shakespeare.lit'
                      to='romeo@montague.lit'/>
            """
        )
        self.recv(
            """
            <presence type='subscribed'
                      from='romeo@montague.lit'
                      to='capuletnurse@aim.shakespeare.lit'/>
            """
        )

    def testRemoveContact(self):
        self.add_user()
        result = {}
        # Jabber User sends IQ-set qualified by the 'jabber:iq:roster' namespace, containing subscription
        # attribute with value of "remove".
        def legacy_contacts_remove(jid, node, ifrom, roster_items):
            result.update(**locals())

        self.xmpp["xep_0100"].api.register(
            legacy_contacts_remove, "legacy_contacts_remove"
        )

        # Jabber User sends IQ-set qualified by the 'jabber:iq:roster' namespace, containing subscription
        # attribute with value of "remove".
        self.recv(
            """
            <iq type='set'
                from='romeo@montague.lit/orchard'
                id='remove1'>
            <query xmlns='jabber:iq:roster'>
                <item jid='CapuletNurse@aim.shakespeare.lit'
                      subscription='remove'/>
            </query>
            </iq>
            """
        )
        # Server sends normal "roster push" to Jabber User (see RFC 6121) and sends presence stanzas of type
        # "unsubscribe", "unsubscribed", and "unavailable" to Legacy User.
        # → nothing to do here then?

        self.assertTrue(
            JID("CapuletNurse@aim.shakespeare.lit")
            in result["roster_items"]
        )

    def testSendMessage(self):
        self.xmpp["xep_0100"].transform_legacy_message(
            jabber_user_jid="romeo@montague.lit",
            legacy_contact_id="juliet",
            body="Art thou not Romeo, and a Montague?",
        )
        self.send(
            """
            <message from='juliet@aim.shakespeare.lit'
                     to='romeo@montague.lit'>
            <body>Art thou not Romeo, and a Montague?</body>
            </message>
            """
        )

    def testLegacyMessage(self):
        self.add_user()
        result = {}

        def legacy_message(msg):
            result["msg"] = msg

        self.xmpp.add_event_handler("legacy_message", legacy_message)
        self.recv(
            """
            <message to='juliet@aim.shakespeare.lit'
                     from='romeo@montague.lit'>
            <body>Something shakespearian</body>
            </message>
            """
        )
        self.wait_for_send_queue()
        self.assertTrue(result["msg"]["from"] == "romeo@montague.lit")
        self.assertTrue(result["msg"]["to"] == "juliet@aim.shakespeare.lit")

    def testPluginEnd(self):
        exc = False
        try:
            self.xmpp.plugin.disable("xep_0100")
        except Exception:
            exc = True
        self.assertFalse(exc)

    def add_user(self):
        self.xmpp["xep_0077"].api["user_validate"](
            None,
            None,
            JID("romeo@montague.lit"),
            {"username": "RomeoMyRomeo", "password": "ILoveJuliet"},
        )
        self.xmpp.client_roster._jids["romeo@montague.lit"] = RosterItem(
            self.xmpp,
            "romeo@montague.lit",
            self.xmpp.boundjid.bare,
            state={
                "name": "",
                "groups": [],
                "from": True,
                "to": True,
                "pending_in": False,
                "pending_out": False,
                "whitelisted": False,
                "subscription": "both",
            },
        )

    # TODO: edit reg
    # TODO: unregister
    # TODO: login fails


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamGateway)
