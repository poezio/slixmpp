#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from getpass import getpass
from argparse import ArgumentParser

import slixmpp
from slixmpp.xmlstream import ET, tostring
from slixmpp.xmlstream.asyncio import asyncio

def make_callback():
    future = asyncio.Future()
    def callback(result):
        future.set_result(result)
    return future, callback

class PubsubClient(slixmpp.ClientXMPP):

    def __init__(self, jid, password, server,
                       node=None, action='list', data=''):
        super(PubsubClient, self).__init__(jid, password)

        self.register_plugin('xep_0030')
        self.register_plugin('xep_0059')
        self.register_plugin('xep_0060')

        self.actions = ['nodes', 'create', 'delete',
                        'publish', 'get', 'retract',
                        'purge', 'subscribe', 'unsubscribe']

        self.action = action
        self.node = node
        self.data = data
        self.pubsub_server = server

        self.add_event_handler('session_start', self.start)

    def start(self, event):
        self.get_roster()
        self.send_presence()

        try:
            getattr(self, self.action)()
        except:
            logging.error('Could not execute: %s' % self.action)
        self.disconnect()

    def nodes(self):
        future, callback = make_callback()
        try:
            self['xep_0060'].get_nodes(self.pubsub_server, self.node, callback=callback)
            result = yield from future
            for item in result['disco_items']['items']:
                print('  - %s' % str(item))
        except:
            logging.error('Could not retrieve node list.')

    def create(self):
        try:
            self['xep_0060'].create_node(self.pubsub_server, self.node)
        except:
            logging.error('Could not create node: %s' % self.node)

    def delete(self):
        try:
            self['xep_0060'].delete_node(self.pubsub_server, self.node)
            print('Deleted node: %s' % self.node)
        except:
            logging.error('Could not delete node: %s' % self.node)

    def publish(self):
        payload = ET.fromstring("<test xmlns='test'>%s</test>" % self.data)
        future, callback = make_callback()
        try:
            self['xep_0060'].publish(self.pubsub_server, self.node, payload=payload, callback=callback)
            result = yield from future
            id = result['pubsub']['publish']['item']['id']
            print('Published at item id: %s' % id)
        except:
            logging.error('Could not publish to: %s' % self.node)

    def get(self):
        future, callback = make_callback()
        try:
            self['xep_0060'].get_item(self.pubsub_server, self.node, self.data, callback=callback)
            result = yield from future
            for item in result['pubsub']['items']['substanzas']:
                print('Retrieved item %s: %s' % (item['id'], tostring(item['payload'])))
        except:
            logging.error('Could not retrieve item %s from node %s' % (self.data, self.node))

    def retract(self):
        try:
            self['xep_0060'].retract(self.pubsub_server, self.node, self.data)
            print('Retracted item %s from node %s' % (self.data, self.node))
        except:
            logging.error('Could not retract item %s from node %s' % (self.data, self.node))

    def purge(self):
        try:
            self['xep_0060'].purge(self.pubsub_server, self.node)
            print('Purged all items from node %s' % self.node)
        except:
            logging.error('Could not purge items from node %s' % self.node)

    def subscribe(self):
        try:
            self['xep_0060'].subscribe(self.pubsub_server, self.node)
            print('Subscribed %s to node %s' % (self.boundjid.bare, self.node))
        except:
            logging.error('Could not subscribe %s to node %s' % (self.boundjid.bare, self.node))

    def unsubscribe(self):
        try:
            self['xep_0060'].unsubscribe(self.pubsub_server, self.node)
            print('Unsubscribed %s from node %s' % (self.boundjid.bare, self.node))
        except:
            logging.error('Could not unsubscribe %s from node %s' % (self.boundjid.bare, self.node))




if __name__ == '__main__':
    # Setup the command line arguments.
    parser = ArgumentParser()
    parser.version = '%%prog 0.1'
    parser.usage = "Usage: %%prog [options] <jid> " + \
                             'nodes|create|delete|purge|subscribe|unsubscribe|publish|retract|get' + \
                             ' [<node> <data>]'

    parser.add_argument("-q","--quiet", help="set logging to ERROR",
                        action="store_const",
                        dest="loglevel",
                        const=logging.ERROR,
                        default=logging.ERROR)
    parser.add_argument("-d","--debug", help="set logging to DEBUG",
                        action="store_const",
                        dest="loglevel",
                        const=logging.DEBUG,
                        default=logging.ERROR)

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid",
                        help="JID to use")
    parser.add_argument("-p", "--password", dest="password",
                        help="password to use")

    parser.add_argument("server")
    parser.add_argument("action", choice=["nodes", "create", "delete", "purge", "subscribe", "unsubscribe", "publish", "retract", "get"])
    parser.add_argument("node", nargs='?')
    parser.add_argument("data", nargs='?')

    args = parser.parse_args()

    # Setup logging.
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")

    # Setup the Pubsub client
    xmpp = PubsubClient(args.jid, args.password,
                        server=args.server,
                        node=args.node,
                        action=args.action,
                        data=args.data)

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
