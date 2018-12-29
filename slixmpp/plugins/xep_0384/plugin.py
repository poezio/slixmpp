"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Maxime “pep” Buquet <pep@bouah.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from typing import Any, Dict, List, Set, Tuple, Union

import os
import json
import base64
import asyncio
from slixmpp.plugins.xep_0384.stanza import OMEMO_BASE_NS
from slixmpp.plugins.xep_0384.stanza import OMEMO_DEVICES_NS, OMEMO_BUNDLES_NS
from slixmpp.plugins.xep_0384.stanza import Bundle, Devices, Device, Encrypted, Key, PreKeyPublic
from slixmpp.plugins.base import BasePlugin
from slixmpp.exceptions import IqError
from slixmpp.stanza import Message, Iq
from slixmpp.jid import JID

log = logging.getLogger(__name__)

HAS_OMEMO = True
try:
    import omemo.exceptions
    from omemo import SessionManager, ExtendedPublicBundle
    from omemo.util import generateDeviceID
    from omemo.backends import Backend
    from omemo_backend_signal import BACKEND as SignalBackend
    from slixmpp.plugins.xep_0384.storage import SyncFileStorage
    from slixmpp.plugins.xep_0384.otpkpolicy import KeepingOTPKPolicy
except (ImportError,):
    HAS_OMEMO = False

TRUE_VALUES = {True, 'true', '1'}


def b64enc(data: bytes) -> str:
    return base64.b64encode(bytes(bytearray(data))).decode('ASCII')


def b64dec(data: str) -> bytes:
    return base64.b64decode(data)


def _load_device_id(data_dir: str) -> int:
    filepath = os.path.join(data_dir, 'device_id.json')
    # Try reading file first, decoding, and if file was empty generate
    # new DeviceID
    try:
        with open(filepath, 'r') as f:
            did = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        did = generateDeviceID()
        with open(filepath, 'w') as f:
            json.dump(did, f)

    return did


def _parse_bundle(backend: Backend, bundle: Bundle) -> ExtendedPublicBundle:
    identity_key = b64dec(bundle['identityKey']['value'].strip())
    spk = {
        'id': int(bundle['signedPreKeyPublic']['signedPreKeyId']),
        'key': b64dec(bundle['signedPreKeyPublic']['value'].strip()),
    }
    spk_signature = b64dec(bundle['signedPreKeySignature']['value'].strip())

    otpks = []
    for prekey in bundle['prekeys']:
        otpks.append({
            'id': int(prekey['preKeyId']),
            'key': b64dec(prekey['value'].strip()),
        })

    return ExtendedPublicBundle.parse(backend, identity_key, spk, spk_signature, otpks)


def _generate_encrypted_payload(encrypted) -> Encrypted:
    tag = Encrypted()

    tag['header']['sid'] = str(encrypted['sid'])
    tag['header']['iv']['value'] = b64enc(encrypted['iv'])
    tag['payload']['value'] = b64enc(encrypted['payload'])

    for message in encrypted['messages']:
        key = Key()
        key['value'] = b64enc(message['message'])
        key['rid'] = str(message['rid'])
        if message['pre_key']:
            key['prekey'] = '1'
        tag['header'].append(key)

    return tag


# XXX: This should probably be moved in plugins/base.py?
class PluginCouldNotLoad(Exception): pass


# Generic exception
class XEP0384(Exception): pass


class MissingOwnKey(XEP0384): pass


class NoAvailableSession(XEP0384): pass


class NoEligibleDevices(XEP0384): pass


class EncryptionPrepareException(XEP0384): pass


class XEP_0384(BasePlugin):

    """
    XEP-0384: OMEMO
    """

    name = 'xep_0384'
    description = 'XEP-0384 OMEMO'
    dependencies = {'xep_0163'}
    default_config = {
        'data_dir': None,
    }

    backend_loaded = HAS_OMEMO

    def plugin_init(self):
        if not self.backend_loaded:
            log.info("xep_0384 cannot be loaded as the backend omemo library "
                     "is not available")
            return

        storage = SyncFileStorage(self.data_dir)
        otpkpolicy = KeepingOTPKPolicy()
        self._omemo_backend = SignalBackend
        bare_jid = self.xmpp.boundjid.bare
        self._device_id = _load_device_id(self.data_dir)

        try:
            self._omemo = SessionManager.create(
                storage,
                otpkpolicy,
                self._omemo_backend,
                bare_jid,
                self._device_id,
            )
        except:
            log.error("Couldn't load the OMEMO object; ¯\\_(ツ)_/¯")
            raise PluginCouldNotLoad

        self.xmpp['xep_0060'].map_node_event(OMEMO_DEVICES_NS, 'omemo_device_list')
        self.xmpp.add_event_handler('omemo_device_list_publish', self._receive_device_list)
        asyncio.ensure_future(self._set_device_list())
        asyncio.ensure_future(self._publish_bundle())

    def plugin_end(self):
        if not self.backend_loaded:
            return

        self.xmpp.remove_event_handler('omemo_device_list_publish', self._receive_device_list)
        self.xmpp['xep_0163'].remove_interest(OMEMO_DEVICES_NS)

    def session_bind(self, _jid):
        self.xmpp['xep_0163'].add_interest(OMEMO_DEVICES_NS)

    def my_device_id(self) -> int:
        return self._device_id

    def _generate_bundle_iq(self) -> Iq:
        bundle = self._omemo.public_bundle.serialize(self._omemo_backend)

        iq = self.xmpp.Iq(stype='set')
        publish = iq['pubsub']['publish']
        publish['node'] = '%s:%d' % (OMEMO_BUNDLES_NS, self._device_id)
        payload = publish['item']['bundle']
        signedPreKeyPublic = b64enc(bundle['spk']['key'])
        payload['signedPreKeyPublic']['value'] = signedPreKeyPublic
        payload['signedPreKeyPublic']['signedPreKeyId'] = str(bundle['spk']['id'])
        payload['signedPreKeySignature']['value'] = b64enc(
            bundle['spk_signature']
        )
        identityKey = b64enc(bundle['ik'])
        payload['identityKey']['value'] = identityKey

        prekeys = []
        for otpk in bundle['otpks']:
            prekey = PreKeyPublic()
            prekey['preKeyId'] = str(otpk['id'])
            prekey['value'] = b64enc(otpk['key'])
            prekeys.append(prekey)
        payload['prekeys'] = prekeys

        return iq

    async def _publish_bundle(self) -> None:
        if self._omemo.republish_bundle:
            iq = self._generate_bundle_iq()
            await iq.send()

    async def _fetch_bundle(self, jid: str, device_id: int) -> Union[None, ExtendedPublicBundle]:
        node = '%s:%d' % (OMEMO_BUNDLES_NS, device_id)
        iq = await self.xmpp['xep_0060'].get_items(jid, node)
        bundle = iq['pubsub']['items']['item']['bundle']

        return _parse_bundle(self._omemo_backend, bundle)

    def _store_device_ids(self, jid: str, items) -> None:
        device_ids = []  # type: List[int]
        for item in items:
            device_ids = [int(d['id']) for d in item['devices']]

            # XXX: There should only be one item so this is fine, but slixmpp
            # loops forever otherwise. ???
            break
        return self._omemo.newDeviceList(device_ids, str(jid))

    def _receive_device_list(self, msg: Message) -> None:
        if msg['pubsub_event']['items']['node'] != OMEMO_DEVICES_NS:
            return

        jid = msg['from'].bare
        items = msg['pubsub_event']['items']
        self._store_device_ids(jid, items)

        device_ids = self.get_device_list(jid)
        active_devices = device_ids['active']

        if jid == self.xmpp.boundjid.bare and \
           self._device_id not in active_devices:
            asyncio.ensure_future(self._set_device_list())

    async def _set_device_list(self) -> None:
        jid = self.xmpp.boundjid.bare

        try:
            iq = await self.xmpp['xep_0060'].get_items(
                self.xmpp.boundjid.bare, OMEMO_DEVICES_NS,
            )
            items = iq['pubsub']['items']
            self._store_device_ids(jid, items)
        except IqError as iq_err:
            if iq_err.condition == "item-not-found":
                self._store_device_ids(jid, [])
            else:
                return  # XXX: Handle this!

        device_ids = self.get_device_list(jid)

        # Verify that this device in the list and set it if necessary
        if self._device_id in device_ids:
            return

        device_ids['active'].add(self._device_id)

        devices = []
        for i in device_ids['active']:
            d = Device()
            d['id'] = str(i)
            devices.append(d)
        payload = Devices()
        payload['devices'] = devices

        await self.xmpp['xep_0060'].publish(
            jid, OMEMO_DEVICES_NS, payload=payload,
        )

    def get_device_list(self, jid: str) -> List[str]:
        # XXX: Maybe someday worry about inactive devices somehow
        return  self._omemo.getDevices(jid)

    def is_encrypted(self, msg: Message) -> bool:
        return msg.xml.find('{%s}encrypted' % OMEMO_BASE_NS) is not None

    def decrypt_message(self, msg: Message) -> Union[None, str]:
        header = msg['omemo_encrypted']['header']
        payload = b64dec(msg['omemo_encrypted']['payload']['value'])

        jid = msg['from'].bare
        sid = int(header['sid'])

        key = header.xml.find("{%s}key[@rid='%s']" % (
            OMEMO_BASE_NS, self._device_id))
        if key is None:
            raise MissingOwnKey("Encrypted message is not for us")

        key = Key(key)
        isPrekeyMessage = key['prekey'] in TRUE_VALUES
        message = b64dec(key['value'])
        iv = b64dec(header['iv']['value'])

        # XXX: 'cipher' is part of KeyTransportMessages and is used when no payload
        # is passed. We do not implement this yet.
        try:
            _cipher, body = self._omemo.decryptMessage(
                jid,
                sid,
                iv,
                message,
                isPrekeyMessage,
                payload,
            )
            return body
        except (omemo.exceptions.NoSessionException,):
            # This might happen when the sender is sending using a session
            # that we don't know about (deleted session storage, etc.). In
            # this case we can't decrypt the message and it's going to be lost
            # in any case, but we want to tell the user, always.
            raise NoAvailableSession(jid, sid)
        finally:
            asyncio.ensure_future(self._publish_bundle())

    def _fetching_bundle(self, jid: str, exn: Exception, key: str, _val: Any) -> bool:
        return isinstance(exn, omemo.exceptions.MissingBundleException) and key == jid

    async def encrypt_message(self, plaintext: str, recipients: List[JID]) -> Encrypted:
        """
        Returns an encrypted payload to be placed into a message.

        The API for getting an encrypted payload consists of trying first
        and fixing errors progressively. The actual sending happens once the
        application (us) thinks we're good to go.
        """

        recipients = [jid.bare for jid in recipients]
        bundles = {}  # type: Dict[str, Dict[int, ExtendedPublicBundle]]

        old_errors = None  # type: Union[None, List[Tuple[Exception, Any, Any]]]
        while True:
            # Try to encrypt and resolve errors until there is no error at all
            # or if we hit the same set of errors.
            errors = []

            self._omemo.encryptMessage(
                recipients,
                plaintext.encode('utf-8'),
                bundles,
                callback=lambda *args: errors.append(args),
                always_trust=True,
                dry_run=True,
            )

            if not errors:
                break

            if errors == old_errors:
                raise EncryptionPrepareException

            old_errors = errors

            no_eligible_devices = set()  # type: Set[str]
            for (exn, key, val) in errors:
                if isinstance(exn, omemo.exceptions.MissingBundleException):
                    bundle = await self._fetch_bundle(key, val)
                    if bundle is not None:
                        devices = bundles.setdefault(key, {})
                        devices[val] = bundle
                elif isinstance(exn, omemo.exceptions.NoEligibleDevicesException):
                    # This error is apparently returned every time the omemo
                    # lib couldn't find a device to encrypt to for a
                    # particular JID.
                    # In case there is also an MissingBundleException in the
                    # returned errors, ignore this and retry later, assuming
                    # the fetching of the bundle succeeded. TODO: Ensure that it
                    # did.
                    # This exception is mostly useful when a contact does not
                    # do OMEMO, or hasn't published any device list for any
                    # other reason.

                    if any(self._fetching_bundle(key, *err) for err in errors):
                        continue

                    no_eligible_devices.add(key)

            if no_eligible_devices:
                raise NoEligibleDevices(no_eligible_devices)

        # Attempt encryption
        encrypted = self._omemo.encryptMessage(
            recipients,
            plaintext.encode('utf-8'),
            bundles,
            always_trust=True,
        )
        return _generate_encrypted_payload(encrypted)
