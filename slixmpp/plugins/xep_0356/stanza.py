from slixmpp.stanza import Message
from slixmpp.xmlstream import (
    ElementBase,
    register_stanza_plugin,
)
from slixmpp.plugins.xep_0297 import Forwarded


class Privilege(ElementBase):
    namespace = "urn:xmpp:privilege:1"
    name = "privilege"
    plugin_attrib = "privilege"

    def permission(self, access):
        for perm in self["perms"]:
            if perm["access"] == access:
                return perm["type"]

    def roster(self):
        return self.permission("roster")

    def message(self):
        return self.permission("message")

    def presence(self):
        return self.permission("presence")
    
    def add_perm(self, access, type):
        # This should only be needed for servers, so maybe out of scope for slixmpp
        perm = Perm()
        perm["type"] = type
        perm["access"] = access
        self.append(perm)


class Perm(ElementBase):
    namespace = "urn:xmpp:privilege:1"
    name = "perm"
    plugin_attrib = "perm"
    plugin_multi_attrib = "perms"
    interfaces = {"type", "access"}


def register():
    register_stanza_plugin(Message, Privilege)
    register_stanza_plugin(Privilege, Forwarded)
    register_stanza_plugin(Privilege, Perm, iterable=True)