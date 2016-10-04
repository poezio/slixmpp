# -*- coding: utf-8 -*-
"""
    slixmpp.jid
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module allows for working with Jabber IDs (JIDs).

    Part of Slixmpp: The Slick XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

import re
import socket

from copy import deepcopy
from functools import lru_cache

from slixmpp.stringprep import nodeprep, resourceprep, idna, StringprepError

HAVE_INET_PTON = hasattr(socket, 'inet_pton')

#: The basic regex pattern that a JID must match in order to determine
#: the local, domain, and resource parts. This regex does NOT do any
#: validation, which requires application of nodeprep, resourceprep, etc.
JID_PATTERN = re.compile(
    "^(?:([^\"&'/:<>@]{1,1023})@)?([^/@]{1,1023})(?:/(.{1,1023}))?$"
)

#: The set of escape sequences for the characters not allowed by nodeprep.
JID_ESCAPE_SEQUENCES = {'\\20', '\\22', '\\26', '\\27', '\\2f',
                        '\\3a', '\\3c', '\\3e', '\\40', '\\5c'}

#: The reverse mapping of escape sequences to their original forms.
JID_UNESCAPE_TRANSFORMATIONS = {'\\20': ' ',
                                '\\22': '"',
                                '\\26': '&',
                                '\\27': "'",
                                '\\2f': '/',
                                '\\3a': ':',
                                '\\3c': '<',
                                '\\3e': '>',
                                '\\40': '@',
                                '\\5c': '\\'}


# TODO: Find the best cache size for a standard usage.
@lru_cache(maxsize=1024)
def _parse_jid(data):
    """
    Parse string data into the node, domain, and resource
    components of a JID, if possible.

    :param string data: A string that is potentially a JID.

    :raises InvalidJID:

    :returns: tuple of the validated local, domain, and resource strings
    """
    match = JID_PATTERN.match(data)
    if not match:
        raise InvalidJID('JID could not be parsed')

    (node, domain, resource) = match.groups()

    node = _validate_node(node)
    domain = _validate_domain(domain)
    resource = _validate_resource(resource)

    return node, domain, resource


def _validate_node(node):
    """Validate the local, or username, portion of a JID.

    :raises InvalidJID:

    :returns: The local portion of a JID, as validated by nodeprep.
    """
    if node is None:
        return ''

    try:
        node = nodeprep(node)
    except StringprepError:
        raise InvalidJID('Nodeprep failed')

    if not node:
        raise InvalidJID('Localpart must not be 0 bytes')
    if len(node) > 1023:
        raise InvalidJID('Localpart must be less than 1024 bytes')
    return node


def _validate_domain(domain):
    """Validate the domain portion of a JID.

    IP literal addresses are left as-is, if valid. Domain names
    are stripped of any trailing label separators (`.`), and are
    checked with the nameprep profile of stringprep. If the given
    domain is actually a punyencoded version of a domain name, it
    is converted back into its original Unicode form. Domains must
    also not start or end with a dash (`-`).

    :raises InvalidJID:

    :returns: The validated domain name
    """
    ip_addr = False

    # First, check if this is an IPv4 address
    try:
        socket.inet_aton(domain)
        ip_addr = True
    except socket.error:
        pass

    # Check if this is an IPv6 address
    if not ip_addr and HAVE_INET_PTON and domain[0] == '[' and domain[-1] == ']':
        try:
            ip = domain[1:-1]
            socket.inet_pton(socket.AF_INET6, ip)
            ip_addr = True
        except (socket.error, ValueError):
            pass

    if not ip_addr:
        # This is a domain name, which must be checked further

        if domain and domain[-1] == '.':
            domain = domain[:-1]

        try:
            domain = idna(domain)
        except StringprepError:
            raise InvalidJID('idna validation failed')

        if ':' in domain:
            raise InvalidJID('Domain containing a port')
        for label in domain.split('.'):
            if not label:
                raise InvalidJID('Domain containing too many dots')
            if '-' in (label[0], label[-1]):
                raise InvalidJID('Domain started or ended with -')

    if not domain:
        raise InvalidJID('Domain must not be 0 bytes')
    if len(domain) > 1023:
        raise InvalidJID('Domain must be less than 1024 bytes')

    return domain


def _validate_resource(resource):
    """Validate the resource portion of a JID.

    :raises InvalidJID:

    :returns: The local portion of a JID, as validated by resourceprep.
    """
    if resource is None:
        return ''

    try:
        resource = resourceprep(resource)
    except StringprepError:
        raise InvalidJID('Resourceprep failed')

    if not resource:
        raise InvalidJID('Resource must not be 0 bytes')
    if len(resource) > 1023:
        raise InvalidJID('Resource must be less than 1024 bytes')
    return resource


def _unescape_node(node):
    """Unescape a local portion of a JID.

    .. note::
        The unescaped local portion is meant ONLY for presentation,
        and should not be used for other purposes.
    """
    unescaped = []
    seq = ''
    for i, char in enumerate(node):
        if char == '\\':
            seq = node[i:i+3]
            if seq not in JID_ESCAPE_SEQUENCES:
                seq = ''
        if seq:
            if len(seq) == 3:
                unescaped.append(JID_UNESCAPE_TRANSFORMATIONS.get(seq, char))

            # Pop character off the escape sequence, and ignore it
            seq = seq[1:]
        else:
            unescaped.append(char)
    return ''.join(unescaped)


def _format_jid(local=None, domain=None, resource=None):
    """Format the given JID components into a full or bare JID.

    :param string local: Optional. The local portion of the JID.
    :param string domain: Required. The domain name portion of the JID.
    :param strin resource: Optional. The resource portion of the JID.

    :return: A full or bare JID string.
    """
    if domain is None:
        return ''
    if local is not None:
        result = local + '@' + domain
    else:
        result = domain
    if resource is not None:
        result += '/' + resource
    return result


class InvalidJID(ValueError):
    """
    Raised when attempting to create a JID that does not pass validation.

    It can also be raised if modifying an existing JID in such a way as
    to make it invalid, such trying to remove the domain from an existing
    full JID while the local and resource portions still exist.
    """

# pylint: disable=R0903
class UnescapedJID:

    """
    .. versionadded:: 1.1.10
    """

    __slots__ = ('_node', '_domain', '_resource')

    def __init__(self, node, domain, resource):
        self._node = node
        self._domain = domain
        self._resource = resource

    def __getattribute__(self, name):
        """Retrieve the given JID component.

        :param name: one of: user, server, domain, resource,
                     full, or bare.
        """
        if name == 'resource':
            return self._resource or ''
        if name in ('user', 'username', 'local', 'node'):
            return self._node or ''
        if name in ('server', 'domain', 'host'):
            return self._domain or ''
        if name in ('full', 'jid'):
            return _format_jid(self._node, self._domain, self._resource)
        if name == 'bare':
            return _format_jid(self._node, self._domain)
        return object.__getattribute__(self, name)

    def __str__(self):
        """Use the full JID as the string value."""
        return _format_jid(self._node, self._domain, self._resource)

    def __repr__(self):
        """Use the full JID as the representation."""
        return _format_jid(self._node, self._domain, self._resource)


class JID:

    """
    A representation of a Jabber ID, or JID.

    Each JID may have three components: a user, a domain, and an optional
    resource. For example: user@domain/resource

    When a resource is not used, the JID is called a bare JID.
    The JID is a full JID otherwise.

    **JID Properties:**
        :full: The string value of the full JID.
        :jid: Alias for ``full``.
        :bare: The string value of the bare JID.
        :node: The node portion of the JID.
        :user: Alias for ``node``.
        :local: Alias for ``node``.
        :username: Alias for ``node``.
        :domain: The domain name portion of the JID.
        :server: Alias for ``domain``.
        :host: Alias for ``domain``.
        :resource: The resource portion of the JID.

    :param string jid:
        A string of the form ``'[user@]domain[/resource]'``.

    :raises InvalidJID:
    """

    __slots__ = ('_node', '_domain', '_resource', '_bare', '_full')

    def __init__(self, jid=None):
        if not jid:
            self._node = ''
            self._domain = ''
            self._resource = ''
            self._bare = ''
            self._full = ''
            return
        elif not isinstance(jid, JID):
            self._node, self._domain, self._resource = _parse_jid(jid)
        else:
            self._node = jid._node
            self._domain = jid._domain
            self._resource = jid._resource
        self._update_bare_full()

    def unescape(self):
        """Return an unescaped JID object.

        Using an unescaped JID is preferred for displaying JIDs
        to humans, and they should NOT be used for any other
        purposes than for presentation.

        :return: :class:`UnescapedJID`

        .. versionadded:: 1.1.10
        """
        return UnescapedJID(_unescape_node(self._node),
                            self._domain,
                            self._resource)

    def _update_bare_full(self):
        """Format the given JID into a bare and a full JID.
        """
        self._bare = (self._node + '@' + self._domain
                      if self._node
                      else self._domain)
        self._full = (self._bare + '/' + self._resource
                      if self._resource
                      else self._bare)

    @property
    def node(self):
        return self._node

    @property
    def user(self):
        return self._node

    @property
    def local(self):
        return self._node

    @property
    def username(self):
        return self._node

    @property
    def domain(self):
        return self._domain

    @property
    def server(self):
        return self._domain

    @property
    def host(self):
        return self._domain

    @property
    def resource(self):
        return self._resource

    @property
    def bare(self):
        return self._bare

    @property
    def full(self):
        return self._full

    @property
    def jid(self):
        return self._full

    @node.setter
    def node(self, value):
        self._node = _validate_node(value)
        self._update_bare_full()

    @user.setter
    def user(self, value):
        self._node = _validate_node(value)
        self._update_bare_full()

    @local.setter
    def local(self, value):
        self._node = _validate_node(value)
        self._update_bare_full()

    @username.setter
    def username(self, value):
        self._node = _validate_node(value)
        self._update_bare_full()

    @domain.setter
    def domain(self, value):
        self._domain = _validate_domain(value)
        self._update_bare_full()

    @server.setter
    def server(self, value):
        self._domain = _validate_domain(value)
        self._update_bare_full()

    @host.setter
    def host(self, value):
        self._domain = _validate_domain(value)
        self._update_bare_full()

    @bare.setter
    def bare(self, value):
        node, domain, resource = _parse_jid(value)
        assert not resource
        self._node = node
        self._domain = domain
        self._update_bare_full()

    @resource.setter
    def resource(self, value):
        self._resource = _validate_resource(value)
        self._update_bare_full()

    @full.setter
    def full(self, value):
        self._node, self._domain, self._resource = _parse_jid(value)
        self._update_bare_full()

    @jid.setter
    def jid(self, value):
        self._node, self._domain, self._resource = _parse_jid(value)
        self._update_bare_full()

    def __str__(self):
        """Use the full JID as the string value."""
        return self._full

    def __repr__(self):
        """Use the full JID as the representation."""
        return self._full

    # pylint: disable=W0212
    def __eq__(self, other):
        """Two JIDs are equal if they have the same full JID value."""
        if isinstance(other, UnescapedJID):
            return False
        if not isinstance(other, JID):
            other = JID(other)

        return (self._node == other._node and
                self._domain == other._domain and
                self._resource == other._resource)

    def __ne__(self, other):
        """Two JIDs are considered unequal if they are not equal."""
        return not self == other

    def __hash__(self):
        """Hash a JID based on the string version of its full JID."""
        return hash(self._full)
