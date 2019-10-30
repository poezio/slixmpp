import logging
from argparse import ArgumentParser
from getpass import getpass

import slixmpp
import example_plugin

class Responder(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("example_tag_get_iq", self.example_tag_get_iq)
        self.add_event_handler("example_tag_message", self.example_tag_message)

    def start(self, event):
        # Two, not required methods, but allows another users to see us available, and receive that information.
        self.send_presence()
        self.get_roster()
        
        #~ self.send_example_iq()

    def example_tag_get_iq(self, iq):
        print(iq)
        if not bool(iq['example_tag'].get_boolean()):
            iq.reply(clear=False)
            iq["type"] = "error"
        else:
            reply = iq.reply()
            print(iq, reply)
        iq.send()
            
            
        
    def example_tag_message(self, msg):
        print(msg) # Message is standalone object, it can be replied, but 
            #~ print(stanza)
        
    #~ def send_example_iq(self):
        #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
        #~ iq = self.make_iq(ito="test-slixmpp-bot@xmpp.jp/1762397490042511769727982537",
                          #~ itype="get")
        #~ iq['example_tag'].set_boolean(True)
        #~ iq['example_tag'].set_some_string("Another_string")
        #~ iq['example_tag'].set_text("Info_inside_tag")
        #~ iq.send()


if __name__ == '__main__':
    parser = ArgumentParser(description=Responder.__doc__)

    parser.add_argument("-q", "--quiet", help="set logging to ERROR",
                        action="store_const", dest="loglevel",
                        const=logging.ERROR, default=logging.INFO)
    parser.add_argument("-d", "--debug", help="set logging to DEBUG",
                        action="store_const", dest="loglevel",
                        const=logging.DEBUG, default=logging.INFO)

    parser.add_argument("-j", "--jid", dest="jid",
                        help="JID to use")
    parser.add_argument("-p", "--password", dest="password",
                        help="password to use")
    parser.add_argument("-t", "--to", dest="to",
                        help="JID to send the message to")

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel,
                        format=' %(name)s - %(levelname)-8s %(message)s')

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")

    xmpp = Responder(args.jid, args.password)
    xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin is a class name from example_plugin

    xmpp.connect()
    try:
        xmpp.process()
    except KeyboardInterrupt:
        try:
            xmpp.disconnect()
        except:
            pass
