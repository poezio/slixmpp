import logging
import unittest
from slixmpp.test import SlixTest


class TestReply(SlixTest):
    def setUp(self):
        self.stream_start(plugins=["xep_0461"])

    def tearDown(self):
        self.stream_close()

    def testFallBackBody(self):
        async def on_reply(msg):
            start = msg["feature_fallback"]["fallback_body"]["start"]
            end = msg["feature_fallback"]["fallback_body"]["end"]
            self.xmpp["xep_0461"].send_reply(
                reply_to=msg.get_from(),
                reply_id=msg.get_id(),
                mto="test@test.com",
                mbody=f"{start} to {end}",
            )

        self.xmpp.add_event_handler("message_reply", on_reply)

        self.recv(
            """
            <message id="other-id" from="from@from.com/res">
              <reply xmlns="urn:xmpp:reply:0" id="some-id" />
              <body>&gt; quoted\nsome-body</body>
                <fallback xmlns='urn:xmpp:feature-fallback:0' for='urn:xmpp:reply:0'>
                   <body start="0" end="8" />
                </fallback>
            </message>
            """
        )
        self.send(
            """
            <message xmlns="jabber:client" to="test@test.com" type="normal">
              <reply xmlns="urn:xmpp:reply:0" id="other-id" to="from@from.com/res" />
              <body>0 to 8</body>
            </message>
            """
        )


logging.basicConfig(level=logging.DEBUG)
suite = unittest.TestLoader().loadTestsFromTestCase(TestReply)
