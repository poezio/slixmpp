import unittest
from slixmpp import Message
from slixmpp.test import SlixTest
from slixmpp.xmlstream import register_stanza_plugin

from slixmpp.plugins.xep_0356 import stanza


class TestPermissions(SlixTest):
    def setUp(self):
        stanza.register()

    def testAdvertisePermission(self):
        xmlstring = """
            <message from='capulet.net' to='pubub.capulet.lit'>
                <privilege xmlns='urn:xmpp:privilege:1'>
                    <perm access='roster' type='both'/>
                    <perm access='message' type='outgoing'/>
                    <perm access='presence' type='managed_entity'/>
                </privilege>
            </message>
        """
        msg = self.Message()
        msg["from"] = "capulet.net"
        msg["to"] = "pubub.capulet.lit"
        # This raises AttributeError: 'NoneType' object has no attribute 'use_origin_id'
        # msg["id"] = "id"

        for access, type_ in [
            ("roster", "both"),
            ("message", "outgoing"),
            ("presence", "managed_entity"),
        ]:
            msg["privilege"].add_perm(access, type_)

        self.check(msg, xmlstring)
        # Should this one work? →        # AttributeError: 'Message' object has no attribute 'permission'
        # self.assertEqual(msg.permission["roster"], "both")

    def testRosterQuery(self):
        # This doesn't use anything from plugins.xep_0356
        # https://xmpp.org/extensions/xep-0356.html#priv_manage_roster
        iq = self.Iq()
        iq.set_query("jabber:iq:roster")
        iq["id"] = "roster1"
        iq["from"] = "pubsub.capulet.lit"
        iq["to"] = "juliet@example.com"
        iq["type"] = "get"

        xmlstring = """
        <iq id='roster1' from='pubsub.capulet.lit' to='juliet@example.com' type='get'>
            <query xmlns='jabber:iq:roster'/>
        </iq>
        """
        self.check(iq, xmlstring)


suite = unittest.TestLoader().loadTestsFromTestCase(TestPermissions)
