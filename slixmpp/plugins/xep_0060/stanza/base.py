
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2011  Nathanael C. Fritz
# This file is part of Slixmpp.
# See the file LICENSE for copying permission.
from slixmpp.xmlstream import ET


class OptionalSetting(object):

    interfaces = {'required'}

    def set_required(self, value):
        if value in (True, 'true', 'True', '1'):
            self.xml.append(ET.Element("{%s}required" % self.namespace))
        elif self['required']:
            self.del_required()

    def get_required(self):
        required = self.xml.find("{%s}required" % self.namespace)
        return required is not None

    def del_required(self):
        required = self.xml.find("{%s}required" % self.namespace)
        if required is not None:
            self.xml.remove(required)
