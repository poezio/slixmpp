import unittest
from slixmpp import JID, Presence, Message
from slixmpp.test import SlixTest
import slixmpp.plugins.xep_0045 as xep_0045
from slixmpp.xmlstream import register_stanza_plugin


class TestMUC(SlixTest):

    def setUp(self):
        register_stanza_plugin(Presence, xep_0045.stanza.MUCPresence)
        register_stanza_plugin(Message, xep_0045.stanza.MUCMessage)

    def testPresence(self):
        result = '''
            <presence from='foo@muc/user1' type='unavailable'>
                <x xmlns='http://jabber.org/protocol/muc#user'>
                    <item affiliation='none'
                          role='none'
                          jid='some@jid'/>
                </x>
            </presence>
        '''

        presence = self.Presence()
        presence['type'] = 'unavailable'
        presence['from'] = JID('foo@muc/user1')
        presence['muc']['affiliation'] = 'none'
        presence['muc']['role'] = 'none'
        # presence['muc']['nick'] = 'newnick2'
        presence['muc']['jid'] = JID('some@jid')

        self.check(presence, result)

    def testMessage(self):
        result = '''
            <message from='foo@muc/user1' type='chat'>
                <body>Correct!</body>
                <replace xmlns='urn:xmpp:message-correct:0' id='someid1'/>
                <x xmlns='http://jabber.org/protocol/muc#user'>
                    <item affiliation='none'
                          role='none'
                          jid='some@jid'/>
                </x>
            </message>
        '''

        msg = self.Message()
        msg['id'] = 'someid2'
        msg['type'] = 'chat'
        msg['from'] = JID('foo@muc/nick1')
        msg['body'] = 'Correct!'
        msg['muc']['affiliation'] = 'none'
        msg['muc']['role'] = 'none'
        # msg['muc']['nick'] = 'newnick2'
        msg['muc']['jid'] = JID('some@jid')

        self.check(msg, result)

suite = unittest.TestLoader().loadTestsFromTestCase(TestMUC)
