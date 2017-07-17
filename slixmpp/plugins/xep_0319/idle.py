"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from datetime import datetime, timedelta, timezone

from slixmpp.stanza import Presence
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.plugins.xep_0319 import stanza


def get_local_timezone():
    return datetime.now(timezone.utc).astimezone().tzinfo


class XEP_0319(BasePlugin):
    name = 'xep_0319'
    description = 'XEP-0319: Last User Interaction in Presence'
    dependencies = {'xep_0012'}
    stanza = stanza

    def plugin_init(self):
        self._idle_stamps = {}
        register_stanza_plugin(Presence, stanza.Idle)
        self.api.register(self._set_idle,
                'set_idle',
                default=True)
        self.api.register(self._get_idle,
                'get_idle',
                default=True)
        self.xmpp.register_handler(
                Callback('Idle Presence',
                    StanzaPath('presence/idle'),
                    self._idle_presence))
        self.xmpp.add_filter('out', self._stamp_idle_presence)

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature('urn:xmpp:idle:1')

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature='urn:xmpp:idle:1')
        self.xmpp.del_filter('out', self._stamp_idle_presence)
        self.xmpp.remove_handler('Idle Presence')

    def idle(self, jid=None, since=None):
        seconds = None
        timezone = get_local_timezone()
        if since is None:
            since = datetime.now(timezone)
        else:
            seconds = datetime.now(timezone) - since
        self.api['set_idle'](jid, None, None, since)
        self.xmpp['xep_0012'].set_last_activity(jid=jid, seconds=seconds)

    def active(self, jid=None):
        self.api['set_idle'](jid, None, None, None)
        self.xmpp['xep_0012'].del_last_activity(jid)

    def _set_idle(self, jid, node, ifrom, data):
        self._idle_stamps[jid] = data

    def _get_idle(self, jid, node, ifrom, data):
        return self._idle_stamps.get(jid, None)

    def _idle_presence(self, pres):
        self.xmpp.event('presence_idle', pres)

    def _stamp_idle_presence(self, stanza):
        if isinstance(stanza, Presence):
            since = self.api['get_idle'](stanza['from'] or self.xmpp.boundjid)
            if since:
                stanza['idle']['since'] = since
        return stanza
