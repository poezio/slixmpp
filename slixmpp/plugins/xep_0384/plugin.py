"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Maxime “pep” Buquet <pep@bouah.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

from typing import Any, Dict, List, Optional, Set, Tuple, Union

import os
import json
import base64
import asyncio
from slixmpp.plugins.xep_0384.stanza import OMEMO_BASE_NS
from slixmpp.plugins.xep_0384.stanza import OMEMO_DEVICES_NS, OMEMO_BUNDLES_NS
from slixmpp.plugins.xep_0384.stanza import Bundle, Devices, Device, Encrypted, Key, PreKeyPublic
from slixmpp.plugins.xep_0060.stanza import Items, EventItems
from slixmpp.plugins.base import BasePlugin
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.stanza import Message, Iq
from slixmpp.jid import JID

log = logging.getLogger(__name__)

HAS_OMEMO = True
try:
    import omemo.exceptions
    from omemo import SessionManager, ExtendedPublicBundle, DefaultOTPKPolicy
    from omemo.util import generateDeviceID
    from omemo.backends import Backend
    from omemo_backend_signal import BACKEND as SignalBackend
    from omemo.implementation import JSONFileStorage
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

    for bare_jid, devices in encrypted['keys'].items():
        for rid, device in devices.items():
            key = Key()
            key['value'] = b64enc(device['data'])
            key['rid'] = str(rid)
            if device['pre_key']:
                key['prekey'] = '1'
            tag['header'].append(key)

    return tag


# XXX: This should probably be moved in plugins/base.py?
class PluginCouldNotLoad(Exception): pass


# Generic exception
class XEP0384(Exception): pass


class MissingOwnKey(XEP0384): pass


class NoAvailableSession(XEP0384): pass


class EncryptionPrepareException(XEP0384): pass


class UntrustedException(XEP0384): pass


class UndecidedException(XEP0384): pass


class XEP_0384(BasePlugin):

    """
    XEP-0384: OMEMO
    """

    name = 'xep_0384'
    description = 'XEP-0384 OMEMO'
    dependencies = {'xep_0163'}
    default_config = {
        'data_dir': None,
        'storage_backend': None,
        'otpk_policy': DefaultOTPKPolicy,
        'omemo_backend': SignalBackend,
    }

    backend_loaded = HAS_OMEMO

    def plugin_init(self) -> None:
        if not self.backend_loaded:
            log.info("xep_0384 cannot be loaded as the backend omemo library "
                     "is not available")
            return None

        if not self.data_dir:
            log.info("xep_0384 canoot be loaded as there is not data directory "
                     "specified")
            return None

        storage = self.storage_backend
        if self.storage_backend is None:
            storage = JSONFileStorage(self.data_dir)

        otpkpolicy = self.otpk_policy
        bare_jid = self.xmpp.boundjid.bare
        self._device_id = _load_device_id(self.data_dir)

        try:
            self._omemo = SessionManager.create(
                storage,
                otpkpolicy,
                self.omemo_backend,
                bare_jid,
                self._device_id,
            )
        except:
            log.error("Couldn't load the OMEMO object; ¯\\_(ツ)_/¯")
            raise PluginCouldNotLoad

        self.xmpp['xep_0060'].map_node_event(OMEMO_DEVICES_NS, 'omemo_device_list')
        self.xmpp.add_event_handler('omemo_device_list_publish', self._receive_device_list)
        return None

    def plugin_end(self):
        if not self.backend_loaded:
            return

        self.xmpp.remove_event_handler('omemo_device_list_publish', self._receive_device_list)
        self.xmpp['xep_0163'].remove_interest(OMEMO_DEVICES_NS)

    def session_bind(self, _jid):
        self.xmpp['xep_0163'].add_interest(OMEMO_DEVICES_NS)
        asyncio.ensure_future(self._set_device_list())
        asyncio.ensure_future(self._publish_bundle())

    def my_device_id(self) -> int:
        return self._device_id

    def _generate_bundle_iq(self) -> Iq:
        bundle = self._omemo.public_bundle.serialize(self._omemo)

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

    async def _fetch_bundle(self, jid: str, device_id: int) -> Optional[ExtendedPublicBundle]:
        node = '%s:%d' % (OMEMO_BUNDLES_NS, device_id)
        try:
            iq = await self.xmpp['xep_0060'].get_items(jid, node)
        except (IqError, IqTimeout):
            return None
        bundle = iq['pubsub']['items']['item']['bundle']

        return _parse_bundle(self._omemo, bundle)

    async def _fetch_device_list(self, jid: JID) -> None:
        """Manually query PEP OMEMO_DEVICES_NS nodes"""
        jid = JID(jid)
        iq = await self.xmpp['xep_0060'].get_items(jid, OMEMO_DEVICES_NS)
        return await self._read_device_list(jid, iq['pubsub']['items'])

    def _store_device_ids(self, jid: str, items: Union[Items, EventItems]) -> None:
        """Store Device list"""
        device_ids = []  # type: List[int]
        items = list(items)
        device_ids = [int(d['id']) for d in items[0]['devices']]
        return self._omemo.newDeviceList(str(jid), device_ids)

    def _receive_device_list(self, msg: Message) -> None:
        """Handler for received PEP OMEMO_DEVICES_NS payloads"""
        asyncio.ensure_future(
            self._read_device_list(msg['from'],
            msg['pubsub_event']['items']),
        )

    async def _read_device_list(self, jid: JID, items: Union[Items, EventItems]) -> None:
        """Read items and devices if we need to set the device list again or not"""
        bare_jid = jid.bare
        self._store_device_ids(bare_jid, items)

        items = list(items)
        device_ids = [int(d['id']) for d in items[0]['devices']]

        if bare_jid == self.xmpp.boundjid.bare and \
           self._device_id not in device_ids:
            await self._set_device_list()

        return None

    async def _set_device_list(self, device_ids: Optional[Set[int]] = None) -> None:
        own_jid = self.xmpp.boundjid

        try:
            iq = await self.xmpp['xep_0060'].get_items(
                own_jid.bare, OMEMO_DEVICES_NS,
            )
            items = iq['pubsub']['items']
            self._store_device_ids(own_jid.bare, items)
        except IqError as iq_err:
            if iq_err.condition == "item-not-found":
                self._store_device_ids(own_jid.bare, [])
            else:
                return  # XXX: Handle this!

        if device_ids is None:
            device_ids = self.get_device_list(own_jid)

        devices = []
        for i in device_ids:
            d = Device()
            d['id'] = str(i)
            devices.append(d)
        payload = Devices()
        payload['devices'] = devices

        await self.xmpp['xep_0060'].publish(
            own_jid.bare, OMEMO_DEVICES_NS, payload=payload,
        )

    def get_device_list(self, jid: JID) -> List[str]:
        """Return active device ids. Always contains our own device id."""
        return self._omemo.getDevices(jid.bare).get('active', [])

    def trust(self, jid: JID, device_id: int, ik: bytes) -> None:
        self._omemo.trust(jid.bare, device_id, ik)

    def distrust(self, jid: JID, device_id: int, ik: bytes) -> None:
        self._omemo.distrust(jid.bare, device_id, ik)

    def is_encrypted(self, msg: Message) -> bool:
        return msg.xml.find('{%s}encrypted' % OMEMO_BASE_NS) is not None

    def decrypt_message(self, msg: Message, allow_untrusted: bool = False) -> Optional[str]:
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
            body = self._omemo.decryptMessage(
                jid,
                sid,
                iv,
                message,
                isPrekeyMessage,
                payload,
                allow_untrusted=allow_untrusted,
            )
            return body
        except (omemo.exceptions.NoSessionException,):
            # This might happen when the sender is sending using a session
            # that we don't know about (deleted session storage, etc.). In
            # this case we can't decrypt the message and it's going to be lost
            # in any case, but we want to tell the user, always.
            raise NoAvailableSession(jid, sid)
        except (omemo.exceptions.UntrustedException,) as e:
            raise UntrustedException(e)
        finally:
            asyncio.ensure_future(self._publish_bundle())

    async def encrypt_message(
        self,
        plaintext: str,
        recipients: List[JID],
        expect_problems: Optional[Dict[JID, List[int]]] = None,
    ) -> Encrypted:
        """
        Returns an encrypted payload to be placed into a message.

        The API for getting an encrypted payload consists of trying first
        and fixing errors progressively. The actual sending happens once the
        application (us) thinks we're good to go.
        """

        recipients = [jid.bare for jid in recipients]
        bundles = {}  # type: Dict[str, Dict[int, ExtendedPublicBundle]]

        old_errors = None  # type: Optional[List[Tuple[Exception, Any, Any]]]
        while True:
            # Try to encrypt and resolve errors until there is no error at all
            # or if we hit the same set of errors.
            errors = []  # type: List[omemo.exceptions.OMEMOException]

            if expect_problems is not None:
                expect_problems = {jid.bare: did for (jid, did) in expect_problems.items()}

            try:
                encrypted = self._omemo.encryptMessage(
                    recipients,
                    plaintext.encode('utf-8'),
                    bundles,
                    expect_problems=expect_problems,
                )
                return _generate_encrypted_payload(encrypted)
            except omemo.exceptions.EncryptionProblemsException as e:
                errors = e.problems

            if errors == old_errors:
                raise EncryptionPrepareException(errors)

            old_errors = errors

            no_eligible_devices = set()  # type: Set[str]
            for exn in errors:
                if isinstance(exn, omemo.exceptions.NoDevicesException):
                    await self._fetch_device_list(exn.bare_jid)
                elif isinstance(exn, omemo.exceptions.MissingBundleException):
                    bundle = await self._fetch_bundle(exn.bare_jid, exn.device)
                    if bundle is not None:
                        devices = bundles.setdefault(exn.bare_jid, {})
                        devices[exn.device] = bundle
                elif isinstance(exn, omemo.exceptions.UntrustedException):
                    # On UntrustedException, there are two possibilities.
                    # Either trust has not been explicitely set yet, and is
                    # 'undecided', or the device is explicitely not
                    # trusted. When undecided, we need to ask our user to make
                    # a choice. If untrusted, then we can safely tell the
                    # OMEMO lib to not encrypt to this device
                    if self._omemo.getTrustForDevice(exn.bare_jid, exn.device) is None:
                        raise UndecidedException(exn.bare_jid, exn.device, exn.ik)
                    expect_problems.setdefault(exn.bare_jid, []).append(exn.device)
                elif isinstance(exn, omemo.exceptions.NoEligibleDevicesException):
                    # This error is returned by the library to specify that
                    # encryption is not possible to any device of a user.
                    # This always comes with a more specific exception, (empty
                    # device list, missing bundles, trust issues, etc.).
                    # This does the heavy lifting of state management, and
                    # seeing if it's possible to encrypt at all, or not.
                    # This exception is only passed to the user, that should
                    # decide what to do with it, as there isn't much we can if
                    # other issues can't be resolved.
                    continue
