
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2011  Nathanael C. Fritz
# This file is part of Slixmpp.
# See the file LICENSE for copying permission.
from slixmpp.xmlstream import StanzaBase, ElementBase
from typing import Set, ClassVar


class STARTTLS(StanzaBase):
    """

    .. code-block:: xml

         <starttls xmlns='urn:ietf:params:xml:ns:xmpp-tls'/>

    """
    name = 'starttls'
    namespace = 'urn:ietf:params:xml:ns:xmpp-tls'
    interfaces = {'required'}
    plugin_attrib = name

    def get_required(self):
        return True


class Proceed(StanzaBase):
    """

    .. code-block:: xml

        <proceed xmlns='urn:ietf:params:xml:ns:xmpp-tls'/>

    """
    name = 'proceed'
    namespace = 'urn:ietf:params:xml:ns:xmpp-tls'
    interfaces: ClassVar[Set[str]] = set()


class Failure(StanzaBase):
    """

    .. code-block:: xml

        <failure xmlns='urn:ietf:params:xml:ns:xmpp-tls'/>

    """
    name = 'failure'
    namespace = 'urn:ietf:params:xml:ns:xmpp-tls'
    interfaces: ClassVar[Set[str]] = set()
