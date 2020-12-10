"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz, Lance J.T. Stout
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import asyncio
import logging


from typing import Optional, Callable

from slixmpp import Iq
from slixmpp import future_wrapper
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.xmlstream import register_stanza_plugin, JID
from slixmpp.plugins.xep_0030 import stanza, DiscoInfo, DiscoItems
from slixmpp.plugins.xep_0030 import StaticDisco


log = logging.getLogger(__name__)


class XEP_0030(BasePlugin):

    """
    XEP-0030: Service Discovery

    Service discovery in XMPP allows entities to discover information about
    other agents in the network, such as the feature sets supported by a
    client, or signposts to other, related entities.

    Also see <http://www.xmpp.org/extensions/xep-0030.html>.

    The XEP-0030 plugin works using a hierarchy of dynamic
    node handlers, ranging from global handlers to specific
    JID+node handlers. The default set of handlers operate
    in a static manner, storing disco information in memory.
    However, custom handlers may use any available backend
    storage mechanism desired, such as SQLite or Redis.

    Node handler hierarchy:

    ::

        JID   | Node  | Level
        ---------------------
        None  | None  | Global
        Given | None  | All nodes for the JID
        None  | Given | Node on self.xmpp.boundjid
        Given | Given | A single node

    Stream Handlers:

    ::

        Disco Info  -- Any Iq stanze that includes a query with the
                       namespace http://jabber.org/protocol/disco#info.
        Disco Items -- Any Iq stanze that includes a query with the
                       namespace http://jabber.org/protocol/disco#items.

    Events:

    ::

        disco_info         -- Received a disco#info Iq query result.
        disco_items        -- Received a disco#items Iq query result.
        disco_info_query   -- Received a disco#info Iq query request.
        disco_items_query  -- Received a disco#items Iq query request.

    Attributes:

    :var static: Object containing the default set of
                 static node handlers.
    :var default_handlers: A dictionary mapping operations to the default
                           global handler (by default, the static handlers).
    """

    name = 'xep_0030'
    description = 'XEP-0030: Service Discovery'
    dependencies = set()
    stanza = stanza
    default_config = {
        'use_cache': True,
        'wrap_results': False
    }

    def plugin_init(self):
        """
        Start the XEP-0030 plugin.
        """
        self.xmpp.register_handler(
                Callback('Disco Info',
                         StanzaPath('iq/disco_info'),
                         self._handle_disco_info))

        self.xmpp.register_handler(
                Callback('Disco Items',
                         StanzaPath('iq/disco_items'),
                         self._handle_disco_items))

        register_stanza_plugin(Iq, DiscoInfo)
        register_stanza_plugin(Iq, DiscoItems)

        self.static = StaticDisco(self.xmpp, self)

        self._disco_ops = [
                'get_info', 'set_info', 'set_identities', 'set_features',
                'get_items', 'set_items', 'del_items', 'add_identity',
                'del_identity', 'add_feature', 'del_feature', 'add_item',
                'del_item', 'del_identities', 'del_features', 'cache_info',
                'get_cached_info', 'supports', 'has_identity']

        for op in self._disco_ops:
            self.api.register(getattr(self.static, op), op, default=True)

        self.domain_infos = {}

    def session_bind(self, jid):
        self.add_feature('http://jabber.org/protocol/disco#info')

    def plugin_end(self):
        self.del_feature('http://jabber.org/protocol/disco#info')

    def _add_disco_op(self, op, default_handler):
        self.api.register(default_handler, op)
        self.api.register_default(default_handler, op)

    def set_node_handler(self, htype: str, jid: Optional[JID] = None,
                         node: Optional[str] = None,
                         handler: Optional[Callable] = None):
        """
        Add a node handler for the given hierarchy level and
        handler type.

        Node handlers are ordered in a hierarchy where the
        most specific handler is executed. Thus, a fallback,
        global handler can be used for the majority of cases
        with a few node specific handler that override the
        global behavior.

        Node handler hierarchy:

        ::

            JID   | Node  | Level
            ---------------------
            None  | None  | Global
            Given | None  | All nodes for the JID
            None  | Given | Node on self.xmpp.boundjid
            Given | Given | A single node

        Handler types:

        ::

            get_info
            get_items
            set_identities
            set_features
            set_items
            del_items
            del_identities
            del_identity
            del_feature
            del_features
            del_item
            add_identity
            add_feature
            add_item

        :param htype: The operation provided by the handler.
        :param jid: The JID the handler applies to. May be narrowed
                    further if a node is given.
        :param node: The particular node the handler is for. If no JID
                     is given, then the self.xmpp.boundjid.full is
                     assumed.
        :param handler: The handler function to use.
        """
        self.api.register(handler, htype, jid, node)

    def del_node_handler(self, htype, jid, node):
        """
        Remove a handler type for a JID and node combination.

        The next handler in the hierarchy will be used if one
        exists. If removing the global handler, make sure that
        other handlers exist to process existing nodes.

        Node handler hierarchy:

        ::

            JID   | Node  | Level
            ---------------------
            None  | None  | Global
            Given | None  | All nodes for the JID
            None  | Given | Node on self.xmpp.boundjid
            Given | Given | A single node

        :param htype: The type of handler to remove.
        :param jid: The JID from which to remove the handler.
        :param node: The node from which to remove the handler.
        """
        self.api.unregister(htype, jid, node)

    def restore_defaults(self, jid=None, node=None, handlers=None):
        """
        Change all or some of a node's handlers to the default
        handlers. Useful for manually overriding the contents
        of a node that would otherwise be handled by a JID level
        or global level dynamic handler.

        The default is to use the built-in static handlers, but that
        may be changed by modifying self.default_handlers.

        :param jid: The JID owning the node to modify.
        :param node: The node to change to using static handlers.
        :param handlers: Optional list of handlers to change to the
                         default version. If provided, only these
                         handlers will be changed. Otherwise, all
                         handlers will use the default version.
        """
        if handlers is None:
            handlers = self._disco_ops
        for op in handlers:
            self.api.restore_default(op, jid, node)

    def supports(self, jid=None, node=None, feature=None, local=False,
                       cached=True, ifrom=None):
        """
        Check if a JID supports a given feature.

        Return values:
        :param True: The feature is supported
        :param False: The feature is not listed as supported
        :param None: Nothing could be found due to a timeout

        :param jid: Request info from this JID.
        :param node: The particular node to query.
        :param feature: The name of the feature to check.
        :param local: If true, then the query is for a JID/node
                      combination handled by this Slixmpp instance and
                      no stanzas need to be sent.
                      Otherwise, a disco stanza must be sent to the
                      remove JID to retrieve the info.
        :param cached: If true, then look for the disco info data from
                       the local cache system. If no results are found,
                       send the query as usual. The self.use_cache
                       setting must be set to true for this option to
                       be useful. If set to false, then the cache will
                       be skipped, even if a result has already been
                       cached. Defaults to false.
        """
        data = {'feature': feature,
                'local': local,
                'cached': cached}
        return self.api['supports'](jid, node, ifrom, data)

    def has_identity(self, jid=None, node=None, category=None, itype=None,
                     lang=None, local=False, cached=True, ifrom=None):
        """
        Check if a JID provides a given identity.

        Return values:
        :param True: The identity is provided
        :param False: The identity is not listed
        :param None: Nothing could be found due to a timeout

        :param jid: Request info from this JID.
        :param node: The particular node to query.
        :param category: The category of the identity to check.
        :param itype: The type of the identity to check.
        :param lang: The language of the identity to check.
        :param local: If true, then the query is for a JID/node
                        combination handled by this Slixmpp instance and
                        no stanzas need to be sent.
                        Otherwise, a disco stanza must be sent to the
                        remove JID to retrieve the info.
        :param cached: If true, then look for the disco info data from
                        the local cache system. If no results are found,
                        send the query as usual. The self.use_cache
                        setting must be set to true for this option to
                        be useful. If set to false, then the cache will
                        be skipped, even if a result has already been
                        cached. Defaults to false.
        """
        data = {'category': category,
                'itype': itype,
                'lang': lang,
                'local': local,
                'cached': cached}
        return self.api['has_identity'](jid, node, ifrom, data)

    async def get_info_from_domain(self, domain=None, timeout=None,
                                   cached=True, callback=None):
        """Fetch disco#info of specified domain and one disco#items level below"""

        if domain is None:
            domain = self.xmpp.boundjid.domain

        if not cached or domain not in self.domain_infos:
            infos = [self.get_info(
                domain, timeout=timeout)]
            iq_items = await self.get_items(
                domain, timeout=timeout)
            items = iq_items['disco_items']['items']
            infos += [
                self.get_info(item[0], timeout=timeout)
                for item in items]
            info_futures, _ = await asyncio.wait(
                infos,
                timeout=timeout,
                loop=self.xmpp.loop
            )

            self.domain_infos[domain] = [
                future.result() for future in info_futures if not future.exception()]

        results = self.domain_infos[domain]

        if callback is not None:
            callback(results)
        return results

    @future_wrapper
    def get_info(self, jid=None, node=None, local=None,
                       cached=None, **kwargs):
        """
        Retrieve the disco#info results from a given JID/node combination.

        Info may be retrieved from both local resources and remote agents;
        the local parameter indicates if the information should be gathered
        by executing the local node handlers, or if a disco#info stanza
        must be generated and sent.

        If requesting items from a local JID/node, then only a DiscoInfo
        stanza will be returned. Otherwise, an Iq stanza will be returned.

        :param jid: Request info from this JID.
        :param node: The particular node to query.
        :param local: If true, then the query is for a JID/node
                      combination handled by this Slixmpp instance and
                      no stanzas need to be sent.
                      Otherwise, a disco stanza must be sent to the
                      remote JID to retrieve the info.
        :param cached: If true, then look for the disco info data from
                       the local cache system. If no results are found,
                       send the query as usual. The self.use_cache
                       setting must be set to true for this option to
                       be useful. If set to false, then the cache will
                       be skipped, even if a result has already been
                       cached. Defaults to false.
        """
        if local is None:
            if jid is not None and not isinstance(jid, JID):
                jid = JID(jid)
                if self.xmpp.is_component:
                    if jid.domain == self.xmpp.boundjid.domain:
                        local = True
                else:
                    if str(jid) == str(self.xmpp.boundjid):
                        local = True
                jid = jid.full
            elif jid in (None, ''):
                local = True

        if local:
            log.debug("Looking up local disco#info data " + \
                      "for %s, node %s.", jid, node)
            info = self.api['get_info'](jid, node,
                    kwargs.get('ifrom', None),
                    kwargs)
            info = self._fix_default_info(info)
            return self._wrap(kwargs.get('ifrom', None), jid, info)

        if cached:
            log.debug("Looking up cached disco#info data " + \
                      "for %s, node %s.", jid, node)
            info = self.api['get_cached_info'](jid, node,
                    kwargs.get('ifrom', None),
                    kwargs)
            if info is not None:
                return self._wrap(kwargs.get('ifrom', None), jid, info)

        iq = self.xmpp.Iq()
        # Check dfrom parameter for backwards compatibility
        iq['from'] = kwargs.get('ifrom', kwargs.get('dfrom', ''))
        iq['to'] = jid
        iq['type'] = 'get'
        iq['disco_info']['node'] = node if node else ''
        return iq.send(timeout=kwargs.get('timeout', None),
                       callback=kwargs.get('callback', None),
                       timeout_callback=kwargs.get('timeout_callback', None))

    def set_info(self, jid=None, node=None, info=None):
        """
        Set the disco#info data for a JID/node based on an existing
        disco#info stanza.
        """
        if isinstance(info, Iq):
            info = info['disco_info']
        self.api['set_info'](jid, node, None, info)

    @future_wrapper
    def get_items(self, jid=None, node=None, local=False, **kwargs):
        """
        Retrieve the disco#items results from a given JID/node combination.

        Items may be retrieved from both local resources and remote agents;
        the local parameter indicates if the items should be gathered by
        executing the local node handlers, or if a disco#items stanza must
        be generated and sent.

        If requesting items from a local JID/node, then only a DiscoItems
        stanza will be returned. Otherwise, an Iq stanza will be returned.

        :param jid: Request info from this JID.
        :param node: The particular node to query.
        :param local: If true, then the query is for a JID/node
                      combination handled by this Slixmpp instance and
                      no stanzas need to be sent.
                      Otherwise, a disco stanza must be sent to the
                      remove JID to retrieve the items.
        :param iterator: If True, return a result set iterator using
                         the XEP-0059 plugin, if the plugin is loaded.
                         Otherwise the parameter is ignored.
        """
        if local or local is None and jid is None:
            items = self.api['get_items'](jid, node,
                    kwargs.get('ifrom', None),
                    kwargs)
            return self._wrap(kwargs.get('ifrom', None), jid, items)

        iq = self.xmpp.Iq()
        # Check dfrom parameter for backwards compatibility
        iq['from'] = kwargs.get('ifrom', kwargs.get('dfrom', ''))
        iq['to'] = jid
        iq['type'] = 'get'
        iq['disco_items']['node'] = node if node else ''
        if kwargs.get('iterator', False) and self.xmpp['xep_0059']:
            raise NotImplementedError("XEP 0059 has not yet been fixed")
            return self.xmpp['xep_0059'].iterate(iq, 'disco_items')
        else:
            return iq.send(timeout=kwargs.get('timeout', None),
                           callback=kwargs.get('callback', None),
                           timeout_callback=kwargs.get('timeout_callback', None))

    def set_items(self, jid=None, node=None, **kwargs):
        """
        Set or replace all items for the specified JID/node combination.

        The given items must be in a list or set where each item is a
        tuple of the form: (jid, node, name).

        :param jid: The JID to modify.
        :param node: Optional node to modify.
        :param items: A series of items in tuple format.
        """
        self.api['set_items'](jid, node, None, kwargs)

    def del_items(self, jid=None, node=None, **kwargs):
        """
        Remove all items from the given JID/node combination.

        Arguments:
        :param jid: The JID to modify.
        :param node: Optional node to modify.
        """
        self.api['del_items'](jid, node, None, kwargs)

    def add_item(self, jid='', name='', node=None, subnode='', ijid=None):
        """
        Add a new item element to the given JID/node combination.

        Each item is required to have a JID, but may also specify
        a node value to reference non-addressable entities.

        :param jid: The JID for the item.
        :param name: Optional name for the item.
        :param node: The node to modify.
        :param subnode: Optional node for the item.
        :param ijid: The JID to modify.
        """
        if not jid:
            jid = self.xmpp.boundjid.full
        kwargs = {'ijid': jid,
                  'name': name,
                  'inode': subnode}
        self.api['add_item'](ijid, node, None, kwargs)

    def del_item(self, jid=None, node=None, **kwargs):
        """
        Remove a single item from the given JID/node combination.

        :param jid: The JID to modify.
        :param node: The node to modify.
        :param ijid: The item's JID.
        :param inode: The item's node.
        """
        self.api['del_item'](jid, node, None, kwargs)

    def add_identity(self, category='', itype='', name='',
                     node=None, jid=None, lang=None):
        """
        Add a new identity to the given JID/node combination.

        Each identity must be unique in terms of all four identity
        components: category, type, name, and language.

        Multiple, identical category/type pairs are allowed only
        if the xml:lang values are different. Likewise, multiple
        category/type/xml:lang pairs are allowed so long as the
        names are different. A category and type is always required.

        :param category: The identity's category.
        :param itype: The identity's type.
        :param name: Optional name for the identity.
        :param lang: Optional two-letter language code.
        :param node: The node to modify.
        :param jid: The JID to modify.
        """
        kwargs = {'category': category,
                  'itype': itype,
                  'name': name,
                  'lang': lang}
        self.api['add_identity'](jid, node, None, kwargs)

    def add_feature(self, feature: str, node: Optional[str] = None,
                    jid: Optional[JID] = None):
        """
        Add a feature to a JID/node combination.

        :param feature: The namespace of the supported feature.
        :param node: The node to modify.
        :param jid: The JID to modify.
        """
        kwargs = {'feature': feature}
        self.api['add_feature'](jid, node, None, kwargs)

    def del_identity(self, jid: Optional[JID] = None, node: Optional[str] = None, **kwargs):
        """
        Remove an identity from the given JID/node combination.

        :param jid: The JID to modify.
        :param node: The node to modify.
        :param category: The identity's category.
        :param itype: The identity's type value.
        :param name: Optional, human readable name for the identity.
        :param lang: Optional, the identity's xml:lang value.
        """
        self.api['del_identity'](jid, node, None, kwargs)

    def del_feature(self, jid=None, node=None, **kwargs):
        """
        Remove a feature from a given JID/node combination.

        :param jid: The JID to modify.
        :param node: The node to modify.
        :param feature: The feature's namespace.
        """
        self.api['del_feature'](jid, node, None, kwargs)

    def set_identities(self, jid=None, node=None, **kwargs):
        """
        Add or replace all identities for the given JID/node combination.

        The identities must be in a set where each identity is a tuple
        of the form: (category, type, lang, name)

        :param jid: The JID to modify.
        :param node: The node to modify.
        :param identities: A set of identities in tuple form.
        :param lang: Optional, xml:lang value.
        """
        self.api['set_identities'](jid, node, None, kwargs)

    def del_identities(self, jid=None, node=None, **kwargs):
        """
        Remove all identities for a JID/node combination.

        If a language is specified, only identities using that
        language will be removed.

        :param jid: The JID to modify.
        :param node: The node to modify.
        :param lang: Optional. If given, only remove identities
                    using this xml:lang value.
        """
        self.api['del_identities'](jid, node, None, kwargs)

    def set_features(self, jid=None, node=None, **kwargs):
        """
        Add or replace the set of supported features
        for a JID/node combination.

        :param jid: The JID to modify.
        :param node: The node to modify.
        :param features: The new set of supported features.
        """
        self.api['set_features'](jid, node, None, kwargs)

    def del_features(self, jid=None, node=None, **kwargs):
        """
        Remove all features from a JID/node combination.

        :param jid: The JID to modify.
        :param node: The node to modify.
        """
        self.api['del_features'](jid, node, None, kwargs)

    def _run_node_handler(self, htype, jid, node=None, ifrom=None, data=None):
        """
        Execute the most specific node handler for the given
        JID/node combination.

        :param htype: The handler type to execute.
        :param jid: The JID requested.
        :param node: The node requested.
        :param data: Optional, custom data to pass to the handler.
        """
        if not data:
            data = {}

        return self.api[htype](jid, node, ifrom, data)

    def _handle_disco_info(self, iq):
        """
        Process an incoming disco#info stanza. If it is a get
        request, find and return the appropriate identities
        and features. If it is an info result, fire the
        disco_info event.

        :param iq: The incoming disco#items stanza.
        """
        if iq['type'] == 'get':
            log.debug("Received disco info query from " + \
                      "<%s> to <%s>.", iq['from'], iq['to'])
            info = self.api['get_info'](iq['to'],
                                        iq['disco_info']['node'],
                                        iq['from'],
                                        iq)
            if isinstance(info, Iq):
                info['id'] = iq['id']
                info.send()
            else:
                node = iq['disco_info']['node']
                iq = iq.reply()
                if info:
                    info = self._fix_default_info(info)
                    info['node'] = node
                    iq.set_payload(info.xml)
                iq.send()
        elif iq['type'] == 'result':
            log.debug("Received disco info result from " + \
                      "<%s> to <%s>.", iq['from'], iq['to'])
            if self.use_cache:
                log.debug("Caching disco info result from " \
                      "<%s> to <%s>.", iq['from'], iq['to'])
                if self.xmpp.is_component:
                    ito = iq['to'].full
                else:
                    ito = None
                self.api['cache_info'](iq['from'],
                                       iq['disco_info']['node'],
                                       ito,
                                       iq)
            self.xmpp.event('disco_info', iq)

    def _handle_disco_items(self, iq):
        """
        Process an incoming disco#items stanza. If it is a get
        request, find and return the appropriate items. If it
        is an items result, fire the disco_items event.

        :param iq: The incoming disco#items stanza.
        """
        if iq['type'] == 'get':
            log.debug("Received disco items query from " + \
                      "<%s> to <%s>.", iq['from'], iq['to'])
            items = self.api['get_items'](iq['to'],
                                          iq['disco_items']['node'],
                                          iq['from'],
                                          iq)
            if isinstance(items, Iq):
                items.send()
            else:
                iq = iq.reply()
                if items:
                    iq.set_payload(items.xml)
                iq.send()
        elif iq['type'] == 'result':
            log.debug("Received disco items result from " + \
                      "%s to %s.", iq['from'], iq['to'])
            self.xmpp.event('disco_items', iq)

    def _fix_default_info(self, info):
        """
        Disco#info results for a JID are required to include at least
        one identity and feature. As a default, if no other identity is
        provided, Slixmpp will use either the generic component or the
        bot client identity. A the standard disco#info feature will also be
        added if no features are provided.

        :param info: The disco#info quest (not the full Iq stanza) to modify.
        """
        result = info
        if isinstance(info, Iq):
            info = info['disco_info']
        if not info['node']:
            if not info['identities']:
                if self.xmpp.is_component:
                    log.debug("No identity found for this entity. " + \
                              "Using default component identity.")
                    info.add_identity('component', 'generic')
                else:
                    log.debug("No identity found for this entity. " + \
                              "Using default client identity.")
                    info.add_identity('client', 'bot')
            if not info['features']:
                log.debug("No features found for this entity. " + \
                          "Using default disco#info feature.")
                info.add_feature(info.namespace)
        return result

    def _wrap(self, ito, ifrom, payload, force=False):
        """
        Ensure that results are wrapped in an Iq stanza
        if self.wrap_results has been set to True.

        :param ito: The JID to use as the 'to' value
        :param ifrom: The JID to use as the 'from' value
        :param payload: The disco data to wrap
        :param force: Force wrapping, regardless of self.wrap_results
        """
        if (force or self.wrap_results) and not isinstance(payload, Iq):
            iq = self.xmpp.Iq()
            # Since we're simulating a result, we have to treat
            # the 'from' and 'to' values opposite the normal way.
            iq['to'] = self.xmpp.boundjid if ito is None else ito
            iq['from'] = self.xmpp.boundjid if ifrom is None else ifrom
            iq['type'] = 'result'
            iq.append(payload)
            return iq
        return payload
