"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from typing import Optional, Callable, List
from slixmpp import JID
from slixmpp.xmlstream import register_stanza_plugin, ElementBase
from slixmpp.plugins.base import BasePlugin, register_plugin
from slixmpp.plugins.xep_0004.stanza import Form


log = logging.getLogger(__name__)


class XEP_0223(BasePlugin):

    """
    XEP-0223: Persistent Storage of Private Data via PubSub
    """

    name = 'xep_0223'
    description = 'XEP-0223: Persistent Storage of Private Data via PubSub'
    dependencies = {'xep_0163', 'xep_0060', 'xep_0004'}

    profile = {'pubsub#persist_items': True,
               'pubsub#access_model': 'whitelist'}

    def configure(self, node, ifrom=None, callback=None, timeout=None):
        """
        Update a node's configuration to match the public storage profile.
        """
        # TODO: that cannot possibly work, why is this here?
        config = self.xmpp['xep_0004'].Form()
        config['type'] = 'submit'

        for field, value in self.profile.items():
            config.add_field(var=field, value=value)

        return self.xmpp['xep_0060'].set_node_config(None, node, config,
                                                     ifrom=ifrom,
                                                     callback=callback,
                                                     timeout=timeout)

    def store(self, stanza: ElementBase, node: Optional[str] = None,
              id: Optional[str] = None, ifrom: Optional[JID] = None,
              options: Optional[Form] = None,
              callback: Optional[Callable] = None,
              timeout: Optional[int] = None,
              timeout_callback: Optional[Callable] = None):
        """
        Store private data via PEP.

        This is just a (very) thin wrapper around the XEP-0060 publish()
        method to set the defaults expected by PEP.

        :param stanza:  The private content to store.
        :param node: The node to publish the content to. If not specified,
                     the stanza's namespace will be used.
        :param id: Optionally specify the ID of the item.
        :param options: Publish options to use, which will be modified to
                        fit the persistent storage option profile.
        """
        if not options:
            options = self.xmpp['xep_0004'].stanza.Form()
            options['type'] = 'submit'
            options.add_field(
                var='FORM_TYPE',
                ftype='hidden',
                value='http://jabber.org/protocol/pubsub#publish-options')

        fields = options['fields']
        for field, value in self.profile.items():
            if field not in fields:
                options.add_field(var=field)
            options.get_fields()[field]['value'] = value

        return self.xmpp['xep_0163'].publish(stanza, node, options=options,
                                             ifrom=ifrom, callback=callback,
                                             timeout=timeout,
                                             timeout_callback=timeout_callback)

    def retrieve(self, node: str, id: Optional[str] = None,
                 item_ids: Optional[List[str]] = None,
                 ifrom: Optional[JID] = None,
                 callback: Optional[Callable] = None,
                 timeout: Optional[int] = None,
                 timeout_callback: Optional[Callable] = None):
        """
        Retrieve private data via PEP.

        This is just a (very) thin wrapper around the XEP-0060 publish()
        method to set the defaults expected by PEP.

        :param node: The node to retrieve content from.
        :param id: Optionally specify the ID of the item.
        :param item_ids: Specify a group of IDs. If id is also specified, it
                         will be included in item_ids.
        :param ifrom: Specify the sender's JID.
        :param timeout: The length of time (in seconds) to wait for a response
                        before exiting the send call if blocking is used.
                        Defaults to slixmpp.xmlstream.RESPONSE_TIMEOUT
        :param callback: Optional reference to a stream handler function. Will
                         be executed when a reply stanza is received.
        """
        if item_ids is None:
            item_ids = []
        if id is not None:
            item_ids.append(id)

        return self.xmpp['xep_0060'].get_items(None, node,
                                               item_ids=item_ids, ifrom=ifrom,
                                               callback=callback, timeout=timeout,
                                               timeout_callback=timeout_callback)


register_plugin(XEP_0223)
