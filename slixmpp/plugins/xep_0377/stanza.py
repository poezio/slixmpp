
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2020 Mathieu Pasquet
# This file is part of Slixmpp.
# See the file LICENSE for copying permission.
from slixmpp.xmlstream import ET, ElementBase


class Report(ElementBase):
    """
    A spam/abuse report.

    Example sub stanza:
    ::

        <report xmlns="urn:xmpp:reporting:0">
          <text xml:lang="en">
            Never came trouble to my house like this.
          </text>
          <spam/>
        </report>

    Stanza Interface:
    ::

        abuse    -- Flag the report as abuse
        spam     -- Flag the report as spam
        text     -- Add a reason to the report

    Only one <spam/> or <abuse/> element can be present at once.
    """
    name = "report"
    namespace = "urn:xmpp:reporting:0"
    plugin_attrib = "report"
    interfaces = ("spam", "abuse", "text")
    sub_interfaces = {'text'}

    def _purge_spam(self):
        spam = self.xml.findall('{%s}spam' % self.namespace)
        for element in spam:
            self.xml.remove(element)

    def _purge_abuse(self):
        abuse = self.xml.findall('{%s}abuse' % self.namespace)
        for element in abuse:
            self.xml.remove(element)

    def get_spam(self):
        return self.xml.find('{%s}spam' % self.namespace) is not None

    def set_spam(self, value):
        self._purge_spam()
        if bool(value):
            self._purge_abuse()
            self.xml.append(ET.Element('{%s}spam' % self.namespace))

    def get_abuse(self):
        return self.xml.find('{%s}abuse' % self.namespace) is not None

    def set_abuse(self, value):
        self._purge_abuse()
        if bool(value):
            self._purge_spam()
            self.xml.append(ET.Element('{%s}abuse' % self.namespace))


class Text(ElementBase):
    name = "text"
    plugin_attrib = "text"
    namespace = "urn:xmpp:reporting:0"
