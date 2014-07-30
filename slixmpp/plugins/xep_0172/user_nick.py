"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp.stanza.message import Message
from slixmpp.stanza.presence import Presence
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import MatchXPath
from slixmpp.plugins.base import BasePlugin
from slixmpp.plugins.xep_0172 import stanza, UserNick


log = logging.getLogger(__name__)


class XEP_0172(BasePlugin):

    """
    XEP-0172: User Nickname
    """

    name = 'xep_0172'
    description = 'XEP-0172: User Nickname'
    dependencies = set(['xep_0163'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, UserNick)
        register_stanza_plugin(Presence, UserNick)

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=UserNick.namespace)
        self.xmpp['xep_0163'].remove_interest(UserNick.namespace)

    def session_bind(self, jid):
        self.xmpp['xep_0163'].register_pep('user_nick', UserNick)

    def publish_nick(self, nick=None, options=None, ifrom=None, timeout_callback=None,
                     callback=None, timeout=None):
        """
        Publish the user's current nick.

        Arguments:
            nick     -- The user nickname to publish.
            options  -- Optional form of publish options.
            ifrom    -- Specify the sender's JID.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to slixmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        nickname = UserNick()
        nickname['nick'] = nick
        self.xmpp['xep_0163'].publish(nickname, node=UserNick.namespace,
                                      options=options, ifrom=ifrom,
                                      callback=callback, timeout=timeout,
                                      timeout_callback=timeout_callback)

    def stop(self, ifrom=None, timeout_callback=None, callback=None, timeout=None):
        """
        Clear existing user nick information to stop notifications.

        Arguments:
            ifrom    -- Specify the sender's JID.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to slixmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        nick = UserNick()
        return self.xmpp['xep_0163'].publish(nick, node=UserNick.namespace,
                                             ifrom=ifrom, callback=callback,
                                             timeout=timeout,
                                             timeout_callback=timeout_callback)
