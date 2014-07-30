"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp.stanza import Iq, StreamFeatures
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins import BasePlugin

from slixmpp.features.feature_session import stanza


log = logging.getLogger(__name__)


class FeatureSession(BasePlugin):

    name = 'feature_session'
    description = 'RFC 3920: Stream Feature: Start Session'
    dependencies = set()
    stanza = stanza

    def plugin_init(self):
        self.xmpp.register_feature('session',
                self._handle_start_session,
                restart=False,
                order=10001)

        register_stanza_plugin(Iq, stanza.Session)
        register_stanza_plugin(StreamFeatures, stanza.Session)

    def _handle_start_session(self, features):
        """
        Handle the start of the session.

        Arguments:
            feature -- The stream features element.
        """
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq.enable('session')
        iq.send(callback=self._on_start_session_response)

    def _on_start_session_response(self, response):
        self.xmpp.features.add('session')

        log.debug("Established Session")
        self.xmpp.sessionstarted = True
        self.xmpp.event('session_start')
