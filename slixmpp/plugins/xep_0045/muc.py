"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    Copyright (C) 2020 "Maxime “pep” Buquet <pep@bouah.net>"
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""
from __future__ import with_statement

import logging
from typing import (
    List,
    Tuple,
    Optional,
)

from slixmpp import (
    Presence,
    Message,
    Iq,
    JID,
)
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream import register_stanza_plugin, ET
from slixmpp.xmlstream.handler.callback import Callback
from slixmpp.xmlstream.matcher.xpath import MatchXPath
from slixmpp.xmlstream.matcher.stanzapath import StanzaPath
from slixmpp.xmlstream.matcher.xmlmask import MatchXMLMask
from slixmpp.exceptions import IqError, IqTimeout

from slixmpp.plugins.xep_0045 import stanza
from slixmpp.plugins.xep_0045.stanza import (
    MUCInvite,
    MUCDecline,
    MUCPresence,
    MUCJoin,
    MUCMessage,
    MUCAdminQuery,
    MUCAdminItem,
    MUCHistory,
    MUCOwnerQuery,
    MUCOwnerDestroy,
    MUCStatus,
)


log = logging.getLogger(__name__)

AFFILIATIONS = ('outcast', 'member', 'admin', 'owner', 'none')
ROLES = ('moderator', 'participant', 'visitor', 'none')


class XEP_0045(BasePlugin):

    """
    Implements XEP-0045 Multi-User Chat
    """

    name = 'xep_0045'
    description = 'XEP-0045: Multi-User Chat'
    dependencies = {'xep_0030', 'xep_0004'}
    stanza = stanza

    def plugin_init(self):
        self.rooms = {}
        self.our_nicks = {}
        # load MUC support in presence stanzas
        register_stanza_plugin(MUCMessage, MUCInvite)
        register_stanza_plugin(MUCMessage, MUCDecline)
        register_stanza_plugin(MUCMessage, MUCStatus)
        register_stanza_plugin(MUCPresence, MUCStatus)
        register_stanza_plugin(Presence, MUCPresence)
        register_stanza_plugin(Presence, MUCJoin)
        register_stanza_plugin(MUCJoin, MUCHistory)
        register_stanza_plugin(Message, MUCMessage)
        register_stanza_plugin(Iq, MUCAdminQuery)
        register_stanza_plugin(Iq, MUCOwnerQuery)
        register_stanza_plugin(MUCOwnerQuery, MUCOwnerDestroy)
        register_stanza_plugin(MUCAdminQuery, MUCAdminItem, iterable=True)

        # Register handlers
        self.xmpp.register_handler(
            Callback(
                'MUCPresence',
                MatchXMLMask("<presence xmlns='%s' />" % self.xmpp.default_ns),
                self.handle_groupchat_presence,
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCError',
                MatchXMLMask("<message xmlns='%s' type='error'><error/></message>" % self.xmpp.default_ns),
                self.handle_groupchat_error_message
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCMessage',
                MatchXMLMask("<message xmlns='%s' type='groupchat'><body/></message>" % self.xmpp.default_ns),
                self.handle_groupchat_message
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCSubject',
                MatchXMLMask("<message xmlns='%s' type='groupchat'><subject/></message>" % self.xmpp.default_ns),
                self.handle_groupchat_subject
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCConfig',
                StanzaPath('message/muc/status'),
                self.handle_config_change
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCInvite',
                StanzaPath('message/muc/invite'),
                self.handle_groupchat_invite
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCDecline',
                StanzaPath('message/muc/decline'),
                self.handle_groupchat_decline
        ))

    def plugin_end(self):
        self.xmpp.plugin['xep_0030'].del_feature(feature=stanza.NS)

    def session_bind(self, jid):
        self.xmpp.plugin['xep_0030'].add_feature(stanza.NS)

    def handle_groupchat_invite(self, inv):
        """ Handle an invite into a muc. """
        if inv['from'] not in self.rooms.keys():
            self.xmpp.event("groupchat_invite", inv)

    def handle_groupchat_decline(self, decl):
        """Handle an invitation decline."""
        if decl['from'] in self.room.keys():
            self.xmpp.event('groupchat_decline', decl)

    def handle_config_change(self, msg):
        """Handle a MUC configuration change (with status code)."""
        self.xmpp.event('groupchat_config_status', msg)
        self.xmpp.event('muc::%s::config_status' % msg['from'].bare , msg)

    def handle_groupchat_presence(self, pr):
        """ Handle a presence in a muc.
        """
        got_offline = False
        got_online = False
        if pr['muc']['room'] not in self.rooms.keys():
            return
        self.xmpp.roster[pr['from']].ignore_updates = True
        entry = pr['muc'].get_stanza_values()
        entry['show'] = pr['show'] if pr['show'] in pr.showtypes else None
        entry['status'] = pr['status']
        entry['alt_nick'] = pr['nick']
        if pr['type'] == 'unavailable':
            if entry['nick'] in self.rooms[entry['room']]:
                del self.rooms[entry['room']][entry['nick']]
            got_offline = True
        else:
            if entry['nick'] not in self.rooms[entry['room']]:
                got_online = True
            self.rooms[entry['room']][entry['nick']] = entry
        log.debug("MUC presence from %s/%s : %s", entry['room'],entry['nick'], entry)
        self.xmpp.event("groupchat_presence", pr)
        self.xmpp.event("muc::%s::presence" % entry['room'], pr)
        if got_offline:
            self.xmpp.event("muc::%s::got_offline" % entry['room'], pr)
        if got_online:
            self.xmpp.event("muc::%s::got_online" % entry['room'], pr)

    def handle_groupchat_message(self, msg: Message) -> None:
        """ Handle a message event in a muc.
        """
        self.xmpp.event('groupchat_message', msg)
        self.xmpp.event("muc::%s::message" % msg['from'].bare, msg)

    def handle_groupchat_error_message(self, msg):
        """ Handle a message error event in a muc.
        """
        self.xmpp.event('groupchat_message_error', msg)
        self.xmpp.event("muc::%s::message_error" % msg['from'].bare, msg)


    def handle_groupchat_subject(self, msg: Message) -> None:
        """ Handle a message coming from a muc indicating
        a change of subject (or announcing it when joining the room)
        """
        # See poezio#3452. A message containing subject _and_ (body or thread)
        # is not a subject change.
        if msg['body'] or msg['thread']:
            return None
        self.xmpp.event('groupchat_subject', msg)

    def jid_in_room(self, room: JID, jid: JID) -> bool:
        for nick in self.rooms[room]:
            entry = self.rooms[room][nick]
            if entry is not None and entry['jid'].full == jid:
                return True
        return False

    def get_nick(self, room: JID, jid: JID) -> Optional[str]:
        for nick in self.rooms[room]:
            entry = self.rooms[room][nick]
            if entry is not None and entry['jid'].full == jid:
                return nick

    def join_muc(self, room: JID, nick: str, maxhistory="0", password='',
                 pstatus='', pshow='', pfrom=''):
        """ Join the specified room, requesting 'maxhistory' lines of history.
        """
        stanza = self.xmpp.make_presence(
            pto="%s/%s" % (room, nick), pstatus=pstatus,
            pshow=pshow, pfrom=pfrom
        )
        stanza.enable('muc_join')
        if password:
            stanza['muc_join']['password'] = password
        if maxhistory:
            if maxhistory == "0":
                stanza['muc_join']['history']['maxchars'] = '0'
            else:
                stanza['muc_join']['history']['maxstanzas'] = str(maxhistory)
        self.xmpp.send(stanza)
        self.rooms[room] = {}
        self.our_nicks[room] = nick

    async def destroy(self, room: JID, reason='', altroom='', *,
                      ifrom: Optional[JID] = None, **iqkwargs) -> Iq:
        """Destroy a room."""
        iq = self.xmpp.make_iq_set(ifrom=ifrom, ito=room)
        iq.enable('mucowner_query')
        iq['mucowner_query'].enable('destroy')
        if altroom:
            iq['mucowner_query']['destroy']['jid'] = altroom
        if reason:
            iq['mucowner_query']['destroy']['reason'] = reason
        await iq.send(**iqkwargs)

    async def set_affiliation(self, room: JID, jid: Optional[JID] = None, nick: Optional[str] = None, *, affiliation: str,
                              ifrom: Optional[JID] = None, **iqkwargs):
        """ Change room affiliation."""
        if affiliation not in AFFILIATIONS:
            raise ValueError('%s is not a valid affiliation' % affiliation)
        if not any((jid, nick)):
            raise ValueError('One of jid or nick must be set')
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        iq.enable('mucadmin_query')
        item = MUCAdminItem()
        item['affiliation'] = affiliation
        if nick:
            item['nick'] = nick
        if jid:
            item['jid'] = jid
        iq['mucadmin_query'].append(item)
        await iq.send(**iqkwargs)

    async def set_role(self, room: JID, nick: str, role: str, *,
                       ifrom: Optional[JID] = None, **iqkwargs) -> Iq:
        """ Change role property of a nick in a room.
            Typically, roles are temporary (they last only as long as you are in the
            room), whereas affiliations are permanent (they last across groupchat
            sessions).
        """
        if role not in ROLES:
            raise ValueError("Role %s does not exist" % role)
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        iq.enable('mucadmin_query')
        item = MUCAdminItem()
        item['role'] = role
        item['nick'] = nick
        iq['mucadmin_query'].append(item)
        await iq.send(**iqkwargs)

    def invite(self, room: JID, jid: JID, reason: str = '', *,
               mfrom: Optional[JID] = None):
        """ Invite a jid to a room."""
        msg = self.xmpp.make_message(room, mfrom=mfrom)
        msg['muc']['invite']['to'] = jid
        if reason:
            msg['muc']['invite']['reason'] = reason
        self.xmpp.send(msg)

    def decline(self, room: JID, jid: JID, reason: str = '', *,
                mfrom: Optional[JID] = None):
        """Decline a mediated invitation."""
        msg = self.xmpp.make_message(room, mfrom=mfrom)
        msg['muc']['decline']['to'] = jid
        if reason:
            msg['muc']['decline']['reason'] = reason
        self.xmpp.send(msg)

    def leave_muc(self, room: JID, nick: str, msg='', pfrom=None):
        """ Leave the specified room.
        """
        if msg:
            self.xmpp.send_presence(pshow='unavailable', pto="%s/%s" % (room, nick), pstatus=msg, pfrom=pfrom)
        else:
            self.xmpp.send_presence(pshow='unavailable', pto="%s/%s" % (room, nick), pfrom=pfrom)
        del self.rooms[room]

    async def get_room_config(self, room: JID, ifrom=''):
        """Get the room config form in 0004 plugin format """
        iq = self.xmpp.make_iq_get(stanza.NS_OWNER, ito=room, ifrom=ifrom)
        # For now, swallow errors to preserve existing API
        result = await iq.send()
        form = result.xml.find('{http://jabber.org/protocol/muc#owner}query/{jabber:x:data}x')
        if form is None:
            raise ValueError("Configuration form not found")
        return self.xmpp.plugin['xep_0004'].build_form(form)

    async def cancel_config(self, room: JID, *,
                            ifrom: Optional[JID] = None, **iqkwargs) -> Iq:
        """Cancel a requested config form"""
        query = MUCOwnerQuery()
        x = ET.Element('{jabber:x:data}x', type='cancel')
        query.append(x)
        iq = self.xmpp.make_iq_set(query, ito=room, ifrom=ifrom)
        return await iq.send(**iqkwargs)

    async def set_room_config(self, room: JID, config, *,
                              ifrom: Optional[JID] = None, **iqkwargs) -> Iq:
        """Send a room config form"""
        query = MUCOwnerQuery()
        config['type'] = 'submit'
        query.append(config)
        iq = self.xmpp.make_iq_set(query, ito=room, ifrom=ifrom)
        return await iq.send(**iqkwargs)

    async def get_affiliation_list(self, room: JID, affiliation: str, *,
                                   ifrom: Optional[JID] = None, **iqkwargs) -> List[JID]:
        """"Get a list of JIDs with the specified affiliation"""
        iq = self.xmpp.make_iq_get(stanza.NS_ADMIN, ito=room, ifrom=ifrom)
        iq['mucadmin_query']['item']['affiliation'] = affiliation
        result = await iq.send(**iqkwargs)
        return [item['jid'] for item in result['mucadmin_query']]

    async def get_roles_list(self, room: JID, role: str, *,
                             ifrom: Optional[JID] = None, **iqkwargs) -> List[str]:
        """"Get a list of JIDs with the specified role"""
        iq = self.xmpp.make_iq_get(stanza.NS_ADMIN, ito=room, ifrom=ifrom)
        iq['mucadmin_query']['item']['role'] = role
        result = await iq.send(**iqkwargs)
        return [item['nick'] for item in result['mucadmin_query']]

    async def send_affiliation_list(self, room: JID, affiliations: List[Tuple[JID, str]], *,
                                    ifrom: Optional[JID] = None, **iqkwargs) -> Iq:
        """Send an affiliation delta list"""
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        for jid, affiliation in affiliations:
            item = MUCAdminItem()
            item['jid'] = jid
            item['affiliation'] = affiliation
            iq['mucadmin_query'].append(item)
        return await iq.send(**iqkwargs)

    async def send_role_list(self, room: JID, roles: List[Tuple[str, str]], *,
                            ifrom: Optional[JID] = None, **iqkwargs) -> Iq:
        """Send a role delta list"""
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        for nick, affiliation in roles:
            item = MUCAdminItem()
            item['nick'] = nick
            item['affiliation'] = affiliation
            iq['mucadmin_query'].append(item)
        return await iq.send(**iqkwargs)

    def get_joined_rooms(self) -> List[JID]:
        return self.rooms.keys()

    def get_our_jid_in_room(self, room_jid: JID) -> str:
        """ Return the jid we're using in a room.
        """
        return "%s/%s" % (room_jid, self.our_nicks[room_jid])

    def get_jid_property(self, room, nick, jid_property):
        """ Get the property of a nick in a room, such as its 'jid' or 'affiliation'
            If not found, return None.
        """
        if room in self.rooms and nick in self.rooms[room] and jid_property in self.rooms[room][nick]:
            return self.rooms[room][nick][jid_property]
        else:
            return None

    def get_roster(self, room: JID) -> List[str]:
        """ Get the list of nicks in a room.
        """
        if room not in self.rooms.keys():
            return None
        return self.rooms[room].keys()

    def get_users_by_affiliation(self, room: JID, affiliation='member', *, ifrom: Optional[JID] = None):
        # Preserve old API
        if affiliation not in AFFILIATIONS:
            raise TypeError
        return self.get_affiliation_list(room, affiliation, ifrom=ifrom)
