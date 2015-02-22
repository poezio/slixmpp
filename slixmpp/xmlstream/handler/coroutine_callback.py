# -*- coding: utf-8 -*-
"""
    slixmpp.xmlstream.handler.callback
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Part of Slixmpp: The Slick XMPP Library

    :copyright: (c) 2011 Nathanael C. Fritz
    :license: MIT, see LICENSE for more details
"""

from slixmpp.xmlstream.handler.base import BaseHandler
from slixmpp.xmlstream.asyncio import asyncio


class CoroutineCallback(BaseHandler):

    """
    The Callback handler will execute a callback function with
    matched stanzas.

    The handler may execute the callback either during stream
    processing or during the main event loop.

    The event will be scheduled to be run soon in the event loop instead
    of immediately.

    :param string name: The name of the handler.
    :param matcher: A :class:`~slixmpp.xmlstream.matcher.base.MatcherBase`
                    derived object for matching stanza objects.
    :param pointer: The function to execute during callback. If ``pointer``
                    is not a coroutine, this function will raise a ValueError.
    :param bool once: Indicates if the handler should be used only
                      once. Defaults to False.
    :param bool instream: Indicates if the callback should be executed
                          during stream processing instead of in the
                          main event loop.
    :param stream: The :class:`~slixmpp.xmlstream.xmlstream.XMLStream`
                   instance this handler should monitor.
    """

    def __init__(self, name, matcher, pointer, once=False,
                 instream=False, stream=None):
        BaseHandler.__init__(self, name, matcher, stream)
        if not asyncio.iscoroutinefunction(pointer):
            raise ValueError("Given function is not a coroutine")

        @asyncio.coroutine
        def pointer_wrapper(stanza, *args, **kwargs):
            try:
                yield from pointer(stanza, *args, **kwargs)
            except Exception as e:
                stanza.exception(e)

        self._pointer = pointer_wrapper
        self._once = once
        self._instream = instream

    def prerun(self, payload):
        """Execute the callback during stream processing, if
        the callback was created with ``instream=True``.

        :param payload: The matched
            :class:`~slixmpp.xmlstream.stanzabase.ElementBase` object.
        """
        if self._once:
            self._destroy = True
        if self._instream:
            self.run(payload, True)

    def run(self, payload, instream=False):
        """Execute the callback function with the matched stanza payload.

        :param payload: The matched
            :class:`~slixmpp.xmlstream.stanzabase.ElementBase` object.
        :param bool instream: Force the handler to execute during stream
                              processing. This should only be used by
                              :meth:`prerun()`. Defaults to ``False``.
        """
        if not self._instream or instream:
            asyncio.async(self._pointer(payload))
            if self._once:
                self._destroy = True
                del self._pointer
