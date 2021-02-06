# Slixmpp: The Slick XMPP Library
# Copyright © 2021 Mathieu Pasquet <mathieui@mathieui.net>
# This file is part of Slixmpp.
# See the file LICENSE for copying permission.

"""
This file contains boilerplate to define types relevant to slixmpp.
"""

from typing import Optional

try:
    from typing import (
        Literal,
        TypedDict,
    )
except ImportError:
    from typing_extensions import (
        Literal,
        TypedDict,
    )

from slixmpp.jid import JID

PresenceTypes = Literal[
    'error', 'probe', 'subscribe', 'subscribed',
    'unavailable', 'unsubscribe', 'unsubscribed',
]

PresenceShows = Literal[
    'away', 'chat', 'dnd', 'xa',
]


MessageTypes = Literal[
    'chat', 'error', 'groupchat',
    'headline', 'normal',
]

IqTypes = Literal[
    "error", "get", "set", "result",
]

MucRole = Literal[
    'moderator', 'participant', 'visitor', 'none'
]

MucAffiliation = Literal[
    'outcast', 'member', 'admin', 'owner', 'none'
]


class PresenceArgs(TypedDict, total=False):
    pfrom: JID
    pto: JID
    pshow: PresenceShows
    ptype: PresenceTypes
    pstatus: str


class MucRoomItem(TypedDict, total=False):
    jid: JID
    role: MucRole
    affiliation: MucAffiliation
    show: Optional[PresenceShows]
    status: str
    alt_nick: str


MucRoomItemKeys = Literal[
    'jid', 'role', 'affiliation', 'show', 'status',  'alt_nick',
]
