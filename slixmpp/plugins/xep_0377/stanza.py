"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2020 Mathieu Pasquet
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.xmlstream import ET, ElementBase


class Report(ElementBase):
    """
    A spam/abuse report.

    Example sub stanza:

    <report xmlns="urn:xmpp:reporting:0">
      <text xml:lang="en">
        Never came trouble to my house like this.
      </text>
      <spam/>
    </report>

    Stanza Interface:
        abuse    -- Flag the report as abuse
        spam     -- Flag the report as spam
        text     -- Add a reason to the report
    """
    name = "report"
    namespace = "urn:xmpp:reporting:0"
    plugin_attrib = "report"
    interfaces = ("spam", "abuse", "text")
    sub_interfaces = {'text'}

    def get_spam(self):
        return self.xml.find('{%s}spam' % self.namespace) is not None

    def set_spam(self, value):
        if bool(value) and not self.get_spam():
            self.xml.append(ET.Element('{%s}spam' % self.namespace))
        elif not bool(value):
            found = self.xml.findall('{%s}spam' % self.namespace)
            if elm:
                for item in found:
                    self.xml.remove(item)

    def get_abuse(self):
        return self.xml.find('{%s}abuse' % self.namespace) is not None

    def set_abuse(self, value):
        if bool(value) and not self.get_abuse():
            self.xml.append(ET.Element('{%s}abuse' % self.namespace))
        elif not bool(value):
            found = self.xml.findall('{%s}abuse' % self.namespace)
            if elm:
                for item in found:
                    self.xml.remove(item)

class Text(ElementBase):
    name = "text"
    plugin_attrib = "text"
    namespace = "urn:xmpp:reporting:0"
