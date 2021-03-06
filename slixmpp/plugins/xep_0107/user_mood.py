"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2011 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp import Message
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import MatchXPath
from slixmpp.plugins.base import BasePlugin
from slixmpp.plugins.xep_0107 import stanza, UserMood


log = logging.getLogger(__name__)


class XEP_0107(BasePlugin):

    """
    XEP-0107: User Mood
    """

    name = 'xep_0107'
    description = 'XEP-0107: User Mood'
    dependencies = {'xep_0163'}
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, UserMood)

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=UserMood.namespace)
        self.xmpp['xep_0163'].remove_interest(UserMood.namespace)

    def session_bind(self, jid):
        self.xmpp['xep_0163'].register_pep('user_mood', UserMood)

    def publish_mood(self, value=None, text=None, options=None, ifrom=None,
                     callback=None, timeout=None, timeout_callback=None):
        """
        Publish the user's current mood.

        :param value: The name of the mood to publish.
        :param text: Optional natural-language description or reason
                     for the mood.
        :param options: Optional form of publish options.
        """
        mood = UserMood()
        mood['value'] = value
        mood['text'] = text
        self.xmpp['xep_0163'].publish(mood, node=UserMood.namespace,
                                      options=options, ifrom=ifrom,
                                      callback=callback, timeout=timeout,
                                      timeout_callback=timeout_callback)

    def stop(self, ifrom=None, callback=None, timeout=None,
             timeout_callback=None):
        """
        Clear existing user mood information to stop notifications.
        """
        mood = UserMood()
        self.xmpp['xep_0163'].publish(mood, node=UserMood.namespace,
                                      ifrom=ifrom, callback=callback,
                                      timeout=timeout,
                                      timeout_callback=timeout_callback)
