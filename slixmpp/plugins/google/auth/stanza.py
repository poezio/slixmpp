
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
# This file is part of slixmpp.
# See the file LICENSE for copying permission.
from slixmpp.xmlstream import ElementBase, ET


class GoogleAuth(ElementBase):
    name = 'auth'
    namespace = 'http://www.google.com/talk/protocol/auth'
    plugin_attrib = 'google'
    interfaces = {'client_uses_full_bind_result', 'service'}

    discovery_attr= '{%s}client-uses-full-bind-result' % namespace
    service_attr= '{%s}service' % namespace

    def setup(self, xml):
        """Don't create XML for the plugin."""
        self.xml = ET.Element('')

    def get_client_uses_full_bind_result(self):
        return self.parent()._get_attr(self.discovery_attr) == 'true'

    def set_client_uses_full_bind_result(self, value):
        if value in (True, 'true'):
            self.parent()._set_attr(self.discovery_attr, 'true')
        else:
            self.parent()._del_attr(self.discovery_attr)

    def del_client_uses_full_bind_result(self):
        self.parent()._del_attr(self.discovery_attr)

    def get_service(self):
        return self.parent()._get_attr(self.service_attr, '')

    def set_service(self, value):
        if value:
            self.parent()._set_attr(self.service_attr, value)
        else:
            self.parent()._del_attr(self.service_attr)

    def del_service(self):
        self.parent()._del_attr(self.service_attr)
