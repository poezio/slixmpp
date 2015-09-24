# -*- encoding: utf-8 -*-

"""
    slixmpp.xmlstream.dns
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

from slixmpp.xmlstream.asyncio import asyncio
import socket
import logging
import random


log = logging.getLogger(__name__)


#: Global flag indicating the availability of the ``aiodns`` package.
#: Installing ``aiodns`` can be done via:
#:
#: .. code-block:: sh
#:
#:     pip install aiodns
AIODNS_AVAILABLE = False
try:
    import aiodns
    AIODNS_AVAILABLE = True
except ImportError as e:
    log.debug("Could not find aiodns package. " + \
              "Not all features will be available")


def default_resolver(loop):
    """Return a basic DNS resolver object.

    :returns: A :class:`aiodns.DNSResolver` object if aiodns
              is available. Otherwise, ``None``.
    """
    if AIODNS_AVAILABLE:
        return aiodns.DNSResolver(loop=loop,
                                  tries=1,
                                  timeout=1.0)
    return None


@asyncio.coroutine
def resolve(host, port=None, service=None, proto='tcp',
            resolver=None, use_ipv6=True, use_aiodns=True, loop=None):
    """Peform DNS resolution for a given hostname.

    Resolution may perform SRV record lookups if a service and protocol
    are specified. The returned addresses will be sorted according to
    the SRV priorities and weights.

    If no resolver is provided, the aiodns resolver will be used if
    available. Otherwise the built-in socket facilities will be used,
    but those do not provide SRV support.

    If SRV records were used, queries to resolve alternative hosts will
    be made as needed instead of all at once.

    :param     host: The hostname to resolve.
    :param     port: A default port to connect with. SRV records may
                     dictate use of a different port.
    :param  service: Optional SRV service name without leading underscore.
    :param    proto: Optional SRV protocol name without leading underscore.
    :param resolver: Optionally provide a DNS resolver object that has
                     been custom configured.
    :param use_ipv6: Optionally control the use of IPv6 in situations
                     where it is either not available, or performance
                     is degraded. Defaults to ``True``.
    :param use_aiodns: Optionally control if aiodns is used to make
                          the DNS queries instead of the built-in DNS
                          library.

    :type     host: string
    :type     port: int
    :type  service: string
    :type    proto: string
    :type resolver: :class:`aiodns.DNSResolver`
    :type use_ipv6: bool
    :type use_aiodns: bool

    :return: An iterable of IP address, port pairs in the order
             dictated by SRV priorities and weights, if applicable.
    """

    if not use_aiodns:
        if AIODNS_AVAILABLE:
            log.debug("DNS: Not using aiodns, but aiodns is installed.")
        else:
            log.debug("DNS: Not using aiodns.")

    if not use_ipv6:
        log.debug("DNS: Use of IPv6 has been disabled.")

    if resolver is None and AIODNS_AVAILABLE and use_aiodns:
        resolver = aiodns.DNSResolver(loop=loop)

    # An IPv6 literal is allowed to be enclosed in square brackets, but
    # the brackets must be stripped in order to process the literal;
    # otherwise, things break.
    host = host.strip('[]')

    try:
        # If `host` is an IPv4 literal, we can return it immediately.
        ipv4 = socket.inet_aton(host)
        return [(host, host, port)]
    except socket.error:
        pass

    if use_ipv6:
        try:
            # Likewise, If `host` is an IPv6 literal, we can return
            # it immediately.
            if hasattr(socket, 'inet_pton'):
                ipv6 = socket.inet_pton(socket.AF_INET6, host)
                return [(host, host, port)]
        except (socket.error, ValueError):
            pass

    # If no service was provided, then we can just do A/AAAA lookups on the
    # provided host. Otherwise we need to get an ordered list of hosts to
    # resolve based on SRV records.
    if not service:
        hosts = [(host, port)]
    else:
        hosts = yield from get_SRV(host, port, service, proto,
                                   resolver=resolver,
                                   use_aiodns=use_aiodns)
        if not hosts:
            hosts = [(host, port)]

    results = []
    for host, port in hosts:
        if host == 'localhost':
            if use_ipv6:
                results.append((host, '::1', port))
            results.append((host, '127.0.0.1', port))

        if use_ipv6:
            aaaa = yield from get_AAAA(host, resolver=resolver,
                                       use_aiodns=use_aiodns, loop=loop)
            for address in aaaa:
                results.append((host, address, port))

        a = yield from get_A(host, resolver=resolver,
                             use_aiodns=use_aiodns, loop=loop)
        for address in a:
            results.append((host, address, port))

    return results

@asyncio.coroutine
def get_A(host, resolver=None, use_aiodns=True, loop=None):
    """Lookup DNS A records for a given host.

    If ``resolver`` is not provided, or is ``None``, then resolution will
    be performed using the built-in :mod:`socket` module.

    :param     host: The hostname to resolve for A record IPv4 addresses.
    :param resolver: Optional DNS resolver object to use for the query.
    :param use_aiodns: Optionally control if aiodns is used to make
                          the DNS queries instead of the built-in DNS
                          library.

    :type     host: string
    :type resolver: :class:`aiodns.DNSResolver` or ``None``
    :type use_aiodns: bool

    :return: A list of IPv4 literals.
    """
    log.debug("DNS: Querying %s for A records." % host)

    # If not using aiodns, attempt lookup using the OS level
    # getaddrinfo() method.
    if resolver is None or not use_aiodns:
        try:
            recs = yield from loop.getaddrinfo(host, None,
                                               family=socket.AF_INET,
                                               type=socket.SOCK_STREAM)
            return [rec[4][0] for rec in recs]
        except socket.gaierror:
            log.debug("DNS: Error retrieving A address info for %s." % host)
            return []

    # Using aiodns:
    future = resolver.query(host, 'A')
    try:
        recs = yield from future
    except Exception as e:
        log.debug('DNS: Exception while querying for %s A records: %s', host, e)
        recs = []
    return [rec.host for rec in recs]


@asyncio.coroutine
def get_AAAA(host, resolver=None, use_aiodns=True, loop=None):
    """Lookup DNS AAAA records for a given host.

    If ``resolver`` is not provided, or is ``None``, then resolution will
    be performed using the built-in :mod:`socket` module.

    :param     host: The hostname to resolve for AAAA record IPv6 addresses.
    :param resolver: Optional DNS resolver object to use for the query.
    :param use_aiodns: Optionally control if aiodns is used to make
                          the DNS queries instead of the built-in DNS
                          library.

    :type     host: string
    :type resolver: :class:`aiodns.DNSResolver` or ``None``
    :type use_aiodns: bool

    :return: A list of IPv6 literals.
    """
    log.debug("DNS: Querying %s for AAAA records." % host)

    # If not using aiodns, attempt lookup using the OS level
    # getaddrinfo() method.
    if resolver is None or not use_aiodns:
        if not socket.has_ipv6:
            log.debug("DNS: Unable to query %s for AAAA records: IPv6 is not supported", host)
            return []
        try:
            recs = yield from loop.getaddrinfo(host, None,
                                               family=socket.AF_INET6,
                                               type=socket.SOCK_STREAM)
            return [rec[4][0] for rec in recs]
        except (OSError, socket.gaierror):
            log.debug("DNS: Error retreiving AAAA address " + \
                      "info for %s." % host)
            return []

    # Using aiodns:
    future = resolver.query(host, 'AAAA')
    try:
        recs = yield from future
    except Exception as e:
        log.debug('DNS: Exception while querying for %s AAAA records: %s', host, e)
        recs = []
    return [rec.host for rec in recs]

@asyncio.coroutine
def get_SRV(host, port, service, proto='tcp', resolver=None, use_aiodns=True):
    """Perform SRV record resolution for a given host.

    .. note::

        This function requires the use of the ``aiodns`` package. Calling
        :func:`get_SRV` without ``aiodns`` will return the provided host
        and port without performing any DNS queries.

    :param     host: The hostname to resolve.
    :param     port: A default port to connect with. SRV records may
                     dictate use of a different port.
    :param  service: Optional SRV service name without leading underscore.
    :param    proto: Optional SRV protocol name without leading underscore.
    :param resolver: Optionally provide a DNS resolver object that has
                     been custom configured.

    :type     host: string
    :type     port: int
    :type  service: string
    :type    proto: string
    :type resolver: :class:`aiodns.DNSResolver`

    :return: A list of hostname, port pairs in the order dictacted
             by SRV priorities and weights.
    """
    if resolver is None or not use_aiodns:
        log.warning("DNS: aiodns not found. Can not use SRV lookup.")
        return [(host, port)]

    log.debug("DNS: Querying SRV records for %s" % host)
    try:
        future = resolver.query('_%s._%s.%s' % (service, proto, host),
                                'SRV')
        recs = yield from future
    except Exception as e:
        log.debug('DNS: Exception while querying for %s SRV records: %s', host, e)
        return []

    answers = {}
    for rec in recs:
        if rec.priority not in answers:
            answers[rec.priority] = []
        if rec.weight == 0:
            answers[rec.priority].insert(0, rec)
        else:
            answers[rec.priority].append(rec)

    sorted_recs = []
    for priority in sorted(answers.keys()):
        while answers[priority]:
            running_sum = 0
            sums = {}
            for rec in answers[priority]:
                running_sum += rec.weight
                sums[running_sum] = rec

            selected = random.randint(0, running_sum + 1)
            for running_sum in sums:
                if running_sum >= selected:
                    rec = sums[running_sum]
                    host = rec.host
                    if host.endswith('.'):
                        host = host[:-1]
                    sorted_recs.append((host, rec.port))
                    answers[priority].remove(rec)
                    break

    return sorted_recs
