import threading

import unittest
from slixmpp.test import SlixTest


class TestOOB(SlixTest):

    def tearDown(self):
        self.stream_close()

    def testSendOOB(self):
        """Test sending an OOB transfer request."""
        self.stream_start(plugins=['xep_0066', 'xep_0030'])

        url = 'http://github.com/fritzy/Slixmpp/blob/master/README'

        t = threading.Thread(
                name='send_oob',
                target=self.xmpp['xep_0066'].send_oob,
                args=('user@example.com', url),
                kwargs={'desc': 'Slixmpp README'})

        t.start()

        self.send("""
          <iq to="user@example.com" type="set" id="1">
            <query xmlns="jabber:iq:oob">
              <url>http://github.com/fritzy/Slixmpp/blob/master/README</url>
              <desc>Slixmpp README</desc>
            </query>
          </iq>
        """)

        self.recv("""
          <iq id="1" type="result"
              to="tester@localhost"
              from="user@example.com" />
        """)

        t.join()


suite = unittest.TestLoader().loadTestsFromTestCase(TestOOB)
