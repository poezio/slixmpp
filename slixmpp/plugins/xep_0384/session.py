import omemo
from slixmpp.plugins.xep_0384.storage import SQLiteDatabase
from omemo.util import generateDeviceID
import base64

class SessionManager:
    def __init__(self, own_jid, db_path):
        # Database Inferface
        self._store = SQLiteDatabase(db_path)
        # OmemoSessionManager
        self._sm = omemo.SessionManager(own_jid, self._store, generateDeviceID())

    def build_session(self, bundle):
        self._store.createSession()

    def get_bundle(self):
        return self._sm.state.getPublicBundle()

    def set_devicelist(self, device_list, jid=None):
        self._sm.newDeviceList(device_list, jid)

    def get_devicelist(self, jid):
        return self._sm.getDevices(jid)

    def get_own_device_id(self):
        return self._sm.__my_device_id

    def get_own_devices(self):
        devices = self._sm.getDevices()['active']
        if self._sm.__my_device_id not in devices:
            devices = list(devices)
            devices.append(self._sm.__my_device_id)
        return devices

    def get_devices_without_session(self, jid):
        return self._store.getDevicesWithoutSession(jid)

    def get_trusted_fingerprints(self, jid):
        return self._store.getTrustedFingerprints(jid)

    def save_bundle(self, jid, device_id, bundle):
        fingerprint = bundle.fingerprint
        self._store.storeBundle(jid, device_id, fingerprint)

    def clear_devicelist(self):
        return

    def encrypt(self, jids, plaintext, bundles=None, devices=None, callback=None):
        return self._sm.encryptMessage(jids, plaintext, bundles, devices, callback)

    def decrypt(self, jid, sid, iv, message, payload, prekey):
        iv = base64.b64decode(iv.get_value())
        payload = base64.b64decode(payload.get_value())
        message = base64.b64decode(message)
        sid = int(sid)
        if prekey:
            return self._sm.decryptMessage(jid, sid, iv, message, payload)
        return self._sm.decryptPreKeyMessage(jid, sid, iv, message, payload)

    def buid_session(self, jid, device, bundle, callback):
        return self._sm.buildSession(jid, device, bundle, callback)
