import unittest
from slixmpp import Message, Iq, JID
from slixmpp.test import SlixTest
from slixmpp.plugins.xep_0425 import stanza


class TestModeration(SlixTest):

    def setUp(self):
        stanza.register_plugins()

    def testModerate(self):
        iq = Iq()
        iq['type'] = 'set'
        iq['id'] = 'a'
        iq['apply_to']['id'] = 'some-id'
        iq['apply_to']['moderate'].enable('retract')
        iq['apply_to']['moderate']['reason'] = 'R'

        self.check(iq, """
<iq type='set' id='a'>
  <apply-to id="some-id" xmlns="urn:xmpp:fasten:0">
    <moderate xmlns='urn:xmpp:message-moderate:0'>
      <retract xmlns='urn:xmpp:message-retract:0'/>
      <reason>R</reason>
    </moderate>
  </apply-to>
</iq>
        """, use_values=False)

    def testModerated(self):
        message = Message()
        message['moderated']['by'] = JID('toto@titi')
        message['moderated']['retracted']['stamp'] = '2019-09-20T23:09:32Z'
        message['moderated']['reason'] = 'R'

        self.check(message, """
<message>
  <moderated xmlns="urn:xmpp:message-moderate:0" by="toto@titi">
    <retracted stamp="2019-09-20T23:09:32Z" xmlns="urn:xmpp:message-retract:0" />
    <reason>R</reason>
  </moderated>
</message>
        """)


suite = unittest.TestLoader().loadTestsFromTestCase(TestModeration)
