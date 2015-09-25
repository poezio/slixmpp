"""
    slixmpp.xmlstream.xmlstream
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides the module for creating and
    interacting with generic XML streams, along with
    the necessary eventing infrastructure.

    Part of Slixmpp: The Slick XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

import functools
import logging
import socket as Socket
import ssl
import weakref
import uuid

import xml.etree.ElementTree

from slixmpp.xmlstream.asyncio import asyncio
from slixmpp.xmlstream import tostring, highlight
from slixmpp.xmlstream.stanzabase import StanzaBase, ElementBase
from slixmpp.xmlstream.resolver import resolve, default_resolver

#: The time in seconds to wait before timing out waiting for response stanzas.
RESPONSE_TIMEOUT = 30

log = logging.getLogger(__name__)

class NotConnectedError(Exception):
    """
    Raised when we try to send something over the wire but we are not
    connected.
    """

class XMLStream(asyncio.BaseProtocol):
    """
    An XML stream connection manager and event dispatcher.

    The XMLStream class abstracts away the issues of establishing a
    connection with a server and sending and receiving XML "stanzas".
    A stanza is a complete XML element that is a direct child of a root
    document element. Two streams are used, one for each communication
    direction, over the same socket. Once the connection is closed, both
    streams should be complete and valid XML documents.

    Three types of events are provided to manage the stream:
        :Stream: Triggered based on received stanzas, similar in concept
                 to events in a SAX XML parser.
        :Custom: Triggered manually.
        :Scheduled: Triggered based on time delays.

    Typically, stanzas are first processed by a stream event handler which
    will then trigger custom events to continue further processing,
    especially since custom event handlers may run in individual threads.

    :param socket: Use an existing socket for the stream. Defaults to
                   ``None`` to generate a new socket.
    :param string host: The name of the target server.
    :param int port: The port to use for the connection. Defaults to 0.
    """

    def __init__(self, socket=None, host='', port=0):
        # The asyncio.Transport object provided by the connection_made()
        # callback when we are connected
        self.transport = None

        # The socket the is used internally by the transport object
        self.socket = None

        self.connect_loop_wait = 0

        self.parser = None
        self.xml_depth = 0
        self.xml_root = None

        self.force_starttls = None
        self.disable_starttls = None

        # A dict of {name: handle}
        self.scheduled_events = {}

        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        # The event to trigger when the create_connection() succeeds. It can
        # be "connected" or "tls_success" depending on the step we are at.
        self.event_when_connected = "connected"

        #: The list of accepted ciphers, in OpenSSL Format.
        #: It might be useful to override it for improved security
        #: over the python defaults.
        self.ciphers = None

        #: Path to a file containing certificates for verifying the
        #: server SSL certificate. A non-``None`` value will trigger
        #: certificate checking.
        #:
        #: .. note::
        #:
        #:     On Mac OS X, certificates in the system keyring will
        #:     be consulted, even if they are not in the provided file.
        self.ca_certs = None

        #: Path to a file containing a client certificate to use for
        #: authenticating via SASL EXTERNAL. If set, there must also
        #: be a corresponding `:attr:keyfile` value.
        self.certfile = None

        #: Path to a file containing the private key for the selected
        #: client certificate to use for authenticating via SASL EXTERNAL.
        self.keyfile = None

        self._der_cert = None

        # The asyncio event loop
        self._loop = None

        #: The default port to return when querying DNS records.
        self.default_port = int(port)

        #: The domain to try when querying DNS records.
        self.default_domain = ''

        #: The expected name of the server, for validation.
        self._expected_server_name = ''
        self._service_name = ''

        #: The desired, or actual, address of the connected server.
        self.address = (host, int(port))

        #: Enable connecting to the server directly over SSL, in
        #: particular when the service provides two ports: one for
        #: non-SSL traffic and another for SSL traffic.
        self.use_ssl = False

        #: If set to ``True``, attempt to connect through an HTTP
        #: proxy based on the settings in :attr:`proxy_config`.
        self.use_proxy = False

        #: If set to ``True``, attempt to use IPv6.
        self.use_ipv6 = True

        #: If set to ``True``, allow using the ``dnspython`` DNS library
        #: if available. If set to ``False``, the builtin DNS resolver
        #: will be used, even if ``dnspython`` is installed.
        self.use_aiodns = True

        #: Use CDATA for escaping instead of XML entities. Defaults
        #: to ``False``.
        self.use_cdata = False

        #: An optional dictionary of proxy settings. It may provide:
        #: :host: The host offering proxy services.
        #: :port: The port for the proxy service.
        #: :username: Optional username for accessing the proxy.
        #: :password: Optional password for accessing the proxy.
        self.proxy_config = {}

        #: The default namespace of the stream content, not of the
        #: stream wrapper itself.
        self.default_ns = ''

        self.default_lang = None
        self.peer_default_lang = None

        #: The namespace of the enveloping stream element.
        self.stream_ns = ''

        #: The default opening tag for the stream element.
        self.stream_header = "<stream>"

        #: The default closing tag for the stream element.
        self.stream_footer = "</stream>"

        #: If ``True``, periodically send a whitespace character over the
        #: wire to keep the connection alive. Mainly useful for connections
        #: traversing NAT.
        self.whitespace_keepalive = True

        #: The default interval between keepalive signals when
        #: :attr:`whitespace_keepalive` is enabled.
        self.whitespace_keepalive_interval = 300

        #: Flag for controlling if the session can be considered ended
        #: if the connection is terminated.
        self.end_session_on_disconnect = True

        #: A mapping of XML namespaces to well-known prefixes.
        self.namespace_map = {StanzaBase.xml_ns: 'xml'}

        self.__root_stanza = []
        self.__handlers = []
        self.__event_handlers = {}
        self.__filters = {'in': [], 'out': [], 'out_sync': []}

        self._id = 0

        #: We use an ID prefix to ensure that all ID values are unique.
        self._id_prefix = '%s-' % uuid.uuid4()

        #: A list of DNS results that have not yet been tried.
        self.dns_answers = None

        #: The service name to check with DNS SRV records. For
        #: example, setting this to ``'xmpp-client'`` would query the
        #: ``_xmpp-client._tcp`` service.
        self.dns_service = None

        #: An asyncio Future being done when the stream is disconnected.
        self.disconnected = asyncio.Future()

        self.add_event_handler('disconnected', self._remove_schedules)
        self.add_event_handler('session_start', self._start_keepalive)

    @property
    def loop(self):
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        return self._loop

    @loop.setter
    def loop(self, value):
        self._loop = value

    def new_id(self):
        """Generate and return a new stream ID in hexadecimal form.

        Many stanzas, handlers, or matchers may require unique
        ID values. Using this method ensures that all new ID values
        are unique in this stream.
        """
        self._id += 1
        return self.get_id()

    def get_id(self):
        """Return the current unique stream ID in hexadecimal form."""
        return "%s%X" % (self._id_prefix, self._id)

    def connect(self, host='', port=0, use_ssl=False,
                force_starttls=True, disable_starttls=False):
        """Create a new socket and connect to the server.

        :param host: The name of the desired server for the connection.
        :param port: Port to connect to on the server.
        :param use_ssl: Flag indicating if SSL should be used by connecting
                        directly to a port using SSL.  If it is False, the
                        connection will be upgraded to SSL/TLS later, using
                        STARTTLS.  Only use this value for old servers that
                        have specific port for SSL/TLS
        TODO fix the comment
        :param force_starttls: If True, the connection will be aborted if
                               the server does not initiate a STARTTLS
                               negociation.  If None, the connection will be
                               upgraded to TLS only if the server initiate
                               the STARTTLS negociation, otherwise it will
                               connect in clear.  If False it will never
                               upgrade to TLS, even if the server provides
                               it.  Use this for example if you’re on
                               localhost

        """
        if host and port:
            self.address = (host, int(port))
        try:
            Socket.inet_aton(self.address[0])
        except (Socket.error, ssl.SSLError):
            self.default_domain = self.address[0]

        # Respect previous TLS usage.
        if use_ssl is not None:
            self.use_ssl = use_ssl
        if force_starttls is not None:
            self.force_starttls = force_starttls
        if disable_starttls is not None:
            self.disable_starttls = disable_starttls

        self.event("connecting")
        asyncio.async(self._connect_routine())

    @asyncio.coroutine
    def _connect_routine(self):
        self.event_when_connected = "connected"

        record = yield from self.pick_dns_answer(self.default_domain)
        if record is not None:
            host, address, port = record
            self.address = (address, port)
            self._service_name = host
        else:
            # No DNS records left, stop iterating
            # and try (host, port) as a last resort
            self.dns_answers = None

        yield from asyncio.sleep(self.connect_loop_wait)
        try:
            yield from self.loop.create_connection(lambda: self,
                                                   self.address[0],
                                                   self.address[1],
                                                   ssl=self.use_ssl)
        except Socket.gaierror as e:
            self.event('connection_failed',
                       'No DNS record available for %s' % self.default_domain)
        except OSError as e:
            log.debug('Connection failed: %s', e)
            self.event("connection_failed", e)
            self.connect_loop_wait = self.connect_loop_wait * 2 + 1
            asyncio.async(self._connect_routine())
        else:
            self.connect_loop_wait = 0

    def process(self, *, forever=True, timeout=None):
        """Process all the available XMPP events (receiving or sending data on the
        socket(s), calling various registered callbacks, calling expired
        timers, handling signal events, etc).  If timeout is None, this
        function will run forever. If timeout is a number, this function
        will return after the given time in seconds.
        """
        if timeout is None:
            if forever:
                self.loop.run_forever()
            else:
                self.loop.run_until_complete(self.disconnected)
        else:
            tasks = [asyncio.sleep(timeout)]
            if not forever:
                tasks.append(self.disconnected)
            self.loop.run_until_complete(asyncio.wait(tasks))

    def init_parser(self):
        """init the XML parser. The parser must always be reset for each new
        connexion
        """
        self.xml_depth = 0
        self.xml_root = None
        self.parser = xml.etree.ElementTree.XMLPullParser(("start", "end"))

    def connection_made(self, transport):
        """Called when the TCP connection has been established with the server
        """
        self.event(self.event_when_connected)
        self.transport = transport
        self.socket = self.transport.get_extra_info("socket")
        self.init_parser()
        self.send_raw(self.stream_header)
        self.dns_answers = None

    def data_received(self, data):
        """Called when incoming data is received on the socket.

        We feed that data to the parser and the see if this produced any XML
        event.  This could trigger one or more event (a stanza is received,
        the stream is opened, etc).
        """
        self.parser.feed(data)
        for event, xml in self.parser.read_events():
            if event == 'start':
                if self.xml_depth == 0:
                    # We have received the start of the root element.
                    self.xml_root = xml
                    log.debug('[33;1mRECV[0m: %s', highlight(tostring(self.xml_root, xmlns=self.default_ns,
                                                         stream=self,
                                                         top_level=True,
                                                         open_only=True)))
                    self.start_stream_handler(self.xml_root)
                self.xml_depth += 1
            if event == 'end':
                self.xml_depth -= 1
                if self.xml_depth == 0:
                    # The stream's root element has closed,
                    # terminating the stream.
                    log.debug("End of stream received")
                    self.abort()
                elif self.xml_depth == 1:
                    # A stanza is an XML element that is a direct child of
                    # the root element, hence the check of depth == 1
                    self.loop.idle_call(functools.partial(self.__spawn_event, xml))
                    if self.xml_root is not None:
                        # Keep the root element empty of children to
                        # save on memory use.
                        self.xml_root.clear()

    def is_connected(self):
        return self.transport is not None

    def eof_received(self):
        """When the TCP connection is properly closed by the remote end
        """
        self.event("eof_received")

    def connection_lost(self, exception):
        """On any kind of disconnection, initiated by us or not.  This signals the
        closure of the TCP connection
        """
        log.info("connection_lost: %s", (exception,))
        self.event("disconnected")
        if self.end_session_on_disconnect:
            self.event('session_end')
        # All these objects are associated with one TCP connection.  Since
        # we are not connected anymore, destroy them
        self.parser = None
        self.transport = None
        self.socket = None

    def disconnect(self, wait=2.0):
        """Close the XML stream and wait for an acknowldgement from the server for
        at most `wait` seconds.  After the given number of seconds has
        passed without a response from the serveur, or when the server
        successfuly responds with a closure of its own stream, abort() is
        called. If wait is 0.0, this is almost equivalent to calling abort()
        directly.

        Does nothing if we are not connected.

        :param wait: Time to wait for a response from the server.

        """
        if self.transport:
            self.send_raw(self.stream_footer)
            self.schedule('Disconnect wait', wait,
                          self.abort, repeat=False)

    def abort(self):
        """
        Forcibly close the connection
        """
        if self.transport:
            self.transport.close()
            self.transport.abort()
            self.event("killed")
            self.disconnected.set_result(True)
            self.disconnected = asyncio.Future()

    def reconnect(self, wait=2.0):
        """Calls disconnect(), and once we are disconnected (after the timeout, or
        when the server acknowledgement is received), call connect()
        """
        log.debug("reconnecting...")
        self.disconnect(wait)
        self.add_event_handler('disconnected', self.connect, disposable=True)

    def configure_socket(self):
        """Set timeout and other options for self.socket.

        Meant to be overridden.
        """
        pass

    def configure_dns(self, resolver, domain=None, port=None):
        """
        Configure and set options for a :class:`~dns.resolver.Resolver`
        instance, and other DNS related tasks. For example, you
        can also check :meth:`~socket.socket.getaddrinfo` to see
        if you need to call out to ``libresolv.so.2`` to
        run ``res_init()``.

        Meant to be overridden.

        :param resolver: A :class:`~dns.resolver.Resolver` instance
                         or ``None`` if ``dnspython`` is not installed.
        :param domain: The initial domain under consideration.
        :param port: The initial port under consideration.
        """
        pass

    def start_tls(self):
        """Perform handshakes for TLS.

        If the handshake is successful, the XML stream will need
        to be restarted.
        """
        self.event_when_connected = "tls_success"

        if self.ciphers is not None:
            self.ssl_context.set_ciphers(self.ciphers)
        if self.keyfile and self.certfile:
            try:
                self.ssl_context.load_cert_chain(self.certfile, self.keyfile)
            except (ssl.SSLError, OSError):
                log.debug('Error loading the cert chain:', exc_info=True)
            else:
                log.debug('Loaded cert file %s and key file %s',
                          self.certfile, self.keyfile)
        if self.ca_certs is not None:
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            self.ssl_context.load_verify_locations(cafile=self.ca_certs)

        ssl_connect_routine = self.loop.create_connection(lambda: self, ssl=self.ssl_context,
                                                          sock=self.socket,
                                                          server_hostname=self.default_domain)
        @asyncio.coroutine
        def ssl_coro():
            try:
                transp, prot = yield from ssl_connect_routine
            except ssl.SSLError as e:
                log.debug('SSL: Unable to connect', exc_info=True)
                log.error('CERT: Invalid certificate trust chain.')
                if not self.event_handled('ssl_invalid_chain'):
                    self.disconnect()
                else:
                    self.event('ssl_invalid_chain', e)
            else:
                der_cert = transp.get_extra_info("socket").getpeercert(True)
                pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)
                self.event('ssl_cert', pem_cert)

        asyncio.async(ssl_coro())

    def _start_keepalive(self, event):
        """Begin sending whitespace periodically to keep the connection alive.

        May be disabled by setting::

            self.whitespace_keepalive = False

        The keepalive interval can be set using::

            self.whitespace_keepalive_interval = 300
        """
        self.schedule('Whitespace Keepalive',
                      self.whitespace_keepalive_interval,
                      self.send_raw,
                      args=(' ',),
                      repeat=True)

    def _remove_schedules(self, event):
        """Remove some schedules that become pointless when disconnected"""
        self.cancel_schedule('Whitespace Keepalive')
        self.cancel_schedule('Disconnect wait')

    def start_stream_handler(self, xml):
        """Perform any initialization actions, such as handshakes,
        once the stream header has been sent.

        Meant to be overridden.
        """
        pass

    def register_stanza(self, stanza_class):
        """Add a stanza object class as a known root stanza.

        A root stanza is one that appears as a direct child of the stream's
        root element.

        Stanzas that appear as substanzas of a root stanza do not need to
        be registered here. That is done using register_stanza_plugin() from
        slixmpp.xmlstream.stanzabase.

        Stanzas that are not registered will not be converted into
        stanza objects, but may still be processed using handlers and
        matchers.

        :param stanza_class: The top-level stanza object's class.
        """
        self.__root_stanza.append(stanza_class)

    def remove_stanza(self, stanza_class):
        """Remove a stanza from being a known root stanza.

        A root stanza is one that appears as a direct child of the stream's
        root element.

        Stanzas that are not registered will not be converted into
        stanza objects, but may still be processed using handlers and
        matchers.
        """
        self.__root_stanza.remove(stanza_class)

    def add_filter(self, mode, handler, order=None):
        """Add a filter for incoming or outgoing stanzas.

        These filters are applied before incoming stanzas are
        passed to any handlers, and before outgoing stanzas
        are put in the send queue.

        Each filter must accept a single stanza, and return
        either a stanza or ``None``. If the filter returns
        ``None``, then the stanza will be dropped from being
        processed for events or from being sent.

        :param mode: One of ``'in'`` or ``'out'``.
        :param handler: The filter function.
        :param int order: The position to insert the filter in
                          the list of active filters.
        """
        if order:
            self.__filters[mode].insert(order, handler)
        else:
            self.__filters[mode].append(handler)

    def del_filter(self, mode, handler):
        """Remove an incoming or outgoing filter."""
        self.__filters[mode].remove(handler)

    def register_handler(self, handler, before=None, after=None):
        """Add a stream event handler that will be executed when a matching
        stanza is received.

        :param handler:
                The :class:`~slixmpp.xmlstream.handler.base.BaseHandler`
                derived object to execute.
        """
        if handler.stream is None:
            self.__handlers.append(handler)
            handler.stream = weakref.ref(self)

    def remove_handler(self, name):
        """Remove any stream event handlers with the given name.

        :param name: The name of the handler.
        """
        idx = 0
        for handler in self.__handlers:
            if handler.name == name:
                self.__handlers.pop(idx)
                return True
            idx += 1
        return False

    @asyncio.coroutine
    def get_dns_records(self, domain, port=None):
        """Get the DNS records for a domain.

        :param domain: The domain in question.
        :param port: If the results don't include a port, use this one.
        """
        if port is None:
            port = self.default_port

        resolver = default_resolver(loop=self.loop)
        self.configure_dns(resolver, domain=domain, port=port)

        result = yield from resolve(domain, port,
                                    service=self.dns_service,
                                    resolver=resolver,
                                    use_ipv6=self.use_ipv6,
                                    use_aiodns=self.use_aiodns,
                                    loop=self.loop)
        return result

    @asyncio.coroutine
    def pick_dns_answer(self, domain, port=None):
        """Pick a server and port from DNS answers.

        Gets DNS answers if none available.
        Removes used answer from available answers.

        :param domain: The domain in question.
        :param port: If the results don't include a port, use this one.
        """
        if self.dns_answers is None:
            dns_records = yield from self.get_dns_records(domain, port)
            self.dns_answers = iter(dns_records)

        try:
            return next(self.dns_answers)
        except StopIteration:
            return

    def add_event_handler(self, name, pointer, disposable=False):
        """Add a custom event handler that will be executed whenever
        its event is manually triggered.

        :param name: The name of the event that will trigger
                     this handler.
        :param pointer: The function to execute.
        :param disposable: If set to ``True``, the handler will be
                           discarded after one use. Defaults to ``False``.
        """
        if not name in self.__event_handlers:
            self.__event_handlers[name] = []
        self.__event_handlers[name].append((pointer, disposable))

    def del_event_handler(self, name, pointer):
        """Remove a function as a handler for an event.

        :param name: The name of the event.
        :param pointer: The function to remove as a handler.
        """
        if not name in self.__event_handlers:
            return

        # Need to keep handlers that do not use
        # the given function pointer
        def filter_pointers(handler):
            return handler[0] != pointer

        self.__event_handlers[name] = list(filter(
            filter_pointers,
            self.__event_handlers[name]))

    def event_handled(self, name):
        """Returns the number of registered handlers for an event.

        :param name: The name of the event to check.
        """
        return len(self.__event_handlers.get(name, []))

    def event(self, name, data={}):
        """Manually trigger a custom event.

        :param name: The name of the event to trigger.
        :param data: Data that will be passed to each event handler.
                     Defaults to an empty dictionary, but is usually
                     a stanza object.
        """
        log.debug("Event triggered: %s", name)

        handlers = self.__event_handlers.get(name, [])
        for handler in handlers:
            handler_callback, disposable = handler
            old_exception = getattr(data, 'exception', None)

            # If the callback is a coroutine, schedule it instead of
            # running it directly
            if asyncio.iscoroutinefunction(handler_callback):
                @asyncio.coroutine
                def handler_callback_routine(cb):
                    try:
                        yield from cb(data)
                    except Exception as e:
                        if old_exception:
                            old_exception(e)
                        else:
                            self.exception(e)
                asyncio.async(handler_callback_routine(handler_callback))
            else:
                try:
                    handler_callback(data)
                except Exception as e:
                    if old_exception:
                        old_exception(e)
                    else:
                        self.exception(e)
            if disposable:
                # If the handler is disposable, we will go ahead and
                # remove it now instead of waiting for it to be
                # processed in the queue.
                try:
                    self.__event_handlers[name].remove(handler)
                except ValueError:
                    pass

    def schedule(self, name, seconds, callback, args=tuple(),
                 kwargs={}, repeat=False):
        """Schedule a callback function to execute after a given delay.

        :param name: A unique name for the scheduled callback.
        :param seconds: The time in seconds to wait before executing.
        :param callback: A pointer to the function to execute.
        :param args: A tuple of arguments to pass to the function.
        :param kwargs: A dictionary of keyword arguments to pass to
                       the function.
        :param repeat: Flag indicating if the scheduled event should
                       be reset and repeat after executing.
        """
        if seconds is None:
            seconds = RESPONSE_TIMEOUT
        cb = functools.partial(callback, *args, **kwargs)
        if repeat:
            handle = self.loop.call_later(seconds, self._execute_and_reschedule,
                                          name, cb, seconds)
        else:
            handle = self.loop.call_later(seconds, self._execute_and_unschedule,
                                          name, cb)

        # Save that handle, so we can just cancel this scheduled event by
        # canceling scheduled_events[name]
        self.scheduled_events[name] = handle

    def cancel_schedule(self, name):
        try:
            handle = self.scheduled_events.pop(name)
            handle.cancel()
        except KeyError:
            log.debug("Tried to cancel unscheduled event: %s" % (name,))

    def _safe_cb_run(self, name, cb):
        log.debug('Scheduled event: %s', name)
        try:
            cb()
        except Exception as e:
            self.exception(e)

    def _execute_and_reschedule(self, name, cb, seconds):
        """Simple method that calls the given callback, and then schedule itself to
        be called after the given number of seconds.
        """
        self._safe_cb_run(name, cb)
        handle = self.loop.call_later(seconds, self._execute_and_reschedule,
                                      name, cb, seconds)
        self.scheduled_events[name] = handle

    def _execute_and_unschedule(self, name, cb):
        """
        Execute the callback and remove the handler for it.
        """
        self._safe_cb_run(name, cb)
        del self.scheduled_events[name]

    def incoming_filter(self, xml):
        """Filter incoming XML objects before they are processed.

        Possible uses include remapping namespaces, or correcting elements
        from sources with incorrect behavior.

        Meant to be overridden.
        """
        return xml

    def send(self, data, use_filters=True):
        """A wrapper for :meth:`send_raw()` for sending stanza objects.

        May optionally block until an expected response is received.

        :param data: The :class:`~slixmpp.xmlstream.stanzabase.ElementBase`
                     stanza to send on the stream.
        :param bool use_filters: Indicates if outgoing filters should be
                                 applied to the given stanza data. Disabling
                                 filters is useful when resending stanzas.
                                 Defaults to ``True``.
        """
        if isinstance(data, ElementBase):
            if use_filters:
                for filter in self.__filters['out']:
                    data = filter(data)
                    if data is None:
                        return

        if isinstance(data, ElementBase):
            if use_filters:
                for filter in self.__filters['out_sync']:
                    data = filter(data)
                    if data is None:
                        return
            str_data = tostring(data.xml, xmlns=self.default_ns,
                                          stream=self,
                                          top_level=True)
            self.send_raw(str_data)
        else:
            self.send_raw(data)

    def send_xml(self, data):
        """Send an XML object on the stream

        :param data: The :class:`~xml.etree.ElementTree.Element` XML object
                     to send on the stream.
        """
        return self.send(tostring(data))

    def send_raw(self, data):
        """Send raw data across the stream.

        :param string data: Any bytes or utf-8 string value.
        """
        log.debug("[36;1mSEND[0m: %s", highlight(data))
        if not self.transport:
            raise NotConnectedError()
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.transport.write(data)

    def _build_stanza(self, xml, default_ns=None):
        """Create a stanza object from a given XML object.

        If a specialized stanza type is not found for the XML, then
        a generic :class:`~slixmpp.xmlstream.stanzabase.StanzaBase`
        stanza will be returned.

        :param xml: The :class:`~xml.etree.ElementTree.Element` XML object
                    to convert into a stanza object.
        :param default_ns: Optional default namespace to use instead of the
                           stream's current default namespace.
        """
        if default_ns is None:
            default_ns = self.default_ns
        stanza_type = StanzaBase
        for stanza_class in self.__root_stanza:
            if xml.tag == "{%s}%s" % (default_ns, stanza_class.name) or \
               xml.tag == stanza_class.tag_name():
                stanza_type = stanza_class
                break
        stanza = stanza_type(self, xml)
        if stanza['lang'] is None and self.peer_default_lang:
            stanza['lang'] = self.peer_default_lang
        return stanza

    def __spawn_event(self, xml):
        """
        Analyze incoming XML stanzas and convert them into stanza
        objects if applicable and queue stream events to be processed
        by matching handlers.

        :param xml: The :class:`~slixmpp.xmlstream.stanzabase.ElementBase`
                    stanza to analyze.
        """
        # Apply any preprocessing filters.
        xml = self.incoming_filter(xml)

        # Convert the raw XML object into a stanza object. If no registered
        # stanza type applies, a generic StanzaBase stanza will be used.
        stanza = self._build_stanza(xml)
        for filter in self.__filters['in']:
            if stanza is not None:
                stanza = filter(stanza)
        if stanza is None:
            return

        log.debug("[33;1mRECV[0m: %s", highlight(stanza))

        # Match the stanza against registered handlers. Handlers marked
        # to run "in stream" will be executed immediately; the rest will
        # be queued.
        handled = False
        matched_handlers = [h for h in self.__handlers if h.match(stanza)]
        for handler in matched_handlers:
            handler.prerun(stanza)
            try:
                handler.run(stanza)
            except Exception as e:
                stanza.exception(e)
            if handler.check_delete():
                self.__handlers.remove(handler)
            handled = True

        # Some stanzas require responses, such as Iq queries. A default
        # handler will be executed immediately for this case.
        if not handled:
            stanza.unhandled()

    def exception(self, exception):
        """Process an unknown exception.

        Meant to be overridden.

        :param exception: An unhandled exception object.
        """
        pass

