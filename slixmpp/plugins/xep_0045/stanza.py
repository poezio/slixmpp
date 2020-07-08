"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2010 Nathanael C. Fritz
    Copyright (C) 2020 "Maxime “pep” Buquet <pep@bouah.net>"
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

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
    interfaces = {'affiliation', 'role', 'jid', 'nick', 'room'}

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
        item = self.xml.find('f{{{NS_USER}}}item')
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
