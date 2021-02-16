import unittest

from slixmpp import ComponentXMPP, Iq
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.test import SlixTest
from slixmpp.plugins.xep_0077 import Register


class TestRegistration(SlixTest):
    def setUp(self):
        self.stream_start(
            mode="component", plugins=["xep_0077"], jid="shakespeare.lit", server="lit"
        )

    # This one fails inconsistently, maybe because of default values?
    # def testRegistrationForm(self):
    #     self.stream_start(
    #         mode="component", plugins=["xep_0077"], jid="shakespeare.lit", server="lit"
    #     )
    #     self.recv(
    #         """
    #         <iq type='get' id='reg1' to='shakespeare.lit'>
    #             <query xmlns='jabber:iq:register'/>
    #         </iq>
    #         """,
    #     )
    #     self.send(
    #         f"""
    #         <iq type='result' id='reg1' from='shakespeare.lit'>
    #             <query xmlns='jabber:iq:register'>
    #                 <instructions>{self.xmpp["xep_0077"].form_instructions}</instructions>
    #                 <username/>
    #                 <password/>
    #             </query>
    #         </iq>
    #         """,
    #         defaults=['register']
    #     )

    def testRegistrationSuccess(self):
        self.recv(
            """
            <iq type='set' id='reg2' to='shakespeare.lit' from="bill@server/resource">
                <query xmlns='jabber:iq:register'>
                    <username>bill</username>
                    <password>Calliope</password>
                </query>
            </iq>
            """
        )
        self.send("<iq type='result' id='reg2' from='shakespeare.lit' to='bill@server/resource'/>")
        user_store = self.xmpp["xep_0077"]._user_store
        self.assertEqual(user_store["bill@server"]["username"], "bill")
        self.assertEqual(user_store["bill@server"]["password"], "Calliope")


suite = unittest.TestLoader().loadTestsFromTestCase(TestRegistration)
