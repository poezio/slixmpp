import unittest
from slixmpp import Iq
from slixmpp.test import SlixTest
import slixmpp.plugins.xep_0191 as xep_0191
import slixmpp.plugins.xep_0377 as xep_0377
from slixmpp.xmlstream import register_stanza_plugin


class TestSpamReporting(SlixTest):

    def setUp(self):
        register_stanza_plugin(Iq, xep_0191.Block)
        register_stanza_plugin(
                xep_0191.Block,
                xep_0377.Report,
        )
        register_stanza_plugin(
            xep_0377.Report,
            xep_0377.Text,
        )

    def testCreateReport(self):
        report = """
          <iq type="set">
            <block xmlns="urn:xmpp:blocking">
                <report xmlns="urn:xmpp:reporting:0">
                    <spam/>
                </report>
            </block>
          </iq>
        """

        iq = self.Iq()
        iq['type'] = 'set'
        iq['block']['report']['spam'] = True

        self.check(iq, report)

    def testEnforceOnlyOneSubElement(self):
        report = """
          <iq type="set">
            <block xmlns="urn:xmpp:blocking">
                <report xmlns="urn:xmpp:reporting:0">
                    <abuse/>
                </report>
            </block>
          </iq>
        """

        iq = self.Iq()
        iq['type'] = 'set'
        iq['block']['report']['spam'] = True
        iq['block']['report']['abuse'] = True
        self.check(iq, report)

suite = unittest.TestLoader().loadTestsFromTestCase(TestSpamReporting)
