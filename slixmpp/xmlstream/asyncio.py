"""
A module that monkey patches the standard asyncio module to add an
idle_call() method to the main loop. This method is used to execute a
callback whenever the loop is not busy handling anything else. This means
that it is a callback with lower priority than IO, timer, or even
call_soon() ones. These callback are called only once each.
"""

import asyncio
from asyncio import events

import collections

def idle_call(self, callback):
    if asyncio.iscoroutinefunction(callback):
        raise TypeError("coroutines cannot be used with idle_call()")
    handle = events.Handle(callback, [], self)
    self._idle.append(handle)

def my_run_once(self):
    if self._idle:
        self._ready.append(events.Handle(lambda: None, (), self))
    real_run_once(self)
    if self._idle:
        handle = self._idle.popleft()
        handle._run()

cls = asyncio.get_event_loop().__class__

cls._idle = collections.deque()
cls.idle_call = idle_call
real_run_once = cls._run_once
cls._run_once = my_run_once

