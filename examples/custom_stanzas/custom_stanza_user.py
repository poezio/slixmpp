#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging
import getpass
from optparse import OptionParser

import slixmpp
from slixmpp import Iq
from slixmpp.exceptions import XMPPError
from slixmpp.xmlstream import register_stanza_plugin

from stanza import Action


class ActionUserBot(slixmpp.ClientXMPP):

    """
    A simple Slixmpp bot that sends a custom action stanza
    to another client.
    """

    def __init__(self, jid, password, other):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.action_provider = other

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

        register_stanza_plugin(Iq, Action)

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.send_presence()
        self.get_roster()

        self.send_custom_iq()

    def send_custom_iq(self):
        """Create and send two custom actions.

        If the first action was successful, then send
        a shutdown command and then disconnect.
        """
        iq = self.Iq()
        iq['to'] = self.action_provider
        iq['type'] = 'set'
        iq['action']['method'] = 'is_prime'
        iq['action']['param'] = '2'

        try:
            resp = iq.send()
            if resp['action']['status'] == 'done':
                #sending bye
                iq2 = self.Iq()
                iq2['to'] = self.action_provider
                iq2['type'] = 'set'
                iq2['action']['method'] = 'bye'
                iq2.send(block=False)
            
                # The wait=True delays the disconnect until the queue
                # of stanzas to be sent becomes empty.
                self.disconnect(wait=True)
        except XMPPError:
            print('There was an error sending the custom action.')

    def message(self, msg):
        """
        Process incoming message stanzas.

        Arguments:
            msg -- The received message stanza.
        """
        logging.info(msg['body'])

if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-o", "--other", dest="other",
                    help="JID providing custom stanza")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")
    if opts.other is None:
        opts.other = input("JID Providing custom stanza: ")

    # Setup the CommandBot and register plugins. Note that while plugins may
    # have interdependencies, the order in which you register them does
    # not matter.
    xmpp = ActionUserBot(opts.jid, opts.password, opts.other)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0050') # Adhoc Commands

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
