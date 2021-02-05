
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
# This file is part of slixmpp.
# See the file LICENSE for copying permission.
from slixmpp.stanza import Iq, Message
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins import BasePlugin
from slixmpp.plugins.google.nosave import stanza


class GoogleNoSave(BasePlugin):

    """
    Google: Off the Record Chats

    NOTE: This is NOT an encryption method.

    Also see <https://developers.google.com/talk/jep_extensions/otr>.
    """

    name = 'google_nosave'
    description = 'Google: Off the Record Chats'
    dependencies = set(['google_settings'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Message, stanza.NoSave)
        register_stanza_plugin(Iq, stanza.NoSaveQuery)

        self.xmpp.register_handler(
                Callback('Google Nosave',
                    StanzaPath('iq@type=set/google_nosave'),
                    self._handle_nosave_change))

    def plugin_end(self):
        self.xmpp.remove_handler('Google Nosave')

    def enable(self, jid=None, timeout=None, callback=None):
        if jid is None:
            self.xmpp['google_settings'].update({'archiving_enabled': False},
                    timeout=timeout, callback=callback)
        else:
            iq = self.xmpp.Iq()
            iq['type'] = 'set'
            iq['google_nosave']['item']['jid'] = jid
            iq['google_nosave']['item']['value'] = True
            return iq.send(timeout=timeout, callback=callback)

    def disable(self, jid=None, timeout=None, callback=None):
        if jid is None:
            self.xmpp['google_settings'].update({'archiving_enabled': True},
                    timeout=timeout, callback=callback)
        else:
            iq = self.xmpp.Iq()
            iq['type'] = 'set'
            iq['google_nosave']['item']['jid'] = jid
            iq['google_nosave']['item']['value'] = False
            return iq.send(timeout=timeout, callback=callback)

    def get(self, timeout=None, callback=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'get'
        iq.enable('google_nosave')
        return iq.send(timeout=timeout, callback=callback)

    def _handle_nosave_change(self, iq):
        reply = self.xmpp.Iq()
        reply['type'] = 'result'
        reply['id'] = iq['id']
        reply['to'] = iq['from']
        reply.send()
        self.xmpp.event('google_nosave_change', iq)
