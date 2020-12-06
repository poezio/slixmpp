"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2020 Mathieu Pasquet
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import asyncio
import os
try:
    from unittest import IsolatedAsyncioTestCase
except ImportError:
    # Python < 3.8
    # just to make sure the imports do not break, but
    # not usable.
    from unittest import TestCase as IsolatedAsyncioTestCase
from typing import (
    List,
)

from slixmpp import JID
from slixmpp.clientxmpp import ClientXMPP


class SlixIntegration(IsolatedAsyncioTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clients = []
        self.addAsyncCleanup(self._destroy)

    def envjid(self, name):
        """Get a JID from an env var"""
        value = os.getenv(name)
        return JID(value)

    def envstr(self, name):
        """get a str from an env var"""
        return os.getenv(name)

    def register_plugins(self, plugins: List[str]):
        """Register plugins on all known clients"""
        for plugin in plugins:
            for client in self.clients:
                client.register_plugin(plugin)

    def add_client(self, jid: JID, password: str):
        """Register a new client"""
        self.clients.append(ClientXMPP(jid, password))

    async def connect_clients(self):
        """Connect all clients"""
        for client in self.clients:
            client.connect()
        wait = [client.wait_until('session_start') for client in self.clients]
        await asyncio.gather(*wait)

    async def _destroy(self):
        """Kill all clients"""
        for client in self.clients:
            client.abort()
