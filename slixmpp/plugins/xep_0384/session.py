"""
    Wrap omemo.SessionManager object to return futures
"""

from omemo import SessionManager

from asyncio import Future


def wrap(method, *args, **kwargs):
    future = Future()
    promise = method(*args, **kwargs)
    promise.then(future.set_result, future.set_exception)
    return future


class WrappedSessionManager(SessionManager):
    @classmethod
    def create(cls, *args, **kwargs) -> Future:
        return wrap(super().create, *args, **kwargs)

    def encryptMessage(self, *args, **kwargs) -> Future:
        return wrap(super().encryptMessage, *args, **kwargs)

    def decryptMessage(self, *args, **kwargs) -> Future:
        return wrap(super().decryptMessage, *args, **kwargs)

    def newDeviceList(self, *args, **kwargs) -> Future:
        return wrap(super().newDeviceList, *args, **kwargs)

    def getDevices(self, *args, **kwargs) -> Future:
        return wrap(super().getDevices, *args, **kwargs)
