import unittest
from slixmpp import Message
from slixmpp.test import SlixTest
from slixmpp.plugins.xep_0444 import XEP_0444
import slixmpp.plugins.xep_0444.stanza as stanza
from slixmpp.xmlstream import register_stanza_plugin


class TestReactions(SlixTest):

    def setUp(self):
        register_stanza_plugin(Message, stanza.Reactions)
        register_stanza_plugin(stanza.Reactions, stanza.Reaction)

    def testCreateReactions(self):
        """Testing creating Reactions."""

        xmlstring = """
          <message>
            <reactions xmlns="urn:xmpp:reactions:0" id="abcd">
                <reaction>😃</reaction>
                <reaction>🤗</reaction>
            </reactions>
          </message>
        """

        msg = self.Message()
        msg['reactions']['id'] = 'abcd'
        msg['reactions'].set_values(['😃', '🤗'])

        self.check(msg, xmlstring, use_values=False)

        self.assertEqual({'😃', '🤗'}, msg['reactions'].get_values())


suite = unittest.TestLoader().loadTestsFromTestCase(TestReactions)
