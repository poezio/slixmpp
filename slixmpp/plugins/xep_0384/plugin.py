"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Maxime “pep” Buquet <pep@bouah.net>
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import logging

import base64
import asyncio
from slixmpp.plugins.xep_0384.stanza import OMEMO_BASE_NS
from slixmpp.plugins.xep_0384.stanza import OMEMO_DEVICES_NS, OMEMO_BUNDLES_NS
from slixmpp.plugins.xep_0384.stanza import Devices, Device, Key, PreKeyPublic
from slixmpp.plugins.base import BasePlugin, register_plugin
from slixmpp.exceptions import IqError

log = logging.getLogger(__name__)

HAS_OMEMO = True
try:
    import omemo
    from slixmpp.plugins.xep_0384.session import SessionManager
except ImportError as e:
    HAS_OMEMO = False

TRUE_VALUES = {True, 'true', '1'}


def b64enc(data):
    return base64.b64encode(bytes(bytearray(data))).decode('ASCII')


def b64dec(data):
    return base64.b64decode(data.decode('ASCII'))


class XEP_0384(BasePlugin):

    """
    XEP-0384: OMEMO
    """

    name = 'xep_0384'
    description = 'XEP-0384 OMEMO'
    dependencies = {'xep_0163'}
    default_config = {
        'cache_dir': None,
    }

    backend_loaded = HAS_OMEMO

    device_ids = {}

    def plugin_init(self):
        if not self.backend_loaded:
            log.debug("xep_0384 cannot be loaded as the backend omemo library "
                      "is not available")
            return

        self._omemo = SessionManager(
            self.xmpp.boundjid,
            self.cache_dir,
        )
        self._device_id = self._omemo.get_own_device_id()

        self.xmpp.add_event_handler('pubsub_publish', self._get_device_list)

        asyncio.ensure_future(self._publish_bundle())
        asyncio.ensure_future(self._set_device_list())

    def plugin_end(self):
        if not self.backend_loaded:
            return

        self.xmpp.del_event_handler('pubsub_publish', self._get_device_list)
        self.xmpp['xep_0163'].remove_interest(OMEMO_DEVICES_NS)

    def session_bind(self, _jid):
        self.xmpp['xep_0163'].add_interest(OMEMO_DEVICES_NS)

    def my_device_id(self):
        return self._device_id

    def _generate_bundle_iq(self):
        bundle = self._omemo.get_bundle()
        log.debug('FOO2 Bundle: %r', bundle.fingerprint)

        iq = self.xmpp.Iq(stype='set')
        publish = iq['pubsub']['publish']
        publish['node'] = '%s:%d' % (OMEMO_BUNDLES_NS, self._device_id)
        payload = publish['item']['bundle']
        signedPreKeyPublic = b64enc(
            omemo.wireformat.encodePublicKey(bundle.spk['key'])
        )
        payload['signedPreKeyPublic']['value'] = signedPreKeyPublic
        payload['signedPreKeyPublic']['signedPreKeyId'] = str(bundle.spk['id'])
        payload['signedPreKeySignature']['value'] = b64enc(
            bundle.spk_signature
        )
        identityKey = b64enc(omemo.wireformat.encodePublicKey(bundle.ik))
        payload['identityKey']['value'] = identityKey

        prekeys = []
        for otpk in bundle.otpks:
            prekey = PreKeyPublic()
            prekey['preKeyId'] = str(otpk['id'])
            prekey['value'] = b64enc(
                omemo.wireformat.encodePublicKey(otpk['key'])
            )
            prekeys.append(prekey)
        payload['prekeys'] = prekeys

        return iq

    async def _publish_bundle(self):
        # TODO: Check if bundle is already available
        # Otherwise publish it
        iq = self._generate_bundle_iq()
        await iq.send()

    async def clear_device_list(self):
        """Clear devicelist for the account"""

        self_id = Device()
        self_id['id'] = str(self._device_id)
        devices = Devices()
        devices['devices'] = [self_id]

        await self.xmpp['xep_0060'].publish(
            self.xmpp.boundjid.bare,
            OMEMO_DEVICES_NS,
            payload=devices,
        )

    def _store_device_ids(self, jid, items):
        self.device_ids[jid] = []
        for item in items:
            device_ids = [int(d['id']) for d in item['devices']]
            self.device_ids[jid] = device_ids

            # XXX: There should only be one item so this is fine, but slixmpp
            # loops forever otherwise. ???
            break

    def _get_device_list(self, msg):
        if msg['pubsub_event']['items']['node'] != OMEMO_DEVICES_NS:
            return

        jid = msg['from'].bare
        items = msg['pubsub_event']['items']
        self._store_device_ids(jid, items)

        if jid == self.xmpp.boundjid.bare and \
           self._device_id not in self.device_ids[jid]:
            asyncio.ensure_future(self._set_device_list())

    async def _set_device_list(self):
        jid = self.xmpp.boundjid.bare

        try:
            iq = await self.xmpp['xep_0060'].get_items(
                self.xmpp.boundjid.bare, OMEMO_DEVICES_NS,
            )
            log.debug("DEVICES %r", iq)
            items = iq['pubsub']['items']
            self._store_device_ids(jid, items)
        except IqError as iq_err:
            if iq_err.condition == "item-not-found":
                log.debug("NO DEVICES")
                self._store_device_ids(jid, [])
            else:
                return  # XXX: Handle this!

        # Verify that this device in the list and set it if necessary
        if self._device_id in self.device_ids.get(jid, []):
            return

        self.device_ids[jid].append(self._device_id)

        devices = []
        for i in self.device_ids[jid]:
            d = Device()
            d['id'] = str(i)
            devices.append(d)
        payload = Devices()
        payload['devices'] = devices

        await self.xmpp['xep_0060'].publish(
            jid, OMEMO_DEVICES_NS, payload=payload,
        )

    def is_encrypted(self, msg):
        return msg.xml.find('{%s}encrypted' % OMEMO_BASE_NS) is not None

    def decrypt_message(self, msg):
        header = msg['omemo_encrypted']['header']
        payload = msg['omemo_encrypted']['payload']

        jid = msg['from'].bare
        sid = header['sid']

        key = header.xml.find("{%s}key[@rid='%s']" % (
            OMEMO_BASE_NS, self._device_id))
        if key is None:
            log.debug("Saw encrypted message that wasn't for me, ignoring.")
            return

        key = Key(key)
        prekey = key['prekey'] in TRUE_VALUES
        message = key['value']
        iv = header['iv']

        return self._omemo.decrypt(jid, sid, iv, message, payload, prekey)


register_plugin(XEP_0384)
