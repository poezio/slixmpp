"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import time
import logging

from slixmpp.jid import JID
from slixmpp.stanza import Iq
from slixmpp import asyncio
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.xmlstream.handler import Callback
from slixmpp.plugins import BasePlugin
from slixmpp.plugins.xep_0199 import stanza, Ping


log = logging.getLogger(__name__)


class XEP_0199(BasePlugin):

    """
    XEP-0199: XMPP Ping

    Given that XMPP is based on TCP connections, it is possible for the
    underlying connection to be terminated without the application's
    awareness. Ping stanzas provide an alternative to whitespace based
    keepalive methods for detecting lost connections.

    Also see <http://www.xmpp.org/extensions/xep-0199.html>.

    Attributes:
        keepalive -- If True, periodically send ping requests
                     to the server. If a ping is not answered,
                     the connection will be reset.
        interval  -- Time in seconds between keepalive pings.
                     Defaults to 300 seconds.
        timeout   -- Time in seconds to wait for a ping response.
                     Defaults to 30 seconds.
    Methods:
        send_ping -- Send a ping to a given JID, returning the
                     round trip time.
    """

    name = 'xep_0199'
    description = 'XEP-0199: XMPP Ping'
    dependencies = set(['xep_0030'])
    stanza = stanza
    default_config = {
        'keepalive': False,
        'interval': 300,
        'timeout': 30
    }

    def plugin_init(self):
        """
        Start the XEP-0199 plugin.
        """

        register_stanza_plugin(Iq, Ping)

        self.xmpp.register_handler(
                Callback('Ping',
                         StanzaPath('iq@type=get/ping'),
                         self._handle_ping))

        if self.keepalive:
            self.xmpp.add_event_handler('session_start',
                                        self.enable_keepalive)
            self.xmpp.add_event_handler('session_end',
                                        self.disable_keepalive)

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=Ping.namespace)
        self.xmpp.remove_handler('Ping')
        if self.keepalive:
            self.xmpp.del_event_handler('session_start',
                                        self.enable_keepalive)
            self.xmpp.del_event_handler('session_end',
                                        self.disable_keepalive)

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature(Ping.namespace)

    def enable_keepalive(self, interval=None, timeout=None):
        if interval:
            self.interval = interval
        if timeout:
            self.timeout = timeout

        self.keepalive = True
        self.xmpp.schedule('Ping keepalive',
                           self.interval,
                           self._keepalive,
                           repeat=True)

    def disable_keepalive(self, event=None):
        self.xmpp.cancel_schedule('Ping keepalive')

    def _keepalive(self, event=None):
        log.debug("Keepalive ping...")
        try:
            rtt = self.ping(self.xmpp.boundjid.host, timeout=self.timeout)
        except IqTimeout:
            log.debug("Did not recieve ping back in time." + \
                      "Requesting Reconnect.")
            self.xmpp.reconnect()
        else:
            log.debug('Keepalive RTT: %s' % rtt)

    def _handle_ping(self, iq):
        """Automatically reply to ping requests."""
        log.debug("Pinged by %s", iq['from'])
        iq.reply().send()

    def send_ping(self, jid, ifrom=None, timeout=None, callback=None,
                  timeout_callback=None):
        """Send a ping request.

        Arguments:
            jid        -- The JID that will receive the ping.
            ifrom      -- Specifiy the sender JID.
            timeout    -- Time in seconds to wait for a response.
                          Defaults to self.timeout.
            callback   -- Optional handler to execute when a pong
                          is received.
        """
        if not timeout:
            timeout = self.timeout

        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq['to'] = jid
        iq['from'] = ifrom
        iq.enable('ping')

        return iq.send(timeout=timeout, callback=callback,
                       timeout_callback=timeout_callback)

    @asyncio.coroutine
    def ping(self, jid=None, ifrom=None, timeout=None):
        """Send a ping request and calculate RTT.
        This is a coroutine.

        Arguments:
            jid        -- The JID that will receive the ping.
            ifrom      -- Specifiy the sender JID.
            timeout    -- Time in seconds to wait for a response.
                          Defaults to self.timeout.
        """
        own_host = False
        if not jid:
            if self.xmpp.is_component:
                jid = self.xmpp.server
            else:
                jid = self.xmpp.boundjid.host
        jid = JID(jid)
        if jid == self.xmpp.boundjid.host or \
                self.xmpp.is_component and jid == self.xmpp.server:
            own_host = True

        if not timeout:
            timeout = self.timeout

        start = time.time()

        log.debug('Pinging %s' % jid)
        try:
            yield from self.send_ping(jid, ifrom=ifrom, timeout=timeout,
                                      coroutine=True)
        except IqError as e:
            if own_host:
                rtt = time.time() - start
                log.debug('Pinged %s, RTT: %s', jid, rtt)
                return rtt
            else:
                raise e
        else:
            rtt = time.time() - start
            log.debug('Pinged %s, RTT: %s', jid, rtt)
            return rtt
