"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp.plugins.base import BasePlugin
from slixmpp.plugins.xep_0152 import stanza, Reachability


log = logging.getLogger(__name__)


class XEP_0152(BasePlugin):

    """
    XEP-0152: Reachability Addresses
    """

    name = 'xep_0152'
    description = 'XEP-0152: Reachability Addresses'
    dependencies = set(['xep_0163'])
    stanza = stanza

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=Reachability.namespace)
        self.xmpp['xep_0163'].remove_interest(Reachability.namespace)

    def session_bind(self, jid):
        self.xmpp['xep_0163'].register_pep('reachability', Reachability)

    def publish_reachability(self, addresses, options=None, ifrom=None,
                             callback=None, timeout=None,
                             timeout_callback=None):
        """
        Publish alternative addresses where the user can be reached.

        Arguments:
            addresses -- A list of dictionaries containing the URI and
                         optional description for each address.
            options   -- Optional form of publish options.
            ifrom     -- Specify the sender's JID.
            timeout   -- The length of time (in seconds) to wait for a response
                         before exiting the send call if blocking is used.
                         Defaults to slixmpp.xmlstream.RESPONSE_TIMEOUT
            callback  -- Optional reference to a stream handler function. Will
                         be executed when a reply stanza is received.
        """
        if not isinstance(addresses, (list, tuple)):
            addresses = [addresses]
        reach = Reachability()
        for address in addresses:
            if not hasattr(address, 'items'):
                address = {'uri': address}

            addr = stanza.Address()
            for key, val in address.items():
                addr[key] = val
            reach.append(addr)
        return self.xmpp['xep_0163'].publish(reach,
                node=Reachability.namespace,
                options=options,
                ifrom=ifrom,
                callback=callback,
                timeout=timeout,
                timeout_callback=timeout_callback)

    def stop(self, ifrom=None, callback=None, timeout=None, timeout_callback=None):
        """
        Clear existing user activity information to stop notifications.

        Arguments:
            ifrom    -- Specify the sender's JID.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to slixmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        reach = Reachability()
        return self.xmpp['xep_0163'].publish(reach,
                node=Reachability.namespace,
                ifrom=ifrom,
                callback=callback,
                timeout=timeout,
                timeout_callback=timeout_callback)
