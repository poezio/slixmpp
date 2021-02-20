import unittest
from slixmpp import Message
from slixmpp.test import SlixTest
from slixmpp.plugins.xep_0424 import stanza
from slixmpp.plugins.xep_0422 import stanza as astanza


class TestRetraction(SlixTest):

    def setUp(self):
        astanza.register_plugins()
        stanza.register_plugins()

    def testRetract(self):
        message = Message()
        message['apply_to']['id'] = 'some-id'
        message['apply_to']['retract']

        self.check(message, """
<message>
  <apply-to xmlns="urn:xmpp:fasten:0" id="some-id">
      <retract xmlns="urn:xmpp:message-retract:0"/>
  </apply-to>
</message>
        """, use_values=False)

    def testRetracted(self):
        message = Message()
        message['retracted']['stamp'] = '2019-09-20T23:09:32Z'
        message['retracted']['origin_id']['id'] = 'originid'

        self.check(message, """
<message>
  <retracted stamp="2019-09-20T23:09:32Z" xmlns="urn:xmpp:message-retract:0">
    <origin-id xmlns="urn:xmpp:sid:0" id="originid"/>
  </retracted>
</message>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestRetraction)
