"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permissio
"""

import logging

import slixmpp
from slixmpp.stanza import Message, Iq
from slixmpp.exceptions import XMPPError
from slixmpp.xmlstream.handler import Collector
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins import BasePlugin
from slixmpp.plugins.xep_0313 import stanza


log = logging.getLogger(__name__)


class XEP_0313(BasePlugin):

    """
    XEP-0313 Message Archive Management
    """

    name = 'xep_0313'
    description = 'XEP-0313: Message Archive Management'
    dependencies = {'xep_0030', 'xep_0050', 'xep_0059', 'xep_0297'}
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(Iq, stanza.MAM)
        register_stanza_plugin(Iq, stanza.Preferences)
        register_stanza_plugin(Message, stanza.Result)
        register_stanza_plugin(Iq, stanza.Fin)
        register_stanza_plugin(stanza.Result, self.xmpp['xep_0297'].stanza.Forwarded)
        register_stanza_plugin(stanza.MAM, self.xmpp['xep_0059'].stanza.Set)
        register_stanza_plugin(stanza.Fin, self.xmpp['xep_0059'].stanza.Set)

    def retrieve(self, jid=None, start=None, end=None, with_jid=None, ifrom=None,
                 timeout=None, callback=None, iterator=False, rsm=None):
        iq = self.xmpp.Iq()
        query_id = iq['id']

        iq['to'] = jid
        iq['from'] = ifrom
        iq['type'] = 'set'
        iq['mam']['queryid'] = query_id
        iq['mam']['start'] = start
        iq['mam']['end'] = end
        iq['mam']['with'] = with_jid
        if rsm:
            for key, value in rsm.items():
                iq['mam']['rsm'][key] = str(value)

        cb_data = {}
        def pre_cb(query):
            query['mam']['queryid'] = query['id']
            collector = Collector(
                'MAM_Results_%s' % query_id,
                StanzaPath('message/mam_result@queryid=%s' % query['id']))
            self.xmpp.register_handler(collector)
            cb_data['collector'] = collector

        def post_cb(result):
            results = cb_data['collector'].stop()
            if result['type'] == 'result':
                result['mam']['results'] = results

        if iterator:
            return self.xmpp['xep_0059'].iterate(iq, 'mam', 'results',
                                                 recv_interface='mam_fin',
                                                 pre_cb=pre_cb, post_cb=post_cb)

        collector = Collector(
            'MAM_Results_%s' % query_id,
            StanzaPath('message/mam_result@queryid=%s' % query_id))
        self.xmpp.register_handler(collector)

        def wrapped_cb(iq):
            results = collector.stop()
            if iq['type'] == 'result':
                iq['mam']['results'] = results
            if callback:
                callback(iq)

        return iq.send(timeout=timeout, callback=wrapped_cb)

    def set_preferences(self, jid=None, default=None, always=None, never=None,
                        ifrom=None, block=True, timeout=None, callback=None):
        iq = self.xmpp.Iq()
        iq['type'] = 'set'
        iq['to'] = jid
        iq['from'] = ifrom
        iq['mam_prefs']['default'] = default
        iq['mam_prefs']['always'] = always
        iq['mam_prefs']['never'] = never
        return iq.send(block=block, timeout=timeout, callback=callback)

    def get_configuration_commands(self, jid, **kwargs):
        return self.xmpp['xep_0030'].get_items(
                jid=jid,
                node='urn:xmpp:mam#configure',
                **kwargs)
