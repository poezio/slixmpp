"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2019 Mathieu Pasquet
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""
from slixmpp.plugins.base import register_plugin
from slixmpp.plugins.protoxep_occupantid.occupantid import XEP_OccupantID
from slixmpp.plugins.protoxep_occupantid.stanza import OccupantID

register_plugin(XEP_OccupantID)
