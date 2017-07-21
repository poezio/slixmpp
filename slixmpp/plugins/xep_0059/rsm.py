"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Erik Reuterborg Larsson
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

import slixmpp
from slixmpp import Iq
from slixmpp.plugins import BasePlugin, register_plugin
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins.xep_0059 import stanza, Set
from slixmpp.exceptions import XMPPError


log = logging.getLogger(__name__)


class ResultIterator:

    """
    An iterator for Result Set Managment
    """

    def __init__(self, query, interface, results='substanzas', amount=10,
                       start=None, reverse=False, recv_interface=None,
                       pre_cb=None, post_cb=None):
        """
        Arguments:
           query     -- The template query
           interface -- The substanza of the query to send, for example disco_items
           recv_interface -- The substanza of the query to receive, for example disco_items
           results   -- The query stanza's interface which provides a
                        countable list of query results.
           amount    -- The max amounts of items to request per iteration
           start     -- From which item id to start
           reverse   -- If True, page backwards through the results
           pre_cb    -- Callback to run before sending the stanza
           post_cb   -- Callback to run after receiving the reply

        Example:
           q = Iq()
           q['to'] = 'pubsub.example.com'
           q['disco_items']['node'] = 'blog'
           for i in ResultIterator(q, 'disco_items', '10'):
               print i['disco_items']['items']

        """
        self.query = query
        self.amount = amount
        self.start = start
        self.interface = interface
        if recv_interface:
            self.recv_interface = recv_interface
        else:
            self.recv_interface = interface
        self.pre_cb = pre_cb
        self.post_cb = post_cb
        self.results = results
        self.reverse = reverse
        self._stop = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.next()

    async def next(self):
        """
        Return the next page of results from a query.

        Note: If using backwards paging, then the next page of
              results will be the items before the current page
              of items.
        """
        if self._stop:
            raise StopAsyncIteration
        self.query[self.interface]['rsm']['before'] = self.reverse
        self.query['id'] = self.query.stream.new_id()
        self.query[self.interface]['rsm']['max'] = str(self.amount)

        if self.start and self.reverse:
            self.query[self.interface]['rsm']['before'] = self.start
        elif self.start:
            self.query[self.interface]['rsm']['after'] = self.start

        try:
            if self.pre_cb:
                self.pre_cb(self.query)
            r = await self.query.send()

            if not r[self.recv_interface]['rsm']['first'] and \
               not r[self.recv_interface]['rsm']['last']:
                raise StopAsyncIteration

            if r[self.recv_interface]['rsm']['count'] and \
               r[self.recv_interface]['rsm']['first_index']:
                count = int(r[self.recv_interface]['rsm']['count'])
                first = int(r[self.recv_interface]['rsm']['first_index'])
                num_items = len(r[self.recv_interface][self.results])
                if first + num_items == count:
                    self._stop = True

            if self.reverse:
                self.start = r[self.recv_interface]['rsm']['first']
            else:
                self.start = r[self.recv_interface]['rsm']['last']

            if self.post_cb:
                self.post_cb(r)
            return r
        except XMPPError:
            raise StopAsyncIteration


class XEP_0059(BasePlugin):

    """
    XEP-0050: Result Set Management
    """

    name = 'xep_0059'
    description = 'XEP-0059: Result Set Management'
    dependencies = {'xep_0030'}
    stanza = stanza

    def plugin_init(self):
        """
        Start the XEP-0059 plugin.
        """
        register_stanza_plugin(self.xmpp['xep_0030'].stanza.DiscoItems,
                               self.stanza.Set)

    def plugin_end(self):
        self.xmpp['xep_0030'].del_feature(feature=Set.namespace)

    def session_bind(self, jid):
        self.xmpp['xep_0030'].add_feature(Set.namespace)

    def iterate(self, stanza, interface, results='substanzas',
                recv_interface=None, pre_cb=None, post_cb=None):
        """
        Create a new result set iterator for a given stanza query.

        Arguments:
            stanza    -- A stanza object to serve as a template for
                         queries made each iteration. For example, a
                         basic disco#items query.
            interface -- The name of the substanza to which the
                         result set management stanza should be
                         appended in the query stanza. For example,
                         for disco#items queries the interface
                         'disco_items' should be used.
            recv_interface -- The name of the substanza from which the
                              result set management stanza should be
                              read in the result stanza. If unspecified,
                              it will be set to the same value as the
                              ``interface`` parameter.
            pre_cb    -- Callback to run before sending each stanza e.g.
                         setting the MAM queryid and starting a stanza
                         collector.
            post_cb   -- Callback to run after receiving each stanza e.g.
                         stopping a MAM stanza collector in order to
                         gather results.
            results   -- The name of the interface containing the
                         query results (typically just 'substanzas').
        """
        return ResultIterator(stanza, interface, results,
                              recv_interface=recv_interface, pre_cb=pre_cb,
                              post_cb=post_cb)
