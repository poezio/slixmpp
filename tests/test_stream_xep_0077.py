import unittest

from slixmpp import ComponentXMPP
from slixmpp.test import SlixTest


class TestRegistration(SlixTest):
    def setUp(self):
        pass

    def testRegistrationForm(self):
        self.stream_start(
            mode="component", plugins=["xep_0077"], jid="shakespeare.lit", server="lit"
        )
        self.recv(
            """
            <iq type='get' id='reg1' to='shakespeare.lit'>
                <query xmlns='jabber:iq:register'/>
            </iq>
            """
        )
        self.send(
            f"""
            <iq type='result' id='reg1' from='shakespeare.lit'>
                <query xmlns='jabber:iq:register'>
                    <instructions>{self.xmpp["xep_0077"].form_instructions}</instructions>
                    <username/>
                    <password/>
                </query>
            </iq>
            """,
        )


suite = unittest.TestLoader().loadTestsFromTestCase(TestRegistration)
