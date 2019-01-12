"""
    Slixmpp: The Slick XMPP Library

    Shamelessly inspired from Syndace's python-omemo examples.
"""


import os
import copy
import json
from typing import Any, Dict, List, Optional, Set, Union

import omemo


class SyncFileStorage(omemo.Storage):
    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = storage_dir
        self.__state = None
        self.__own_data = None  # type: Optional[Dict[str, Union[str, int]]]
        self.__sessions = {}  # type: Dict[str, Dict[int, Any]]
        self.__devices = {}  # type: Dict[str, Dict[str, Union[List[int], Dict[int, int]]]]
        self.__trust = {}  # type: Dict[str, Dict[int, Dict[str, Any]]]

    def dump(self):
        return copy.deepcopy({
            "state"    : self.__state,
            "sessions" : self.__sessions,
            "devices"  : self.__devices
        })

    def loadOwnData(self, _callback):
        if self.__own_data is None:
            try:
                filepath = os.path.join(self.storage_dir, 'own_data.json')
                with open(filepath, 'r') as f:
                    self.__own_data = json.load(f)
            except OSError:
                return None

        return self.__own_data

    def storeOwnData(self, _callback, own_bare_jid: str, own_device_id: int) -> None:
        self.__own_data = {
            'own_bare_jid': own_bare_jid,
            'own_device_id': own_device_id,
        }

        filepath = os.path.join(self.storage_dir, 'own_data.json')
        with open(filepath, 'w') as f:
            json.dump(self.__own_data, f)

    def loadState(self, _callback):
        if self.__state is None:
            try:
                filepath = os.path.join(self.storage_dir, 'omemo.json')
                with open(filepath, 'r') as f:
                    self.__state = json.load(f)
            except OSError:
                return None

        return self.__state

    def storeState(self, _callback, state) -> None:
        self.__state = state
        filepath = os.path.join(self.storage_dir, 'omemo.json')
        with open(filepath, 'w') as f:
            json.dump(self.__state, f)

    def loadSession(self, _callback, bare_jid: str, device_id: int):
        if not self.__sessions:
            try:
                filepath = os.path.join(self.storage_dir, 'sessions.json')
                with open(filepath, 'r') as f:
                    self.__sessions = json.load(f)
            except OSError:
                return None

        return self.__sessions.get(bare_jid, {}).get(device_id, None)

    def storeSession(self, callback, bare_jid: str, device_id: int, session) -> None:
        self.__sessions[bare_jid] = self.__sessions.get(bare_jid, {})
        self.__sessions[bare_jid][device_id] = session

        filepath = os.path.join(self.storage_dir, 'sessions.json')
        with open(filepath, 'w') as f:
            json.dump(self.__sessions, f)

    def deleteSession(self, callback, bare_jid: str, device_id: int) -> None:
        self.__sessions[bare_jid] = {}

        filepath = os.path.join(self.storage_dir, 'sessions.json')
        os.remove(filepath)

    def loadActiveDevices(self, _callback, bare_jid: str) -> Optional[List[int]]:
        if not self.__devices:
            try:
                filepath = os.path.join(self.storage_dir, 'devices.json')
                with open(filepath, 'r') as f:
                    self.__devices = json.load(f)
            except OSError:
                return None

        return self.__devices.get(bare_jid, {}).get("active", [])

    def storeActiveDevices(self, _callback, bare_jid: str, devices: Set[int]) -> None:
        self.__devices[bare_jid] = self.__devices.get(bare_jid, {})
        self.__devices[bare_jid]["active"] = list(devices)

        filepath = os.path.join(self.storage_dir, 'devices.json')
        with open(filepath, 'w') as f:
            json.dump(self.__devices, f)

    def loadInactiveDevices(self, _callback, bare_jid: str) -> Optional[Dict[int, int]]:
        if not self.__devices:
            try:
                filepath = os.path.join(self.storage_dir, 'devices.json')
                with open(filepath, 'r') as f:
                    self.__devices = json.load(f)
            except OSError:
                return None

        return self.__devices.get(bare_jid, {}).get("inactive", {})

    def storeInactiveDevices(self, _callback, bare_jid: str, devices: Dict[int, int]) -> None:
        self.__devices[bare_jid] = self.__devices.get(bare_jid, {})
        self.__devices[bare_jid]["inactive"] = devices

        filepath = os.path.join(self.storage_dir, 'devices.json')
        with open(filepath, 'w') as f:
            json.dump(self.__devices, f)

    def storeTrust(self, _callback, bare_jid: str, device_id: int, trust: Dict[str, Any]) -> None:
        self.__trust[bare_jid] = self.__trust.get(bare_jid, {})
        self.__trust[bare_jid][device_id] = trust

        filepath = os.path.join(self.storage_dir, 'trust.json')
        with open(filepath, 'w') as f:
            json.dump(self.__trust, f)

    def loadTrust(self, _callback, bare_jid: str, device_id: int) -> Optional[Dict[str, Any]]:
        if not self.__trust:
            try:
                filepath = os.path.join(self.storage_dir, 'trust.json')
                with open(filepath, 'r') as f:
                    self.__trust = json.load(f)
            except OSError:
                return None

        return self.__trust.get(bare_jid, {}).get(device_id)

    def listJIDs(self, _callback) -> Set[str]:
        return set(self.__devices.keys())

    def deleteJID(self, _callback, bare_jid: str) -> None:
        self.__session[bare_jid] = {}
        filepath = os.path.join(self.storage_dir, 'sessions.json')
        with open(filepath, 'w') as f:
            json.dump(self.__sessions, f)

        self.__devices[bare_jid] = {}
        filepath = os.path.join(self.storage_dir, 'devices.json')
        with open(filepath, 'w') as f:
            json.dump(self.__devices, f)

        self.__trust[bare_jid] = {}
        filepath = os.path.join(self.storage_dir, 'trust.json')
        with open(filepath, 'w') as f:
            json.dump(self.__trust, f)

    @property
    def is_async(self) -> bool:
        return False
