"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    Copyright (C) 2020 "Maxime “pep” Buquet <pep@bouah.net>"
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from typing import Iterable, Set
import logging
from slixmpp.xmlstream import ElementBase, ET, JID


log = logging.getLogger(__name__)

NS = 'http://jabber.org/protocol/muc'
NS_USER = 'http://jabber.org/protocol/muc#user'
NS_ADMIN = 'http://jabber.org/protocol/muc#admin'
NS_OWNER = 'http://jabber.org/protocol/muc#owner'


class MUCBase(ElementBase):
    name = 'x'
    namespace = NS_USER
    plugin_attrib = 'muc'
    interfaces = {'affiliation', 'role', 'jid', 'nick', 'room', 'status_codes'}

    def get_status_codes(self) -> Set[str]:
        status = self.xml.findall(f'{{{NS_USER}}}status')
        return {int(status.attrib['code']) for status in status}

    def set_status_codes(self, codes: Iterable[int]):
        self.del_status_codes()
        for code in set(codes):
            self._add_status_code(code)

    def del_status_codes(self):
        status = self.xml.findall(f'{{{NS_USER}}}status')
        for elem in status:
            self.xml.remove(elem)

    def _add_status_code(self, code: int):
        status = MUCStatus()
        status['code'] = code
        self.append(status)

    def get_item_attr(self, attr, default: str):
        item = self.xml.find(f'{{{NS_USER}}}item')
        if item is None:
            return default
        return item.get(attr)

    def set_item_attr(self, attr, value: str):
        item = self.xml.find(f'{{{NS_USER}}}item')
        if item is None:
            item = ET.Element(f'{{{NS_USER}}}item')
            self.xml.append(item)
        item.attrib[attr] = value
        return item

    def del_item_attr(self, attr):
        item = self.xml.find(f'{{{NS_USER}}}item')
        if item is not None and attr in item.attrib:
            del item.attrib[attr]

    def get_affiliation(self):
        return self.get_item_attr('affiliation', '')

    def set_affiliation(self, value):
        self.set_item_attr('affiliation', value)

    def del_affiliation(self):
        # TODO: set default affiliation
        self.del_item_attr('affiliation')

    def get_jid(self):
        return JID(self.get_item_attr('jid', ''))

    def set_jid(self, value):
        if not isinstance(value, str):
            value = str(value)
        self.set_item_attr('jid', value)

    def del_jid(self):
        self.del_item_attr('jid')

    def get_role(self):
        return self.get_item_attr('role', '')

    def set_role(self, value):
        # TODO: check for valid role
        self.set_item_attr('role', value)

    def del_role(self):
        # TODO: set default role
        self.del_item_attr('role')

    def get_nick(self):
        return self.parent()['from'].resource

    def get_room(self):
        return self.parent()['from'].bare

    def set_nick(self, value):
        log.warning(
            "Cannot set nick through the %s plugin.",
            self.__class__.__name__,
        )
        return self

    def set_room(self, value):
        log.warning(
            "Cannot set room through the %s plugin.",
            self.__class__.__name__,
        )
        return self

    def del_nick(self):
        log.warning(
            "Cannot delete nick through the %s plugin.",
            self.__class__.__name__,
        )
        return self

    def del_room(self):
        log.warning(
            "Cannot delete room through the %s plugin.",
            self.__class__.__name__,
        )
        return self


class MUCPresence(MUCBase):
    '''
    A MUC Presence

    ::

        <presence from='foo@muc/user1' type='unavailable'>
            <x xmlns='http://jabber.org/protocol/muc#user'>
                <item affiliation='none'
                      role='none'
                      nick='newnick2'
                      jid='some@jid'/>
                <status code='303'/>
            </x>
        </presence>
    '''


class MUCMessage(MUCBase):
    '''
    A MUC Message

    ::

        <message from='foo@muc/user1' type='groupchat' id='someid'>
            <body>Foo</body>
            <x xmlns='http://jabber.org/protocol/muc#user'>
                <item affiliation='none'
                      role='none'
                      nick='newnick2'
                      jid='some@jid'/>
            </x>
        </message>
    '''

class MUCJoin(ElementBase):
    name = 'x'
    namespace = NS
    plugin_attrib = 'muc_join'
    interfaces = {'password'}
    sub_interfaces = {'password'}


class MUCInvite(ElementBase):
    name = 'invite'
    plugin_attrib = 'invite'
    namespace = NS_USER
    interfaces = {'to', 'from', 'reason'}
    sub_interfaces = {'reason'}


class MUCDecline(ElementBase):
    name = 'decline'
    plugin_attrib = 'decline'
    namespace = NS_USER
    interfaces = {'to', 'from', 'reason'}
    sub_interfaces = {'reason'}


class MUCHistory(ElementBase):
    name = 'history'
    plugin_attrib = 'history'
    namespace = NS
    interfaces = {'maxchars', 'maxstanzas', 'since', 'seconds'}


class MUCOwnerQuery(ElementBase):
    name = 'query'
    plugin_attrib = 'mucowner_query'
    namespace = NS_OWNER


class MUCOwnerDestroy(ElementBase):
    name = 'destroy'
    plugin_attrib = 'destroy'
    interfaces = {'reason', 'jid'}
    sub_interfaces = {'reason'}


class MUCAdminQuery(ElementBase):
    name = 'query'
    plugin_attrib = 'mucadmin_query'
    namespace = NS_ADMIN


class MUCAdminItem(ElementBase):
    namespace = NS_ADMIN
    name = 'item'
    plugin_attrib = 'item'
    interfaces = {'role', 'affiliation', 'nick', 'jid'}


class MUCStatus(ElementBase):
    namespace = NS_USER
    name = 'status'
    plugin_attrib = 'status'
    interfaces = {'code'}

    def set_code(self, code: int):
        self.xml.attrib['code'] = str(code)
