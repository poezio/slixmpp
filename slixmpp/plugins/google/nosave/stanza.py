
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
# This file is part of slixmpp.
# See the file LICENSE for copying permission.
from slixmpp.jid import JID
from slixmpp.xmlstream import ElementBase, register_stanza_plugin


class NoSave(ElementBase):
    name = 'x'
    namespace = 'google:nosave'
    plugin_attrib = 'google_nosave'
    interfaces = {'value'}

    def get_value(self):
        return self._get_attr('value', '') == 'enabled'

    def set_value(self, value):
        self._set_attr('value', 'enabled' if value else 'disabled')


class NoSaveQuery(ElementBase):
    name = 'query'
    namespace = 'google:nosave'
    plugin_attrib = 'google_nosave'
    interfaces = set()


class Item(ElementBase):
    name = 'item'
    namespace = 'google:nosave'
    plugin_attrib = 'item'
    plugin_multi_attrib = 'items'
    interfaces = {'jid', 'source', 'value'}

    def get_value(self):
        return self._get_attr('value', '') == 'enabled'

    def set_value(self, value):
        self._set_attr('value', 'enabled' if value else 'disabled')

    def get_jid(self):
        return JID(self._get_attr('jid', ''))

    def set_jid(self, value):
        self._set_attr('jid', str(value))

    def get_source(self):
        return JID(self._get_attr('source', ''))

    def set_source(self, value):
        self._set_attr('source', str(value))


register_stanza_plugin(NoSaveQuery, Item)
