import unittest

from slixmpp import ComponentXMPP, Iq, Message
from slixmpp.roster import RosterItem
from slixmpp.test import SlixTest


class TestPermissions(SlixTest):
    def setUp(self):
        self.stream_start(
            mode="component",
            plugins=["xep_0356"],
            jid="pubsub.capulet.lit",
            server="capulet.net",
        )

    def testPluginEnd(self):
        exc = False
        try:
            self.xmpp.plugin.disable("xep_0356")
        except Exception as e:
            exc = True
        self.assertFalse(exc)

    def testGrantedPrivileges(self):
        # https://xmpp.org/extensions/xep-0356.html#example-4
        results = {"event": False}
        self.xmpp.add_event_handler(
            "privileges_advertised", lambda msg: results.__setitem__("event", True)
        )
        self.recv(
            """
            <message from='capulet.net' to='pubub.capulet.lit' id='54321'>
                <privilege xmlns='urn:xmpp:privilege:1'>
                    <perm access='roster' type='both'/>
                    <perm access='message' type='outgoing'/>
                </privilege>
            </message>
            """
        )
        self.assertEqual(self.xmpp["xep_0356"].granted_privileges["roster"], "both")
        self.assertEqual(
            self.xmpp["xep_0356"].granted_privileges["message"], "outgoing"
        )
        self.assertEqual(self.xmpp["xep_0356"].granted_privileges["presence"], "none")
        self.assertTrue(results["event"])

    def testGetRosterIq(self):
        iq = self.xmpp["xep_0356"]._make_get_roster("juliet@example.com")
        xmlstring = """
        <iq xmlns="jabber:component:accept"
            id='1'
            from='pubsub.capulet.lit'
            to='juliet@example.com'
            type='get'>
                <query xmlns='jabber:iq:roster'/>
        </iq>
        """
        self.check(iq, xmlstring, use_values=False)

    def testSetRosterIq(self):
        jid = "juliet@example.com"
        items = {
            "friend1@example.com": {
                "name": "Friend 1",
                "subscription": "both",
                "groups": ["group1", "group2"],
            },
            "friend2@example.com": {
                "name": "Friend 2",
                "subscription": "from",
                "groups": ["group3"],
            },
        }
        iq = self.xmpp["xep_0356"]._make_set_roster(jid, items)
        xmlstring = f"""
        <iq xmlns="jabber:component:accept"
            id='1'
            from='pubsub.capulet.lit'
            to='{jid}'
            type='set'>
                <query xmlns='jabber:iq:roster'>
                    <item name='Friend 1' jid='friend1@example.com' subscription='both'>
                        <group>group1</group>
                        <group>group2</group>
                    </item>
                    <item name='Friend 2' jid='friend2@example.com' subscription='from'>
                        <group>group3</group>
                    </item>
                </query>
        </iq>
        """
        self.check(iq, xmlstring, use_values=False)

    def testMakeOutgoingMessage(self):
        xmlstring = """
        <message xmlns="jabber:component:accept" from='pubsub.capulet.lit' to='capulet.net'>
            <privilege xmlns='urn:xmpp:privilege:1'>
                <forwarded xmlns='urn:xmpp:forward:0'>
                    <message from="juliet@capulet.lit" to="romeo@montague.lit" xmlns="jabber:client">
                        <body>I do not hate you</body>
                    </message>
                </forwarded>
            </privilege>
        </message>
        """
        msg = Message()
        msg["from"] = "juliet@capulet.lit"
        msg["to"] = "romeo@montague.lit"
        msg["body"] = "I do not hate you"
        
        priv_msg = self.xmpp["xep_0356"]._make_privileged_message(msg)
        self.check(priv_msg, xmlstring, use_values=False)


suite = unittest.TestLoader().loadTestsFromTestCase(TestPermissions)
