"""
    Slixmpp: The Slick XMPP Library

    Shamelessly copied from Syndace's python-omemo examples.
"""

import omemo

import os
import copy
import json


class AsyncInMemoryStorage(omemo.Storage):
    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        self.__state = None
        self.__own_data = None
        self.__sessions = {}
        self.__devices = {}
        self.__trusted = True

    def dump(self):
        return copy.deepcopy({
            "state"    : self.__state,
            "sessions" : self.__sessions,
            "devices"  : self.__devices
        })

    def trust(self, trusted):
        self.__trusted = trusted

    def loadOwnData(self, callback):
        if self.__own_data is None:
            try:
                filepath = os.path.join(self.storage_dir, 'own_data.json')
                with open(filepath, 'r') as f:
                    self.__own_data = json.load(f)
            except OSError:
                return callback(True, None)
            except json.JSONDecodeError as e:
                return callback(False, e)

        return callback(True, self.__own_data)

    def storeOwnData(self, callback, own_bare_jid, own_device_id):
        self.__own_data = {
            'own_bare_jid': own_bare_jid,
            'own_device_id': own_device_id,
        }

        try:
            filepath = os.path.join(self.storage_dir, 'own_data.json')
            with open(filepath, 'w') as f:
                json.dump(self.__own_data, f)
                return callback(True, None)
        except Exception as e:
            return callback(False, e)

    def loadState(self, callback):
        if self.__state is None:
            try:
                filepath = os.path.join(self.storage_dir, 'omemo.json')
                with open(filepath, 'r') as f:
                    self.__state = json.load(f)
            except OSError:
                return callback(True, None)
            except json.JSONDecodeError as e:
                return callback(False, e)

        return callback(True, self.__state)

    def storeState(self, callback, state):
        self.__state = state
        try:
            filepath = os.path.join(self.storage_dir, 'omemo.json')
            with open(filepath, 'w') as f:
                json.dump(self.__state, f)
                return callback(True, None)
        except Exception as e:
            return callback(False, e)

    def loadSession(self, callback, bare_jid, device_id):
        callback(True, self.__sessions.get(bare_jid, {}).get(device_id, None))

    def storeSession(self, callback, bare_jid, device_id, session):
        self.__sessions[bare_jid] = self.__sessions.get(bare_jid, {})
        self.__sessions[bare_jid][device_id] = session

        callback(True, None)

    def loadActiveDevices(self, callback, bare_jid):
        if self.__devices is None:
            try:
                filepath = os.path.join(self.storage_dir, 'devices.json')
                with open(filepath, 'r') as f:
                    self.__devices = json.load(f)
            except OSError:
                return callback(True, None)
            except json.JSONDecodeError as e:
                return callback(False, e)

        return callback(True, self.__devices.get(bare_jid, {}).get("active", []))

    def storeActiveDevices(self, callback, bare_jid, devices):
        self.__devices[bare_jid] = self.__devices.get(bare_jid, {})
        self.__devices[bare_jid]["active"] = devices

        try:
            filepath = os.path.join(self.storage_dir, 'devices.json')
            with open(filepath, 'w') as f:
                json.dump(self.__devices, f)
                return callback(True, None)
        except Exception as e:
            return callback(False, e)


    def storeInactiveDevices(self, callback, bare_jid, devices):
        self.__devices[bare_jid] = self.__devices.get(bare_jid, {})
        self.__devices[bare_jid]["inactive"] = devices

        callback(True, None)

    def isTrusted(self, callback, bare_jid, device):
        result = False

        if self.__trusted == True:
            result = True
        else:
            result = bare_jid in self.__trusted and device in self.__trusted[bare_jid]

        callback(True, result)

    @property
    def is_async(self):
        return True
