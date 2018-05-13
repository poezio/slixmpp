"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Maxime “pep” Buquet <pep@bouah.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.plugins.base import register_plugin

from slixmpp.plugins.xep_0384.plugin import XEP_0384
from slixmpp.plugins.xep_0384 import stanza


register_plugin(XEP_0384)
