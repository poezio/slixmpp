import unittest
from slixmpp import Message
from slixmpp.test import SlixTest
from slixmpp.plugins.xep_0461 import stanza


class TestReply(SlixTest):
    def setUp(self):
        stanza.register_plugins()

    def testReply(self):
        message = Message()
        message["reply"]["id"] = "some-id"
        message["body"] = "some-body"

        self.check(
            message,
            """
            <message>
              <reply xmlns="urn:xmpp:reply:0" id="some-id" />
              <body>some-body</body>
            </message>
            """,
        )

    def testFallback(self):
        message = Message()
        message["body"] = "12345\nrealbody"
        message["feature_fallback"]["for"] = "NS"
        message["feature_fallback"]["fallback_body"]["start"] = "0"
        message["feature_fallback"]["fallback_body"]["end"] = "6"

        self.check(
            message,
            """
            <message xmlns="jabber:client">
              <body>12345\nrealbody</body>
              <fallback xmlns='urn:xmpp:feature-fallback:0' for='NS'>
                <body start="0" end="6" />
              </fallback>
            </message>
            """,
        )

        assert message["feature_fallback"].get_stripped_body() == "realbody"


suite = unittest.TestLoader().loadTestsFromTestCase(TestReply)
