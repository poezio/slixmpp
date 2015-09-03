"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import hashlib
import logging

from slixmpp import Iq
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.xmlstream import register_stanza_plugin, JID
from slixmpp.plugins.xep_0084 import stanza, Data, MetaData


log = logging.getLogger(__name__)


class XEP_0084(BasePlugin):

    name = 'xep_0084'
    description = 'XEP-0084: User Avatar'
    dependencies = set(['xep_0163', 'xep_0060'])
    stanza = stanza

    def plugin_init(self):
        pubsub_stanza = self.xmpp['xep_0060'].stanza
        register_stanza_plugin(pubsub_stanza.Item, Data)
        register_stanza_plugin(pubsub_stanza.EventItem, Data)

        self.xmpp['xep_0060'].map_node_event(Data.namespace, 'avatar_data')

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=MetaData.namespace)
        self.xmpp['xep_0163'].remove_interest(MetaData.namespace)

    def session_bind(self, jid):
        self.xmpp['xep_0163'].register_pep('avatar_metadata', MetaData)

    def generate_id(self, data):
        return hashlib.sha1(data).hexdigest()

    def retrieve_avatar(self, jid, id, url=None, ifrom=None,
                              callback=None, timeout=None, timeout_callback=None):
        return self.xmpp['xep_0060'].get_item(jid, Data.namespace, id,
                ifrom=ifrom,
                callback=callback,
                timeout=timeout,
                timeout_callback=timeout_callback)

    def publish_avatar(self, data, ifrom=None, callback=None,
                             timeout=None, timeout_callback=None):
        payload = Data()
        payload['value'] = data
        return self.xmpp['xep_0163'].publish(payload,
                id=self.generate_id(data),
                ifrom=ifrom,
                callback=callback,
                timeout=timeout,
                timeout_callback=timeout_callback)

    def publish_avatar_metadata(self, items=None, pointers=None,
                                      ifrom=None,
                                      callback=None, timeout=None,
                                      timeout_callback=None):
        metadata = MetaData()
        if items is None:
            items = []
        if not isinstance(items, (list, set)):
            items = [items]
        for info in items:
            metadata.add_info(info['id'], info['type'], info['bytes'],
                    height=info.get('height', ''),
                    width=info.get('width', ''),
                    url=info.get('url', ''))

        if pointers is not None:
            for pointer in pointers:
                metadata.add_pointer(pointer)

        return self.xmpp['xep_0163'].publish(metadata,
                id=info['id'],
                ifrom=ifrom,
                callback=callback,
                timeout=timeout,
                timeout_callback=timeout_callback)

    def stop(self, ifrom=None, callback=None, timeout=None, timeout_callback=None):
        """
        Clear existing avatar metadata information to stop notifications.

        Arguments:
            ifrom    -- Specify the sender's JID.
            timeout  -- The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to slixmpp.xmlstream.RESPONSE_TIMEOUT
            callback -- Optional reference to a stream handler function. Will
                        be executed when a reply stanza is received.
        """
        metadata = MetaData()
        return self.xmpp['xep_0163'].publish(metadata,
                node=MetaData.namespace,
                ifrom=ifrom,
                callback=callback,
                timeout=timeout,
                timeout_callback=timeout_callback)
