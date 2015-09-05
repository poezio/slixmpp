"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2012 Nathanael C. Fritz,
                       Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import base64


from slixmpp.util import bytes
from slixmpp.xmlstream import ElementBase


class BitsOfBinary(ElementBase):
    name = 'data'
    namespace = 'urn:xmpp:bob'
    plugin_attrib = 'bob'
    interfaces = set(('cid', 'max_age', 'type', 'data'))

    def get_max_age(self):
        return int(self._get_attr('max-age'))

    def set_max_age(self, value):
        self._set_attr('max-age', str(value))

    def get_data(self):
        return base64.b64decode(bytes(self.xml.text))

    def set_data(self, value):
        self.xml.text = bytes(base64.b64encode(value)).decode('utf-8')

    def del_data(self):
        self.xml.text = ''
