"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins.xep_0221 import stanza, Media, URI
from slixmpp.plugins.xep_0004 import FormField


log = logging.getLogger(__name__)


class XEP_0221(BasePlugin):

    name = 'xep_0221'
    description = 'XEP-0221: Data Forms Media Element'
    dependencies = set(['xep_0004'])

    def plugin_init(self):
        register_stanza_plugin(FormField, Media)
