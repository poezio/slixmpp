from slixmpp import JID


class DummyUserStore:
    """
    Simple interface for in memory user store.
    """

    def __init__(self):
        self.users = dict()

    def get(self, jid: JID):
        """
        Returns a dict-like object containing XEP_0077.form_fields for this user.

        :param JID jid: JID of the concerned user
        :returns: None or dict-like
        """
        return self.users.get(jid.bare)

    def remove(self, jid: JID):
        """
        Removes a user from the user store.
        Raise KeyError if the user cannot be found

        :param JID jid: JID of the concerned user
        """
        self.users.pop(jid.bare)

    async def validate(self, iq, fields):
        """
        Should raise ValueError(msg) in case the registration is not OK.
        msg will be sent to the user's XMPP client
        """
        self.users[iq["from"].bare] = {key: iq["register"][key] for key in fields}


class ComponentRegistration:
    async def _handle_registration(self, iq):
        if iq["type"] == "get":
            self._send_form(iq)
        elif iq["type"] == "set":
            if iq["register"]["remove"]:
                try:
                    self.user_store.remove(iq["from"])
                except KeyError:
                    self.send_error(
                        iq,
                        "404",
                        "cancel",
                        "item-not-found",
                        "User not found",
                    )
                else:
                    reply = iq.reply()
                    reply.send()
                    self.xmpp.event("user_unregister", iq)
                return

            for field in self.form_fields:
                if not iq["register"][field]:
                    # Incomplete Registration
                    self.send_error(
                        iq,
                        "406",
                        "modify",
                        "not-acceptable",
                        "Please fill in all fields.",
                    )
                    return

            try:
                await self.user_store.validate(iq, self.form_fields)
            except ValueError as e:
                self.send_error(
                    iq,
                    "406",
                    "modify",
                    "not-acceptable",
                    e.args,
                )
            else:
                reply = iq.reply()
                reply.send()
                self.xmpp.event("user_register", iq)

    def _send_form(self, iq):
        reg = iq["register"]

        user = self.user_store.get(iq["from"])

        if user is None:
            user = {}
        else:
            reg["registered"] = True

        reg["instructions"] = self.form_instructions

        for field in self.form_fields:
            data = user.get(field, "")
            if data:
                reg[field] = data
            else:
                # Add a blank field
                reg.add_field(field)

        reply = iq.reply().set_payload(reg.xml)
        reply.send()

    def send_error(self, iq, code, error_type, name, text=""):
        # FIXME: use XMPPError but the iq payload should include the register info…
        reply = iq.reply()
        reply.set_payload(iq["register"].xml)
        reply.error()
        reply["error"]["code"] = code
        reply["error"]["type"] = error_type
        reply["error"]["condition"] = name
        reply["error"]["text"] = text
        reply.send()
