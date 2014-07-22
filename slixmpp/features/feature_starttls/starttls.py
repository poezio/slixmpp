"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2011  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp.stanza import StreamFeatures
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream.matcher import MatchXPath
from slixmpp.xmlstream.handler import Callback
from slixmpp.features.feature_starttls import stanza


log = logging.getLogger(__name__)


class FeatureSTARTTLS(BasePlugin):

    name = 'feature_starttls'
    description = 'RFC 6120: Stream Feature: STARTTLS'
    dependencies = set()
    stanza = stanza

    def plugin_init(self):
        self.xmpp.register_handler(
                Callback('STARTTLS Proceed',
                        MatchXPath(stanza.Proceed.tag_name()),
                        self._handle_starttls_proceed,
                        instream=True))
        self.xmpp.register_feature('starttls',
                self._handle_starttls,
                restart=True,
                order=self.config.get('order', 0))

        self.xmpp.register_stanza(stanza.Proceed)
        self.xmpp.register_stanza(stanza.Failure)
        register_stanza_plugin(StreamFeatures, stanza.STARTTLS)

    def _handle_starttls(self, features):
        """
        Handle notification that the server supports TLS.

        Arguments:
            features -- The stream:features element.
        """
        if 'starttls' in self.xmpp.features:
            # We have already negotiated TLS, but the server is
            # offering it again, against spec.
            return False
        elif self.xmpp.disable_starttls:
            return False
        else:
            self.xmpp.send(features['starttls'])
            return True

    def _handle_starttls_proceed(self, proceed):
        """Restart the XML stream when TLS is accepted."""
        log.debug("Starting TLS")
        if self.xmpp.start_tls():
            self.xmpp.features.add('starttls')
