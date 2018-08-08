"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

import asyncio
# Required for python < 3.7 to use the old ssl implementation
# and manage to do starttls as an unintended side effect
asyncio.sslproto._is_sslproto_available = lambda: False

from slixmpp.stanza import Message, Presence, Iq
from slixmpp.jid import JID, InvalidJID
from slixmpp.xmlstream.stanzabase import ET, ElementBase, register_stanza_plugin
from slixmpp.xmlstream.handler import *
from slixmpp.xmlstream import XMLStream
from slixmpp.xmlstream.matcher import *
from slixmpp.xmlstream.asyncio import asyncio, future_wrapper
from slixmpp.basexmpp import BaseXMPP
from slixmpp.clientxmpp import ClientXMPP
from slixmpp.componentxmpp import ComponentXMPP

from slixmpp.version import __version__, __version_info__
