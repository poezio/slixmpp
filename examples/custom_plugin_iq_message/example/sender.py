import logging
from argparse import ArgumentParser
from getpass import getpass

import slixmpp
import example_plugin

class Sender(slixmpp.ClientXMPP):
    def __init__(self, args):
        slixmpp.ClientXMPP.__init__(self, args.jid, args.password)

        self.to = args.to
        self.path = args.path

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("example_tag_result_iq", self.example_tag_result_iq)
        self.add_event_handler("example_tag_error_iq", self.example_tag_result_iq)

    def start(self, event):
        # Two, not required methods, but allows another users to see us available, and receive that information.
        self.send_presence()
        self.get_roster()
        
        self.send_example_iq(self.to)
        # <iq to=RESPONDER/RESOURCE xml:lang="en" type="get" id="0" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string" boolean="True">Info_inside_tag</example_tag></iq>
        self.send_example_iq_with_inner_tag(self.to)
        # <iq from="SENDER/RESOURCE" to="RESPONDER/RESOURCE" id="2" xml:lang="en" type="get"><example_tag xmlns="https://example.net/our_extension" some_string="Another_string">Info_inside_tag<inside_tag first_field="1" secound_field="2" /></example_tag></iq>
        self.send_example_message(self.to)
        # <message to="RESPONDER" xml:lang="en" from="SENDER/RESOURCE"><example_tag xmlns="https://example.net/our_extension" boolean="True" some_string="Message string">Info_inside_tag_message</example_tag></message>
        self.send_example_iq_tag_from_file(self.path)


    def example_tag_result_iq(self, iq):
        pass

    def send_example_iq(self, to):
        #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
        iq = self.make_iq(ito=to,
                          itype="get")
        iq['example_tag'].set_boolean(True)
        iq['example_tag'].set_some_string("Another_string")
        iq['example_tag'].set_text("Info_inside_tag")
        iq.send()

    def send_example_iq_with_inner_tag(self, to):
        #~ make_iq(id=0, ifrom=None, ito=None, itype=None, iquery=None)
        iq = self.make_iq(ito=to,
                          itype="get",
                          id=2)
        iq['example_tag'].set_some_string("Another_string")
        iq['example_tag'].set_text("Info_inside_tag")
        
        inner_attributes = {"first_field": "1", "secound_field": "2"}
        iq['example_tag'].add_inside_tag(tag="inside_tag", attributes=inner_attributes)

        iq.send()

    def send_example_message(self, to):
        #~ make_message(mfrom=None, mto=None, mtype=None, mquery=None)
        msg = self.make_message(mto=to)
        msg['example_tag'].set_boolean(True)
        msg['example_tag'].set_some_string("Message string")
        msg['example_tag'].set_text("Info_inside_tag_message")
        msg.send()


if __name__ == '__main__':
    parser = ArgumentParser(description=Sender.__doc__)

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
                        help="JID to send the message/iq to")
    parser.add_argument("-a", "--path", dest="path",
                        help="path to load example_tag content")

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel,
                        format=' %(name)s - %(levelname)-8s %(message)s')

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")

    try:
        xmpp = Sender(args)
        xmpp.register_plugin('OurPlugin', module=example_plugin) # OurPlugin is a class name from example_plugin

        xmpp.connect()
        xmpp.process()
    except KeyboardInterrupt:
        xmpp.disconnect()
        exit(0)
