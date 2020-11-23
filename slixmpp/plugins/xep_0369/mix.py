"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2020 "Mathieu Pasquet <mathieui@mathieui.net>"
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""
from typing import (
    List,
    Optional,
    Set,
    Tuple,
)

from slixmpp import JID, Iq
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.plugins import BasePlugin
from slixmpp.plugins.xep_0369 import stanza


BASE_NODES = [
    'urn:xmpp:mix:nodes:messages',
    'urn:xmpp:mix:nodes:participants',
    'urn:xmpp:mix:nodes:info',
]


class XEP_0369(BasePlugin):
    '''XEP-0369: MIX-CORE'''

    name = 'xep_0369'
    description = 'MIX-CORE'
    dependencies = {'xep_0030', 'xep_0060', 'xep_0004'}
    stanza = stanza
    namespace = stanza.NS

    def plugin_init(self) -> None:
        stanza.register_plugins()

    def session_bind(self, jid):
        self.xmpp.plugin['xep_0030'].add_feature(stanza.NS)

    def plugin_end(self):
        self.xmpp.plugin['xep_0030'].del_feature(feature=stanza.NS)

    async def get_channel_info(self, channel: JID):
        """"
        Get the contents of the channel info node.
        :param JID channel: The MIX channel
        :returns: a dict containing the last modified time and form contents
            (Name, Description, Contact per the spec, YMMV)
        """
        info = await self.xmpp['xep_0060'].get_items(channel, 'urn:xmpp:mix:nodes:info')
        for item in info['pubsub']['items']:
            time = item['id']
            fields = item['form'].get_values()
            del fields['FORM_TYPE']
            fields['modified'] = time
            return fields

    async def join_channel(self, room: JID, nick: str, subscribe: Set[str], *,
                           ifrom: Optional[JID] = None, **iqkwargs) -> Set[str]:
        """
        Join a MIX channel.

        :param JID room: JID of the MIX channel
        :param str nick: Desired nickname on that channel
        :param Set[str] subscribe: Set of notes to subscribe to when joining.
            If empty, all nodes will be subscribed by default.

        :rtype: Set[str]
        :return: The nodes that failed to subscribe, if any
        """
        if not subscribe:
            subscribe = set(BASE_NODES)
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        iq['mix_join']['nick'] = nick
        for node in subscribe:
            sub = stanza.Subscribe()
            sub['node'] = node
            iq['mix_join']['subscribe'].append(sub)
        try:
            result = await iq.send(**iqkwargs)
            result_nodes = {sub['node'] for sub in result['mix_join']}
        except (IqError, IqTimeout) as exc:
            raise exc
        return result_nodes.difference(subscribe)


    async def update_subscription(self, room: JID, subscribe: Optional[Set[str]] = None,
                                  unsubscribe: Optional[Set[str]] = None,
                                  ifrom: Optional[JID] = None, **iqkwargs) -> Tuple[bool, Tuple[Set[str], Set[str]]]:
        """
        Update a MIX channel subscription.

        :param JID room: JID of the MIX channel
        :param Set[str] subscribe: Set of notes to subscribe to additionally.
        :param Set[str] unsubscribe: Set of notes to unsubscribe from.
        :rtype: Tuple[Set[str], Set[str]]
        :return: A tuple containing the set of nodes that failed to subscribe
            and the set of nodes that failed to unsubscribe.
        """
        if not subscribe and not unsubscribe:
            raise ValueError("No nodes were provided.")
        unsubscribe = unsubscribe or set()
        subscribe = subscribe or set()
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        iq.enable('mix_updatesub')
        for node in subscribe:
            sub = stanza.Subscribe()
            sub['node'] = node
            iq['mix_updatesub'].append(sub)
        for node in unsubscribe:
            unsub = stanza.Unsubscribe()
            unsub['node'] = node
            iq['mix_updatesub'].append(unsub)
        result = await iq.send(**iqkwargs)
        result_sub = set()
        result_unsub = set()
        for item in result['mix_updatesub']:
            if isinstance(item, stanza.Subscribe):
                result_sub.add(item['node'])
            elif isinstance(item, stanza.Unsubscribe):
                result_unsub.add(item['node'])
        if (subscribe, unsubscribe) == (result_sub, result_unsub):
            return (set(), set())
        return (
            subscribe.difference(result_sub),
            unsubscribe.difference(result_unsub),
        )

    async def leave_channel(self, room: JID, *,
                            ifrom: Optional[JID] = None, **iqkwargs) -> Iq:
        """"
        Leave a MIX channel
        :param JID room: JID of the channel to leave
        """
        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        iq.enable('mix_leave')
        return await iq.send(**iqkwargs)

    async def set_nick(self, room: JID, nick: str, *,
                       ifrom: Optional[JID] = None, **iqkwargs) -> str:
        """
        Set your nick on a channel. The returned nick MAY be different
        from the one provided, depending on service configuration.
        :param JID jid: MIX channel JID
        :param str nick: desired nick
        :rtype: str
        :return: The nick saved on the MIX channel
        """

        iq = self.xmpp.make_iq_set(ito=room, ifrom=ifrom)
        iq['mix_setnick']['nick'] = nick
        result = await iq.send(**iqkwargs)
        result_nick = result['mix_setnick']['nick']
        return result_nick

    async def can_create_channel(self, service: JID) -> bool:
        """
        Check if the current user can create a channel on the MIX service

        :param JID service: MIX service jid
        :rtype: bool
        """
        results_stanza = await self.xmpp['xep_0030'].get_info(service.server)
        features = results_stanza['disco_info']['features']
        return 'urn:xmpp:mix:core:1#create-channel' in features

    async def create_channel(self, service: JID, channel: Optional[str] = None, *,
                             ifrom: Optional[JID] = None, **iqkwargs) -> str:
        """
        Create a MIX channel.

        :param JID service: MIX service JID
        :param Optional[str] channel: Channel name (or leave empty to let
            the service generate it)
        :returns: The channel name, as created by the service
        """
        if '#' in channel:
            raise ValueError("A channel name cannot contain hashes")
        iq = self.xmpp.make_iq_set(ito=service.server, ifrom=ifrom)
        iq.enable('mix_create')
        if channel is not None:
            iq['mix_create']['channel'] = channel
        result = await iq.send(**iqkwargs)
        return result['mix_create']['channel']

    async def destroy_channel(self, service: JID, channel: str, *,
                              ifrom: Optional[JID] = None, **iqkwargs) -> Iq:
        """
        Destroy a MIX channel.

        :param JID service: MIX service JID
        :param str channel: Channel name
        """
        iq = self.xmpp.make_iq_set(ito=service, ifrom=ifrom)
        iq['mix_destroy'] = channel
        return await iq.send(**iqkwargs)

    async def list_mix_nodes(self, channel: JID,
                             ifrom: Optional[JID] = None, **discokwargs) -> Set[str]:
        """
        List mix nodes for a channel.

        :param JID channel: The MIX channel
        :returns: List of nodes available
        """
        result = await self.xmpp['xep_0030'].get_items(
            channel,
            node='mix',
            ifrom=ifrom,
            **discokwargs,
        )
        nodes = set()
        for item in result['disco_items']:
            nodes.add(item['node'])
        return nodes

    async def list_participants(self, channel: JID, *,
                                ifrom: Optional[JID] = None, **pubsubkwargs) -> List[Tuple[str, str, JID]]:
        """
        List the participants of a MIX channel
        :param JID channel: The MIX channel

        :returns: A list of tuples containing the participant id, nick, and jid (if available)
        """
        info = await self.xmpp['xep_0060'].get_items(
            channel,
            'urn:xmpp:mix:nodes:participants',
            ifrom=ifrom,
            **pubsubkwargs
        )
        participants = list()
        for item in info['pubsub']['items']:
            identifier = item['id']
            nick = item['mix_participant']['nick']
            jid = item['mix_participant']['jid']
            participants.append(
                (identifier, nick, jid),
            )
        return participants

    async def list_channels(self, service: JID, *,
            ifrom: Optional[JID] =None, **discokwargs) -> List[Tuple[JID, str]]:
        """
        List the channels on a MIX service

        :param JID service: MIX service JID
        :returns: A list of rooms with their JID and name
        """
        results_stanza = await self.xmpp['xep_0030'].get_items(
            service.server,
            **discokwargs,
        )
        results = []
        for result in results_stanza['disco_items']:
            results.append((result['jid'], result['name']))
        return results
