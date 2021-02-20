import unittest
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


suite = unittest.TestLoader().loadTestsFromTestCase(TestStreamGateway)
