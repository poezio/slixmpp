"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp.plugins.base import BasePlugin
from slixmpp.plugins.xep_0108 import stanza, UserActivity


log = logging.getLogger(__name__)


class XEP_0108(BasePlugin):

    """
    XEP-0108: User Activity
    """

    name = 'xep_0108'
    description = 'XEP-0108: User Activity'
    dependencies = set(['xep_0163'])
    stanza = stanza

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=UserActivity.namespace)
        self.xmpp['xep_0163'].remove_interest(UserActivity.namespace)

    def session_bind(self, jid):
        self.xmpp['xep_0163'].register_pep('user_activity', UserActivity)

    def publish_activity(self, general, specific=None, text=None,
                         options=None, ifrom=None, callback=None,
                         timeout=None, timeout_callback=None):
        """
        Publish the user's current activity.

        Arguments:
            general  -- The required general category of the activity.
            specific -- Optional specific activity being done as part
                        of the general category.
            text     -- Optional natural-language description or reason
                        for the activity.
            options  -- Optional form of publish options.
            ifrom    -- Specify the sender's JID.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to slixmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        activity = UserActivity()
        activity['value'] = (general, specific)
        activity['text'] = text
        self.xmpp['xep_0163'].publish(activity, node=UserActivity.namespace,
                                      options=options, ifrom=ifrom,
                                      callback=callback,
                                      timeout=timeout,
                                      timeout_callback=timeout_callback)

    def stop(self, ifrom=None, callback=None, timeout=None,
             timeout_callback=None):
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
        activity = UserActivity()
        self.xmpp['xep_0163'].publish(activity, node=UserActivity.namespace,
                                      ifrom=ifrom, callback=callback,
                                      timeout=timeout,
                                      timeout_callback=timeout_callback)
