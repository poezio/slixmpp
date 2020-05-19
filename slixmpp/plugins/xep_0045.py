"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""
from __future__ import with_statement

import logging

from slixmpp import Presence, Message
from slixmpp.plugins import BasePlugin, register_plugin
from slixmpp.xmlstream import register_stanza_plugin, ElementBase, JID, ET
from slixmpp.xmlstream.handler.callback import Callback
from slixmpp.xmlstream.matcher.xpath import MatchXPath
from slixmpp.xmlstream.matcher.xmlmask import MatchXMLMask
from slixmpp.exceptions import IqError, IqTimeout


log = logging.getLogger(__name__)


class MUCPresence(ElementBase):
    name = 'x'
    namespace = 'http://jabber.org/protocol/muc#user'
    plugin_attrib = 'muc'
    interfaces = {'affiliation', 'role', 'jid', 'nick', 'room'}
    affiliations = {'', }
    roles = {'', }

    def get_item_attr(self, attr, default):
        item = self.xml.find('{http://jabber.org/protocol/muc#user}item')
        if item is None:
            return default
        return item.get(attr)

    def set_item_attr(self, attr, value):
        item = self.xml.find('{http://jabber.org/protocol/muc#user}item')
        if item is None:
            item = ET.Element('{http://jabber.org/protocol/muc#user}item')
            self.xml.append(item)
        item.attrib[attr] = value
        return item

    def del_item_attr(self, attr):
        item = self.xml.find('{http://jabber.org/protocol/muc#user}item')
        if item is not None and attr in item.attrib:
            del item.attrib[attr]

    def get_affiliation(self):
        return self.get_item_attr('affiliation', '')

    def set_affiliation(self, value):
        self.set_item_attr('affiliation', value)
        return self

    def del_affiliation(self):
        # TODO: set default affiliation
        self.del_item_attr('affiliation')
        return self

    def get_jid(self):
        return JID(self.get_item_attr('jid', ''))

    def set_jid(self, value):
        if not isinstance(value, str):
            value = str(value)
        self.set_item_attr('jid', value)
        return self

    def del_jid(self):
        self.del_item_attr('jid')
        return self

    def get_role(self):
        return self.get_item_attr('role', '')

    def set_role(self, value):
        # TODO: check for valid role
        self.set_item_attr('role', value)
        return self

    def del_role(self):
        # TODO: set default role
        self.del_item_attr('role')
        return self

    def get_nick(self):
        return self.parent()['from'].resource

    def get_room(self):
        return self.parent()['from'].bare

    def set_nick(self, value):
        log.warning("Cannot set nick through mucpresence plugin.")
        return self

    def set_room(self, value):
        log.warning("Cannot set room through mucpresence plugin.")
        return self

    def del_nick(self):
        log.warning("Cannot delete nick through mucpresence plugin.")
        return self

    def del_room(self):
        log.warning("Cannot delete room through mucpresence plugin.")
        return self


class XEP_0045(BasePlugin):

    """
    Implements XEP-0045 Multi-User Chat
    """

    name = 'xep_0045'
    description = 'XEP-0045: Multi-User Chat'
    dependencies = {'xep_0030', 'xep_0004'}

    def plugin_init(self):
        self.rooms = {}
        self.our_nicks = {}
        self.xep = '0045'
        # load MUC support in presence stanzas
        register_stanza_plugin(Presence, MUCPresence)
        self.xmpp.register_handler(Callback('MUCPresence', MatchXMLMask("<presence xmlns='%s' />" % self.xmpp.default_ns), self.handle_groupchat_presence))
        self.xmpp.register_handler(Callback('MUCError', MatchXMLMask("<message xmlns='%s' type='error'><error/></message>" % self.xmpp.default_ns), self.handle_groupchat_error_message))
        self.xmpp.register_handler(Callback('MUCMessage', MatchXMLMask("<message xmlns='%s' type='groupchat'><body/></message>" % self.xmpp.default_ns), self.handle_groupchat_message))
        self.xmpp.register_handler(Callback('MUCSubject', MatchXMLMask("<message xmlns='%s' type='groupchat'><subject/></message>" % self.xmpp.default_ns), self.handle_groupchat_subject))
        self.xmpp.register_handler(Callback('MUCConfig', MatchXMLMask("<message xmlns='%s' type='groupchat'><x xmlns='http://jabber.org/protocol/muc#user'><status/></x></message>" % self.xmpp.default_ns), self.handle_config_change))
        self.xmpp.register_handler(Callback('MUCInvite', MatchXPath("{%s}message/{%s}x/{%s}invite" % (
            self.xmpp.default_ns,
            'http://jabber.org/protocol/muc#user',
            'http://jabber.org/protocol/muc#user')), self.handle_groupchat_invite))

    def plugin_end(self):
        self.xmpp.plugin['xep_0030'].del_feature(feature='http://jabber.org/protocol/muc')

    def session_bind(self, jid):
        self.xmpp.plugin['xep_0030'].add_feature('http://jabber.org/protocol/muc')

    def handle_groupchat_invite(self, inv):
        """ Handle an invite into a muc.
        """
        logging.debug("MUC invite to %s from %s: %s", inv['to'], inv["from"], inv)
        if inv['from'] not in self.rooms.keys():
            self.xmpp.event("groupchat_invite", inv)

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

    def jid_in_room(self, room, jid):
        for nick in self.rooms[room]:
            entry = self.rooms[room][nick]
            if entry is not None and entry['jid'].full == jid:
                return True
        return False

    def get_nick(self, room, jid):
        for nick in self.rooms[room]:
            entry = self.rooms[room][nick]
            if entry is not None and entry['jid'].full == jid:
                return nick

    def configure_room(self, room, form=None, ifrom=None):
        if form is None:
            form = self.get_room_config(room, ifrom=ifrom)
        iq = self.xmpp.make_iq_set()
        iq['to'] = room
        if ifrom is not None:
            iq['from'] = ifrom
        query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
        form['type'] = 'submit'
        query.append(form)
        iq.append(query)
        # For now, swallow errors to preserve existing API
        try:
            result = iq.send()
        except IqError:
            return False
        except IqTimeout:
            return False
        return True

    def join_muc(self, room, nick, maxhistory="0", password='', wait=False, pstatus=None, pshow=None, pfrom=None):
        """ Join the specified room, requesting 'maxhistory' lines of history.
        """
        stanza = self.xmpp.make_presence(pto="%s/%s" % (room, nick), pstatus=pstatus, pshow=pshow, pfrom=pfrom)
        x = ET.Element('{http://jabber.org/protocol/muc}x')
        if password:
            passelement = ET.Element('{http://jabber.org/protocol/muc}password')
            passelement.text = password
            x.append(passelement)
        if maxhistory:
            history = ET.Element('{http://jabber.org/protocol/muc}history')
            if maxhistory ==  "0":
                history.attrib['maxchars'] = maxhistory
            else:
                history.attrib['maxstanzas'] = maxhistory
            x.append(history)
        stanza.append(x)
        if not wait:
            self.xmpp.send(stanza)
        else:
            #wait for our own room presence back
            expect = ET.Element("{%s}presence" % self.xmpp.default_ns, {'from':"%s/%s" % (room, nick)})
            self.xmpp.send(stanza, expect)
        self.rooms[room] = {}
        self.our_nicks[room] = nick

    def destroy(self, room, reason='', altroom = '', ifrom=None):
        iq = self.xmpp.make_iq_set()
        if ifrom is not None:
            iq['from'] = ifrom
        iq['to'] = room
        query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
        destroy = ET.Element('{http://jabber.org/protocol/muc#owner}destroy')
        if altroom:
            destroy.attrib['jid'] = altroom
        xreason = ET.Element('{http://jabber.org/protocol/muc#owner}reason')
        xreason.text = reason
        destroy.append(xreason)
        query.append(destroy)
        iq.append(query)
        # For now, swallow errors to preserve existing API
        try:
            r = iq.send()
        except IqError:
            return False
        except IqTimeout:
            return False
        return True

    def set_affiliation(self, room, jid=None, nick=None, affiliation='member', ifrom=None):
        """ Change room affiliation."""
        if affiliation not in ('outcast', 'member', 'admin', 'owner', 'none'):
            raise TypeError
        query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
        if nick is not None:
            item = ET.Element('{http://jabber.org/protocol/muc#admin}item', {'affiliation':affiliation, 'nick':nick})
        else:
            item = ET.Element('{http://jabber.org/protocol/muc#admin}item', {'affiliation':affiliation, 'jid':jid})
        query.append(item)
        iq = self.xmpp.make_iq_set(query)
        iq['to'] = room
        iq['from'] = ifrom
        # For now, swallow errors to preserve existing API
        try:
            result = iq.send()
        except IqError:
            return False
        except IqTimeout:
            return False
        return True

    def set_role(self, room, nick, role):
        """ Change role property of a nick in a room.
            Typically, roles are temporary (they last only as long as you are in the
            room), whereas affiliations are permanent (they last across groupchat
            sessions).
        """
        if role not in ('moderator', 'participant', 'visitor', 'none'):
            raise TypeError
        query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
        item = ET.Element('item', {'role':role, 'nick':nick})
        query.append(item)
        iq = self.xmpp.make_iq_set(query)
        iq['to'] = room
        result = iq.send()
        if result is False or result['type'] != 'result':
            raise ValueError
        return True

    def invite(self, room, jid, reason='', mfrom=''):
        """ Invite a jid to a room."""
        msg = self.xmpp.make_message(room)
        msg['from'] = mfrom
        x = ET.Element('{http://jabber.org/protocol/muc#user}x')
        invite = ET.Element('{http://jabber.org/protocol/muc#user}invite', {'to': jid})
        if reason:
            rxml = ET.Element('{http://jabber.org/protocol/muc#user}reason')
            rxml.text = reason
            invite.append(rxml)
        x.append(invite)
        msg.append(x)
        self.xmpp.send(msg)

    def leave_muc(self, room, nick, msg='', pfrom=None):
        """ Leave the specified room.
        """
        if msg:
            self.xmpp.send_presence(pshow='unavailable', pto="%s/%s" % (room, nick), pstatus=msg, pfrom=pfrom)
        else:
            self.xmpp.send_presence(pshow='unavailable', pto="%s/%s" % (room, nick), pfrom=pfrom)
        del self.rooms[room]

    def get_room_config(self, room, ifrom=''):
        iq = self.xmpp.make_iq_get('http://jabber.org/protocol/muc#owner')
        iq['to'] = room
        iq['from'] = ifrom
        # For now, swallow errors to preserve existing API
        try:
            result = iq.send()
        except IqError:
            raise ValueError
        except IqTimeout:
            raise ValueError
        form = result.xml.find('{http://jabber.org/protocol/muc#owner}query/{jabber:x:data}x')
        if form is None:
            raise ValueError
        return self.xmpp.plugin['xep_0004'].build_form(form)

    def cancel_config(self, room, ifrom=None):
        query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
        x = ET.Element('{jabber:x:data}x', type='cancel')
        query.append(x)
        iq = self.xmpp.make_iq_set(query)
        iq['to'] = room
        iq['from'] = ifrom
        iq.send()

    def set_room_config(self, room, config, ifrom=''):
        query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
        config['type'] = 'submit'
        query.append(config)
        iq = self.xmpp.make_iq_set(query)
        iq['to'] = room
        iq['from'] = ifrom
        iq.send()

    def get_joined_rooms(self):
        return self.rooms.keys()

    def get_our_jid_in_room(self, room_jid):
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

    def get_roster(self, room):
        """ Get the list of nicks in a room.
        """
        if room not in self.rooms.keys():
            return None
        return self.rooms[room].keys()

    def get_users_by_affiliation(cls, room, affiliation='member', ifrom=None):
        if affiliation not in ('outcast', 'member', 'admin', 'owner', 'none'):
            raise TypeError
        query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
        item = ET.Element('{http://jabber.org/protocol/muc#admin}item', {'affiliation': affiliation})
        query.append(item)
        iq = cls.xmpp.Iq(sto=room, sfrom=ifrom, stype='get')
        iq.append(query)
        return iq.send()


register_plugin(XEP_0045)
