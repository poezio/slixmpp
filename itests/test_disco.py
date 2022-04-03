import asyncio
import unittest
from slixmpp.test.integration import SlixIntegration


class TestDisco(SlixIntegration):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.add_client(
            self.envjid('CI_ACCOUNT1'),
            self.envstr('CI_ACCOUNT1_PASSWORD'),
        )
        self.add_client(
            self.envjid('CI_ACCOUNT2'),
            self.envstr('CI_ACCOUNT2_PASSWORD'),
        )
        self.register_plugins(['xep_0030'])
        await self.connect_clients()

    async def test_features(self):
        """Check we can add, get and delete a feature"""
        self.clients[0]['xep_0030'].add_feature('urn:xmpp:fake:0')
        info = await self.clients[1]['xep_0030'].get_info(
            self.clients[0].boundjid.full
        )
        self.assertIn('urn:xmpp:fake:0', info['disco_info']['features'])
        self.clients[0]['xep_0030'].del_feature(feature='urn:xmpp:fake:0')
        info = await self.clients[1]['xep_0030'].get_info(
            self.clients[0].boundjid.full
        )
        self.assertNotIn('urn:xmpp:fake:0', info['disco_info']['features'])

    async def test_inflight_dedup(self):
        """Check that doing 15 of the same disco request will generate only
        one outgoing stanza"""
        infos = []
        for _ in range(10):
            infos.append(self.clients[1]['xep_0030'].get_info(self.clients[0].boundjid.full))
        res = await asyncio.gather(*infos)
        iq_number = set(i['id'] for i in res)
        self.assertEqual(len(iq_number), 1)


suite = unittest.TestLoader().loadTestsFromTestCase(TestDisco)
