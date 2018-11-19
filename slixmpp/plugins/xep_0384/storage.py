"""
    Slixmpp: The Slick XMPP Library

    Shamelessly inspired from Syndace's python-omemo examples.
"""


import os
import copy
import json
from typing import Any, Dict, List, Set, Union

import omemo


class SyncFileStorage(omemo.Storage):
    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = storage_dir
        self.__state = None
        self.__own_data = None  # type: Union[None, Dict[str, Union[str, int]]]
        self.__sessions = {}  # type: Dict[str, Dict[int, Any]]
        self.__devices = {}  # type: Dict[str, Dict[str, List[int]]]

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

    def loadState(self, callback):
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
        return self.__sessions.get(bare_jid, {}).get(device_id, None)

    def storeSession(self, callback, bare_jid: str, device_id: int, session) -> None:
        self.__sessions[bare_jid] = self.__sessions.get(bare_jid, {})
        self.__sessions[bare_jid][device_id] = session

    def loadActiveDevices(self, _callback, bare_jid: str) -> Union[None, List[int]]:
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

    def loadInactiveDevices(self, _callback, bare_jid: str) -> Union[None, List[int]]:
        if not self.__devices:
            try:
                filepath = os.path.join(self.storage_dir, 'devices.json')
                with open(filepath, 'r') as f:
                    self.__devices = json.load(f)
            except OSError:
                return None

        return self.__devices.get(bare_jid, {}).get("inactive", [])

    def storeInactiveDevices(self, _callback, bare_jid: str, devices: Set[int]) -> None:
        self.__devices[bare_jid] = self.__devices.get(bare_jid, {})
        self.__devices[bare_jid]["inactive"] = list(devices)

        filepath = os.path.join(self.storage_dir, 'devices.json')
        with open(filepath, 'w') as f:
            json.dump(self.__devices, f)

    def trust(self, _trusted: str) -> None:
        """Set somebody as trusted"""

    def isTrusted(self, callback, bare_jid: str, device: int) -> bool:
        return True

    @property
    def is_async(self) -> bool:
        return False
