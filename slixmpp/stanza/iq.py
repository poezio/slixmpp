"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.stanza.rootstanza import RootStanza
from slixmpp.xmlstream import StanzaBase, ET
from slixmpp.xmlstream.handler import Waiter, Callback, CoroutineCallback
from slixmpp.xmlstream.asyncio import asyncio
from slixmpp.xmlstream.matcher import MatchIDSender, MatcherId
from slixmpp.exceptions import IqTimeout, IqError


class Iq(RootStanza):

    """
    XMPP <iq> stanzas, or info/query stanzas, are XMPP's method of
    requesting and modifying information, similar to HTTP's GET and
    POST methods.

    Each <iq> stanza must have an 'id' value which associates the
    stanza with the response stanza. XMPP entities must always
    be given a response <iq> stanza with a type of 'result' after
    sending a stanza of type 'get' or 'set'.

    Most uses cases for <iq> stanzas will involve adding a <query>
    element whose namespace indicates the type of information
    desired. However, some custom XMPP applications use <iq> stanzas
    as a carrier stanza for an application-specific protocol instead.

    Example <iq> Stanzas:

    .. code-block:: xml

        <iq to="user@example.com" type="get" id="314">
          <query xmlns="http://jabber.org/protocol/disco#items" />
        </iq>

        <iq to="user@localhost" type="result" id="17">
          <query xmlns='jabber:iq:roster'>
            <item jid='otheruser@example.net'
                  name='John Doe'
                  subscription='both'>
              <group>Friends</group>
            </item>
          </query>
        </iq>

    Stanza Interface:
        - **query**: The namespace of the <query> element if one exists.
    Attributes:
        - **types**: May be one of: get, set, result, or error.
    """

    namespace = 'jabber:client'
    name = 'iq'
    interfaces = set(('type', 'to', 'from', 'id', 'query'))
    types = set(('get', 'result', 'set', 'error'))
    plugin_attrib = name

    def __init__(self, *args, **kwargs):
        """
        Initialize a new <iq> stanza with an 'id' value.

        Overrides StanzaBase.__init__.
        """
        StanzaBase.__init__(self, *args, **kwargs)
        if self['id'] == '':
            if self.stream is not None:
                self['id'] = self.stream.new_id()
            else:
                self['id'] = '0'

    def unhandled(self):
        """
        Send a feature-not-implemented error if the stanza is not handled.

        Overrides StanzaBase.unhandled.
        """
        if self['type'] in ('get', 'set'):
            reply = self.reply()
            reply['error']['condition'] = 'feature-not-implemented'
            reply['error']['text'] = 'No handlers registered for this request.'
            reply.send()

    def set_payload(self, value):
        """
        Set the XML contents of the <iq> stanza.

        :param value: An XML object or a list of XML objects to use as the <iq>
                      stanza's contents
        :type value: list or XML object
        """
        self.clear()
        StanzaBase.set_payload(self, value)
        return self

    def set_query(self, value):
        """
        Add or modify a <query> element.

        Query elements are differentiated by their namespace.

        :param str value: The namespace of the <query> element.
        """
        query = self.xml.find("{%s}query" % value)
        if query is None and value:
            plugin = self.plugin_tag_map.get('{%s}query' % value, None)
            if plugin:
                self.enable(plugin.plugin_attrib)
            else:
                self.clear()
                query = ET.Element("{%s}query" % value)
                self.xml.append(query)
        return self

    def get_query(self):
        """Return the namespace of the <query> element.

        :rtype: str"""
        for child in self.xml:
            if child.tag.endswith('query'):
                ns = child.tag.split('}')[0]
                if '{' in ns:
                    ns = ns[1:]
                return ns
        return ''

    def del_query(self):
        """Remove the <query> element."""
        for child in self.xml:
            if child.tag.endswith('query'):
                self.xml.remove(child)
        return self

    def reply(self, clear=True):
        """
        Create a new <iq> stanza replying to ``self``.

        Overrides StanzaBase.reply

        Sets the 'type' to 'result' in addition to the default
        StanzaBase.reply behavior.

        :param bool clear: Indicates if existing content should be
                           removed before replying. Defaults to True.
        """
        new_iq = StanzaBase.reply(self, clear=clear)
        new_iq['type'] = 'result'
        return new_iq

    def send(self, callback=None, timeout=None, timeout_callback=None):
        """Send an <iq> stanza over the XML stream.

        A callback handler can be provided that will be executed when the Iq
        stanza's result reply is received.

        Returns a future which result will be set to the result Iq if it is of type 'get' or 'set'
        (when it is received), or a future with the result set to None if it has another type.

        Overrides StanzaBase.send

        :param function callback: Optional reference to a stream handler
                                  function. Will be executed when a reply
                                  stanza is received.
        :param int timeout: The length of time (in seconds) to wait for a
                            response before the timeout_callback is called,
                            instead of the regular callback
        :param function timeout_callback: Optional reference to a stream handler
                                          function.  Will be executed when the
                                          timeout expires before a response has
                                          been received for the originally-sent
                                          IQ stanza.
        :rtype: asyncio.Future
        """
        if self.stream.session_bind_event.is_set():
            matcher = MatchIDSender({
                'id': self['id'],
                'self': self.stream.boundjid,
                'peer': self['to']
            })
        else:
            matcher = MatcherId(self['id'])

        future = asyncio.Future()

        def callback_success(result):
            if result['type'] == 'error':
                future.set_exception(IqError(result))
            else:
                future.set_result(result)

            if timeout is not None:
                self.stream.cancel_schedule('IqTimeout_%s' % self['id'])
            if callback is not None:
                callback(result)

        def callback_timeout():
            future.set_exception(IqTimeout(self))
            self.stream.remove_handler('IqCallback_%s' % self['id'])
            if timeout_callback is not None:
                timeout_callback(self)

        if self['type'] in ('get', 'set'):
            handler_name = 'IqCallback_%s' % self['id']
            if asyncio.iscoroutinefunction(callback):
                constr = CoroutineCallback
            else:
                constr = Callback
            if timeout is not None:
                self.stream.schedule('IqTimeout_%s' % self['id'],
                                     timeout,
                                     callback_timeout,
                                     repeat=False)
            handler = constr(handler_name,
                             matcher,
                             callback_success,
                             once=True)
            self.stream.register_handler(handler)
        else:
            future.set_result(None)
        StanzaBase.send(self)
        return future

    def _handle_result(self, iq):
        # we got the IQ, so don't fire the timeout
        self.stream.cancel_schedule('IqTimeout_%s' % self['id'])
        self.callback(iq)

    def _fire_timeout(self):
        # don't fire the handler for the IQ, if it finally does come in
        self.stream.remove_handler('IqCallback_%s' % self['id'])
        self.timeout_callback(self)

    def _set_stanza_values(self, values):
        """
        Set multiple stanza interface values using a dictionary.

        Stanza plugin values may be set usind nested dictionaries.

        If the interface 'query' is given, then it will be set
        last to avoid duplication of the <query /> element.

        Overrides ElementBase._set_stanza_values.

        Arguments:
            values -- A dictionary mapping stanza interface with values.
                      Plugin interfaces may accept a nested dictionary that
                      will be used recursively.
        """
        query = values.get('query', '')
        if query:
            del values['query']
            StanzaBase._set_stanza_values(self, values)
            self['query'] = query
        else:
            StanzaBase._set_stanza_values(self, values)
        return self
