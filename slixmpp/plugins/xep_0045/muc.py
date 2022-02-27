# Slixmpp: The Slick XMPP Library
# Copyright (C) 2010 Nathanael C. Fritz
# Copyright (C) 2020 "Maxime “pep” Buquet <pep@bouah.net>"
# This file is part of Slixmpp.
# See the file LICENSE for copying permission.
from __future__ import with_statement

import asyncio
import logging
from datetime import datetime
from typing import (
    Any,
    Dict,
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
from slixmpp.exceptions import IqError, IqTimeout, PresenceError

from slixmpp.plugins.xep_0004 import Form
from slixmpp.plugins.xep_0045 import stanza
from slixmpp.plugins.xep_0045.stanza import (
    MUCInvite,
    MUCDecline,
    MUCDestroy,
    MUCPresence,
    MUCJoin,
    MUCMessage,
    MUCAdminQuery,
    MUCAdminItem,
    MUCHistory,
    MUCOwnerQuery,
    MUCOwnerDestroy,
    MUCStatus,
    MUCActor,
    MUCUserItem,
)
from slixmpp.types import (
    MucRole,
    MucAffiliation,
    MucRoomItem,
    MucRoomItemKeys,
    PresenceArgs,
)

JoinResult = Tuple[Presence, Message, List[Presence], List[Message]]

log = logging.getLogger(__name__)

AFFILIATIONS = ('outcast', 'member', 'admin', 'owner', 'none')
ROLES = ('moderator', 'participant', 'visitor', 'none')


class XEP_0045(BasePlugin):

    """
    XEP-0045 Multi-User Chat
    """

    name = 'xep_0045'
    description = 'XEP-0045: Multi-User Chat'
    dependencies = {'xep_0030', 'xep_0004', 'xep_0203'}
    stanza = stanza

    rooms: Dict[JID, Dict[str, MucRoomItem]]
    our_nicks: Dict[JID, str]

    def plugin_init(self):
        self.rooms = {}
        self.our_nicks = {}
        # load MUC support in presence stanzas
        register_stanza_plugin(MUCMessage, MUCUserItem)
        register_stanza_plugin(MUCPresence, MUCUserItem)
        register_stanza_plugin(MUCUserItem, MUCActor)
        register_stanza_plugin(MUCMessage, MUCInvite)
        register_stanza_plugin(MUCMessage, MUCDecline)
        register_stanza_plugin(MUCMessage, MUCStatus)
        register_stanza_plugin(MUCPresence, MUCStatus)
        register_stanza_plugin(Presence, MUCPresence)
        register_stanza_plugin(MUCPresence, MUCDestroy)
        register_stanza_plugin(Presence, MUCJoin)
        register_stanza_plugin(MUCJoin, MUCHistory)
        register_stanza_plugin(Message, MUCMessage)
        register_stanza_plugin(Iq, MUCAdminQuery)
        register_stanza_plugin(Iq, MUCOwnerQuery)
        register_stanza_plugin(MUCOwnerQuery, MUCOwnerDestroy)
        register_stanza_plugin(MUCOwnerQuery, Form)
        register_stanza_plugin(MUCAdminQuery, MUCAdminItem, iterable=True)

        # Register handlers
        self.xmpp.register_handler(
            Callback(
                'MUCPresence',
                StanzaPath("presence/muc"),
                self._handle_groupchat_presence,
        ))
        # <x xmlns="http://jabber.org/protocol/muc"/> is only used in
        # presence when joining on the client side, and for errors on
        # the server side.
        if self.xmpp.is_component:
            self.xmpp.register_handler(
                Callback(
                    'MUCPresenceJoin',
                    StanzaPath("presence/muc_join"),
                    self._handle_groupchat_join,
            ))
        self.xmpp.register_handler(
            Callback(
                "MUCPresenceError",
                StanzaPath("presence@type=error/muc_join"),
                self._handle_presence_error,
            )
        )

        self.xmpp.register_handler(
            Callback(
                'MUCError',
                MatchXMLMask("<message xmlns='%s' type='error'><error/></message>" % self.xmpp.default_ns),
                self._handle_groupchat_error_message
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCMessage',
                MatchXMLMask("<message xmlns='%s' type='groupchat'><body/></message>" % self.xmpp.default_ns),
                self._handle_groupchat_message
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCSubject',
                MatchXMLMask("<message xmlns='%s' type='groupchat'><subject/></message>" % self.xmpp.default_ns),
                self._handle_groupchat_subject
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCConfig',
                StanzaPath('message/muc/status'),
                self._handle_config_change
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCInvite',
                StanzaPath('message/muc/invite'),
                self._handle_groupchat_invite
        ))
        self.xmpp.register_handler(
            Callback(
                'MUCDecline',
                StanzaPath('message/muc/decline'),
                self._handle_groupchat_decline
        ))

    def plugin_end(self):
        self.xmpp.plugin['xep_0030'].del_feature(feature=stanza.NS)

    def session_bind(self, jid):
        self.xmpp.plugin['xep_0030'].add_feature(stanza.NS)

    def _handle_groupchat_invite(self, inv: Message):
        """ Handle an invite into a muc. """
        if self.xmpp.is_component:
            self.xmpp.event('groupchat_invite', inv)
        else:
            if inv['from'] not in self.rooms.keys():
                self.xmpp.event("groupchat_invite", inv)

    def _handle_groupchat_decline(self, decl: Message):
        """Handle an invitation decline."""
        if self.xmpp.is_component:
            self.xmpp.event('groupchat_invite', decl)
        else:
            if decl['from'] in self.room.keys():
                self.xmpp.event('groupchat_decline', decl)

    def _handle_config_change(self, msg: Message):
        """Handle a MUC configuration change (with status code)."""
        self.xmpp.event('groupchat_config_status', msg)
        self.xmpp.event('muc::%s::config_status' % msg['from'].bare , msg)

    def _client_handle_presence(self, pr: Presence):
        """As a client, handle a presence stanza"""
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
        if 110 in pr['muc']['status_codes']:
            self.xmpp.event("muc::%s::self-presence" % entry['room'], pr)
        self.xmpp.event("muc::%s::presence" % entry['room'], pr)
        if got_offline:
            self.xmpp.event("muc::%s::got_offline" % entry['room'], pr)
        if got_online:
            self.xmpp.event("muc::%s::got_online" % entry['room'], pr)

    def _handle_presence_error(self, pr: Presence):
        """Generate MUC presence error events"""
        self.xmpp.event("muc::%s::presence-error" % pr['from'].bare, pr)

    def _handle_groupchat_presence(self, pr: Presence):
        """ Handle a presence in a muc."""
        if self.xmpp.is_component:
            self.xmpp.event('groupchat_presence', pr)
        else:
            self._client_handle_presence(pr)

    def _handle_groupchat_join(self, pr: Presence):
        """Received a join presence (as a component)"""
        self.xmpp.event('groupchat_join', pr)

    def _handle_groupchat_message(self, msg: Message):
        """ Handle a message event in a muc.
        """
        self.xmpp.event('groupchat_message', msg)
        self.xmpp.event("muc::%s::message" % msg['from'].bare, msg)

    def _handle_groupchat_error_message(self, msg: Message):
        """ Handle a message error event in a muc.
        """
        self.xmpp.event('groupchat_message_error', msg)
        self.xmpp.event("muc::%s::message_error" % msg['from'].bare, msg)


    def _handle_groupchat_subject(self, msg: Message):
        """ Handle a message coming from a muc indicating
        a change of subject (or announcing it when joining the room)
        """
        # See poezio#3452. A message containing subject _and_ (body or thread)
        # is not a subject change.
        if msg['body'] or msg['thread']:
            return
        self.xmpp.event('groupchat_subject', msg)
        self.xmpp.event('muc::%s::groupchat_subject' % msg['from'].bare, msg)

    async def join_muc_wait(self, room: JID, nick: str, *,
                            password: Optional[str] = None,
                            maxchars: Optional[int] = None,
                            maxstanzas: Optional[int] = None,
                            seconds: Optional[int] = None,
                            since: Optional[datetime] = None,
                            presence_options: Optional[PresenceArgs] = None,
                            timeout: Optional[int] = None) -> JoinResult:
        """
        Try to join a MUC and block until we are joined or get an error.

        Only one of {maxchars, maxstanzas, seconds, since} will be used, in
        that order.

        .. versionadded:: 1.8.0

        :param password: The optional room password.
        :param maxchars: Max number of characters to return from history.
        :param maxstanzas: Max number of stanzas to return from history.
        :param seconds: Fetch history until that many seconds in the past.
        :param since: Fetch history since that timestamp.
        :param timeout: Timeout after which a TimeoutError is raised.
                        None means no timeout.
        :raises: A slixmpp.exceptions.PresenceError if the MUC returns a
                 presence error.
        :raises: An asyncio.TimeoutError if there is neither success nor
                presence error when the timeout is reached.
        :return: A tuple containing our own presence, the subject, a list
                 of occupants and a list of history messages.
        """
        if presence_options is None:
            presence_options = {}
        stanza = self.xmpp.make_presence(
            pto="%s/%s" % (room, nick),
            **presence_options
        )
        stanza.enable('muc_join')
        if password is not None:
            stanza['muc_join']['password'] = password
        if maxchars is not None:
            stanza['muc_join']['history']['maxchars'] = str(maxchars)
        elif maxstanzas is not None:
            stanza['muc_join']['history']['maxstanzas'] = str(maxstanzas)
        elif seconds is not None:
            stanza['muc_join']['history']['seconds'] = str(seconds)
        elif since is not None:
            fmt = self.xmpp.plugin['xep_0082'].format_datetime(since)
            stanza['muc_join']['history']['since'] = fmt
        self.rooms[room] = {}
        self.our_nicks[room] = nick
        stanza.send()
        return await self._await_join(room, timeout)

    async def _await_join(self, room: JID, timeout: Optional[int] = None) -> JoinResult:
        """Do the heavy lifting for awaiting a MUC join

        A muc join, once the join stanza is sent, is:
            occupant presences → self-presence → room history → room subject
        """
        presence_done: asyncio.Future = asyncio.Future()
        topic_received: asyncio.Future = asyncio.Future()
        history_buffer: List[Message] = []
        occupant_buffer: List[Presence] = []

        def add_message(msg: Message):
            delay = msg.get_plugin('delay', check=True)
            print(delay)
            if delay is not None and delay['from'] == room:
                history_buffer.append(msg)

        def add_occupant(pres: Presence):
            occupant_buffer.append(pres)

        catch_occupants = self.xmpp.event_handler("muc::%s::got_online" % room, add_occupant)
        catch_history = self.xmpp.event_handler("muc::%s::message" % room, add_message)
        subject_handler = self.xmpp.event_handler("muc::%s::groupchat_subject" % room, topic_received.set_result)
        self_presence = self.xmpp.event_handler("muc::%s::self-presence" % room, presence_done.set_result)
        presence_error = self.xmpp.event_handler("muc::%s::presence-error" % room, presence_done.set_result)

        with subject_handler, catch_history, catch_occupants:
            with self_presence, presence_error:
                done, pending = await asyncio.wait(
                    [presence_done],
                    timeout=timeout,
                )
            if pending:
                raise asyncio.TimeoutError()
            pres: Presence = presence_done.result()
            if pres['type'] == 'error':
                raise PresenceError(pres)
            done, pending = await asyncio.wait(
                [topic_received],
                timeout=timeout,
            )
            if pending:
                raise asyncio.TimeoutError()
        subject: Message = topic_received.result()
        # update known nick in case it has changed
        self.our_nicks[room] = pres['from'].resource
        return (pres, subject, occupant_buffer, history_buffer)

    def join_muc(self, room: JID, nick: str, maxhistory="0", password='',
                 pstatus='', pshow='', pfrom='') -> asyncio.Future:
        """ Join the specified room, requesting 'maxhistory' lines of history.

        .. deprecated:: 1.8.0

            :meth:`join_muc_wait` will replace this old API starting from version
            1.9.0.

        """
        presence_options = PresenceArgs(
            pshow=pshow,
            pstatus=pstatus,
            pfrom=pfrom,
        )
        maxchars, maxstanzas = None, None
        if maxhistory:
            if maxhistory == "0":
                maxchars = 9
            else:
                maxstanzas = int(maxhistory)
        return asyncio.ensure_future(
            self.join_muc_wait(
                room=room,
                nick=nick,
                password=password,
                presence_options=presence_options,
                maxchars=maxchars,
                maxstanzas=maxstanzas,
            ),
            loop=self.xmpp.loop,
        )

    def leave_muc(self, room: JID, nick: str, msg: str = '', pfrom: Optional[JID] = None):
        """ Leave the specified room.

        :param room: Room to leave.
        :param nick: Your nickname.
        :param msg: Presence status to use.
        """
        if msg:
            self.xmpp.send_presence(
                pshow='unavailable',
                pto="%s/%s" % (room, nick),
                pstatus=msg,
                pfrom=pfrom
            )
        else:
            self.xmpp.send_presence(
                pshow='unavailable',
                pto="%s/%s" % (room, nick),
                pfrom=pfrom
            )
        del self.rooms[room]

    def set_subject(self, room: JID, subject: str, *, mfrom: Optional[JID] = None):
        """Set a room’s subject.

        :param room: JID of the room.
        :param subject: Room subject to set.
        """
        msg = self.xmpp.make_message(room, mfrom=mfrom)
        msg['type'] = 'groupchat'
        msg['subject'] = subject
        msg.send()

    async def get_room_config(self, room: JID, ifrom: Optional[JID] = None,
                              **iqkwargs) -> Form:
        """Get the room config form in 0004 plugin format.

        :param room: Room to get the config form from.
        :raises ValueError: When the form is not found.
        :returns: A form object.
        """
        iq = self.xmpp.make_iq_get(stanza.NS_OWNER, ito=room, ifrom=ifrom)
        result = await iq.send(**iqkwargs)
        form = result['mucowner_query'].get_plugin('form', check=True)
        if form is None:
            raise ValueError("Configuration form not found")
        return form

    async def set_room_config(self, room: JID, config: Form, *,
                              ifrom: Optional[JID] = None, **iqkwargs):
        """Send a room config form.

        :param room: Room to send the form to.
        :param config: A filled room form.
        """
        query = MUCOwnerQuery()
        config['type'] = 'submit'
        query.append(config)
        iq = self.xmpp.make_iq_set(query, ito=room, ifrom=ifrom)
        await iq.send(**iqkwargs)

    async def cancel_config(self, room: JID, *,
                            ifrom: Optional[JID] = None, **iqkwargs):
        """Cancel a requested config form.

        :param room: Room to cancel the form for.
        """
        query = MUCOwnerQuery()
        query['form']['type'] = 'cancel'
        iq = self.xmpp.make_iq_set(query, ito=room, ifrom=ifrom)
        await iq.send(**iqkwargs)

    async def destroy(self, room: JID, reason: str = '', altroom: Optional[JID] = None, *,
                      ifrom: Optional[JID] = None, **iqkwargs):
        """Destroy a room.

        :param room: Room JID to destroy.
        :param reason: Reason for destroying the room.
        :param altroom: An alternate room that users should join.
        """
        iq = self.xmpp.make_iq_set(ifrom=ifrom, ito=room)
        iq.enable('mucowner_query')
        iq['mucowner_query'].enable('destroy')
        if altroom:
            iq['mucowner_query']['destroy']['jid'] = altroom
        if reason:
            iq['mucowner_query']['destroy']['reason'] = reason
        await iq.send(**iqkwargs)

    async def set_affiliation(self, room: JID, affiliation: MucAffiliation, *,
                              jid: Optional[JID] = None,
                              nick: Optional[str] = None, reason: str = '',
                              ifrom: Optional[JID] = None, **iqkwargs):
        """ Change room affiliation for a JID or nickname.

        :param room: Room to modify.
        :param affiliation: Affiliation to set.
        :param jid: User JID to use in the set operation.
        :param reason: Reason for the affiliation change.
        """
        if affiliation not in AFFILIATIONS:
            raise ValueError('%s is not a valid affiliation' % affiliation)
        if not any((jid, nick)):
            raise ValueError('One of jid or nick must be set')
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        iq['mucadmin_query']['item']['affiliation'] = affiliation
        if nick:
            iq['mucadmin_query']['item']['nick'] = nick
        if jid:
            iq['mucadmin_query']['item']['jid'] = jid
        if reason:
            iq['mucadmin_query']['item']['reason'] = reason
        await iq.send(**iqkwargs)

    async def get_affiliation_list(self, room: JID, affiliation: MucAffiliation, *,
                                   ifrom: Optional[JID] = None, **iqkwargs) -> List[JID]:
        """Get a list of JIDs with the specified affiliation

        :param room: Room to get affiliations from.
        :param affiliation: The affiliation to list.
        """
        iq = self.xmpp.make_iq_get(stanza.NS_ADMIN, ito=room, ifrom=ifrom)
        iq['mucadmin_query']['item']['affiliation'] = affiliation
        result = await iq.send(**iqkwargs)
        return [item['jid'] for item in result['mucadmin_query']]

    async def send_affiliation_list(self, room: JID,
                                    affiliations: List[Tuple[JID, MucAffiliation]], *,
                                    ifrom: Optional[JID] = None, **iqkwargs):
        """Send an affiliation delta list.

        :param room: Room to send the affiliations to.
        :param affiliations: List of couples (jid, affiliation) to set.
        """
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        for jid, affiliation in affiliations:
            item = MUCAdminItem()
            item['jid'] = jid
            item['affiliation'] = affiliation
            iq['mucadmin_query'].append(item)
        await iq.send(**iqkwargs)

    async def set_role(self, room: JID, nick: str, role: MucRole, *,
                       reason: str = '', ifrom: Optional[JID] = None, **iqkwargs):
        """ Change role property of a nick in a room.
            Typically, roles are temporary (they last only as long as you are in the
            room), whereas affiliations are permanent (they last across groupchat
            sessions).

        :param room: Room to modify.
        :param nick: User nickname to use in the set operation.
        :param role: Role to set.
        :param reason: Reason for the role change.
        """
        if role not in ROLES:
            raise ValueError("Role %s does not exist" % role)
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        iq['mucadmin_query']['item']['role'] = role
        iq['mucadmin_query']['item']['nick'] = nick
        if reason:
            iq['mucadmin_query']['item']['reason'] = reason
        await iq.send(**iqkwargs)

    async def get_roles_list(self, room: JID, role: MucRole, *,
                             ifrom: Optional[JID] = None, **iqkwargs) -> List[str]:
        """"Get a list of JIDs with the specified role

        :param room: Room to get roles from.
        :param role: The role to list.
        """
        iq = self.xmpp.make_iq_get(stanza.NS_ADMIN, ito=room, ifrom=ifrom)
        iq['mucadmin_query']['item']['role'] = role
        result = await iq.send(**iqkwargs)
        return [item['nick'] for item in result['mucadmin_query']]

    async def send_role_list(self, room: JID, roles: List[Tuple[str, MucRole]], *,
                             ifrom: Optional[JID] = None, **iqkwargs):
        """Send a role delta list.

        :param room: Room to send the roles to.
        :param roles: List of couples (nick, role) to set.
        """
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        for nick, affiliation in roles:
            item = MUCAdminItem()
            item['nick'] = nick
            item['affiliation'] = affiliation
            iq['mucadmin_query'].append(item)
        await iq.send(**iqkwargs)

    def invite(self, room: JID, jid: JID, reason: str = '', *,
               mfrom: Optional[JID] = None):
        """ Invite a jid to a room (mediated invitation).

        :param room: Room to invite the user in.
        :param jid: JID of the user to invite.
        :param reason: Reason for inviting the user.
        """
        msg = self.xmpp.make_message(room, mfrom=mfrom)
        msg['muc']['invite']['to'] = jid
        if reason:
            msg['muc']['invite']['reason'] = reason
        self.xmpp.send(msg)

    def invite_server(self, room: JID, jid: JID,
                         invite_from: JID, reason: str = ''):
        """Send a mediated invite to a user, as a MUC service.

        .. versionadded:: 1.8.0

        :param room: Room to invite the user in.
        :param jid: JID of the user to invite.
        :param invite_from: JID of the user to send the invitation from.
        :param reason: Reason for inviting the user.
        """
        if not self.xmpp.is_component:
            raise ValueError("Cannot use this method as a client.")
        msg = self.xmpp.make_message(jid, mfrom=room)
        msg['muc']['invite']['from'] = invite_from
        if reason:
            msg['muc']['invite']['reason'] = reason
        msg.send()

    def decline(self, room: JID, jid: JID, reason: str = '', *,
                mfrom: Optional[JID] = None):
        """Decline a mediated invitation.

        :param room: Room the invitation came from.
        :param jid: JID of the user who sent the invitation.
        :param reason: Reason for declining.
        """
        msg = self.xmpp.make_message(room, mfrom=mfrom)
        msg['muc']['decline']['to'] = jid
        if reason:
            msg['muc']['decline']['reason'] = reason
        self.xmpp.send(msg)

    def request_voice(self, room: JID, role: str, *, mfrom: Optional[JID] = None):
        """Request voice in a moderated room.

        :param room: Room to request voice from.
        """
        #form = self.xmpp['xep_0004'].make_form(ftype='submit')
        msg = self.xmpp.make_message(room, mfrom=mfrom)
        form = msg['form']
        form['type'] = 'submit'
        form.add_field(var='FORM_TYPE', ftype='hidden', value='http://jabber.org/protocol/muc#request')
        form.add_field(var='muc#role', ftype='list-single', label='Requested role', value=role)
        self.xmpp.send(msg)

    def jid_in_room(self, room: JID, jid: JID) -> bool:
        """Check if a JID is present in a room.

        :param room: Room to check.
        :param jid: JID to check.
        """
        for nick in self.rooms[room]:
            entry = self.rooms[room][nick]
            if not entry.get('jid'):
                continue
            if entry is not None and entry['jid'].full == jid:
                return True
        return False

    def get_nick(self, room: JID, jid: JID) -> Optional[str]:
        """Get the nickname of a specific JID in a room.

        :param room: Room to inspect.
        :param jid: JID whose nick to return.
        """
        for nick in self.rooms[room]:
            entry = self.rooms[room][nick]
            if not entry.get('jid'):
                continue
            if entry is not None and entry['jid'].full == jid:
                return nick
        return None

    def get_joined_rooms(self) -> List[JID]:
        """Get the list of rooms we sent a join presence to
        and did not explicitly leave.
        """
        return list(self.rooms.keys())

    def get_our_jid_in_room(self, room_jid: JID) -> str:
        """ Return the jid we're using in a room.
        """
        return "%s/%s" % (room_jid, self.our_nicks[room_jid])

    def get_jid_property(self, room: JID, nick: str,
                         jid_property: MucRoomItemKeys) -> Any:
        """ Get the property of a nick in a room, such as its 'jid' or 'affiliation'
            If not found, return None.

        :param room: Get the property for this room.
        :param nick: Which nickname information to get.
        :param jid_property: Property to fetch.
        """
        if room in self.rooms and nick in self.rooms[room] and jid_property in self.rooms[room][nick]:
            return self.rooms[room][nick][jid_property]
        else:
            return None

    def get_roster(self, room: JID) -> List[str]:
        """ Get the list of nicks in a room.

        :param room: Room to list nicks from.
        """
        if room not in self.rooms.keys():
            raise ValueError("Room %s is not joined" % room)
        return list(self.rooms[room].keys())

    def get_users_by_affiliation(self, room: JID, affiliation='member', *, ifrom: Optional[JID] = None):
        # Preserve old API
        if affiliation not in AFFILIATIONS:
            raise ValueError("Affiliation %s does not exist" % affiliation)
        return self.get_affiliation_list(room, affiliation, ifrom=ifrom)
