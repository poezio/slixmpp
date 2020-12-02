"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2020 Mathieu Pasquet <mathieui@mathieui.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""
from typing import (
    Iterable,
    Optional,
    Tuple,
)

from slixmpp import JID
from slixmpp.plugins import BasePlugin
from slixmpp.plugins.xep_0439 import stanza


class XEP_0439(BasePlugin):
    '''XEP-0439: Quick Response'''

    name = 'xep_0439'
    description = 'Quick Response'
    dependencies = {}
    stanza = stanza
    namespace = stanza.NS

    def plugin_init(self) -> None:
        stanza.register_plugins()

    def ask_for_responses(self, mto: JID, body: str,
                          responses: Iterable[Tuple[str, str]],
                          mtype: str = 'chat', lang: Optional[str] = None, *,
                          mfrom: Optional[JID] = None):
        """
        Send a message with a set of responses.

        :param JID mto: The JID of the entity which will receive the message
        :param str body: The message body of the question
        :param Iterable[Tuple[str, str]] responses: A set of tuples containing
            (value, label) for each response
        :param str mtype: The message type
        :param str lang: The lang of the message (if not use, the default
            for this session will be used.
        """
        if lang is None:
            lang = self.xmpp.default_lang
        msg = self.xmpp.make_message(mto=mto, mfrom=mfrom, mtype=mtype)
        msg['body|%s' % lang] = body
        values = set()
        for value, label in responses:
            if value in values:
                raise ValueError("Duplicate values")
            values.add(value)
            elem = stanza.Response()
            elem['lang'] = lang
            elem['value'] = value
            elem['label'] = label
            msg.append(elem)
        msg.send()

    def ask_for_actions(self, mto: JID, body: str,
                        actions: Iterable[Tuple[str, str]],
                        mtype: str = 'chat', lang: Optional[str] = None, *,
                        mfrom: Optional[JID] = None):
        """
        Send a message with a set of actions.

        :param JID mto: The JID of the entity which will receive the message
        :param str body: The message body of the question
        :param Iterable[Tuple[str, str]] actions: A set of tuples containing
            (action, label) for each action
        :param str mtype: The message type
        :param str lang: The lang of the message (if not use, the default
            for this session will be used.
        """
        if lang is None:
            lang = self.xmpp.default_lang
        msg = self.xmpp.make_message(mto=mto, mfrom=mfrom, mtype=mtype)
        msg['body|%s' % lang] = body
        ids = set()
        for id, label in actions:
            if id in ids:
                raise ValueError("Duplicate ids")
            ids.add(id)
            elem = stanza.Action()
            elem['lang'] = lang
            elem['id'] = id
            elem['label'] = label
            msg.append(elem)
        msg.send()
