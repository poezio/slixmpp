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
        
    def example_tag_get_iq(self, iq): # Iq stanza always should have a respond. If user is offline, it call an error.
        logging.info(iq)
        if iq["example_tag"].get_some_string() == None:
            reply = iq.reply(clear=False)
            reply["type"] = "error"
            reply["error"]["condition"] = "feature-not-implemented"
            reply["error"]["text"] = "Without some_string value returns error."
        else:
            reply = iq.reply()
            reply["example_tag"].fill_interfaces(True, "Reply_string")
        reply.send()

    def example_tag_message(self, msg):
        logging.info(msg) # Message is standalone object, it can be replied, but no error arrives if not.


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
