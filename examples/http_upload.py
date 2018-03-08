#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Emmanuel Gil Peyrot
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

import sys

import logging
from getpass import getpass
from argparse import ArgumentParser

import slixmpp
from slixmpp.exceptions import XMPPError, IqError
from slixmpp import asyncio

from urllib.parse import urlparse
from http.client import HTTPConnection, HTTPSConnection
from mimetypes import MimeTypes

log = logging.getLogger(__name__)


class HttpUpload(slixmpp.ClientXMPP):

    """
    A basic client asking an entity if they confirm the access to an HTTP URL.
    """

    def __init__(self, jid, password, recipient, filename):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.recipient = recipient
        self.file = open(filename, 'rb')
        self.size = self.file.seek(0, 2)
        self.file.seek(0)
        self.content_type = MimeTypes().guess_type(filename)[0] or 'application/octet-stream'

        self.add_event_handler("session_start", self.start)

    @asyncio.coroutine
    def start(self, event):
        log.info('Uploading file %s...', self.file.name)

        info_iq = yield from self['xep_0363'].find_upload_service()
        if info_iq is None:
            log.error('No upload service found on this server')
            self.disconnect()
            return

        for form in info_iq['disco_info'].iterables:
            values = form['values']
            if values['FORM_TYPE'] == ['urn:xmpp:http:upload:0']:
                max_file_size = int(values['max-file-size'])
                if self.size > max_file_size:
                    log.error('File size bigger than max allowed')
                    self.disconnect()
                    return
                break
        else:
            log.warn('Impossible to find max-file-size, assuming infinite storage space')

        log.info('Using service %s', info_iq['from'])
        slot_iq = yield from self['xep_0363'].request_slot(
                info_iq['from'], self.file.name, self.size, self.content_type)
        put = slot_iq['http_upload_slot']['put']['url']
        get = slot_iq['http_upload_slot']['get']['url']

        # Now we got the two URLs, we can start uploading the HTTP file.
        put_scheme, put_host, put_path, _, _, _ = urlparse(put)
        Connection = {'http': HTTPConnection, 'https': HTTPSConnection}[put_scheme]
        conn = Connection(put_host)
        conn.putrequest('PUT', put_path)
        for header, value in slot_iq['http_upload_slot']['put']['headers']:
            conn.putheader(header, value)
        conn.putheader('Content-Length', self.size)
        conn.putheader('Content-Type', self.content_type)
        conn.endheaders(self.file.read())
        response = conn.getresponse()
        if response.status >= 400:
            log.error('Failed to upload file: %d %s', response.status, response.reason)
            self.disconnect()
            return

        log.info('Upload success! %d %s', response.status, response.reason)
        if self.content_type.startswith('image/'):
            html = '<body xmlns="http://www.w3.org/1999/xhtml"><img src="%s" alt="Uploaded Image"/></body>' % get
        else:
            html = '<body xmlns="http://www.w3.org/1999/xhtml"><a href="%s">%s</a></body>' % (get, get)

        log.info('Sending file to %s', self.recipient)
        self.send_message(self.recipient, get, mhtml=html)
        self.disconnect()


if __name__ == '__main__':
    # Setup the command line arguments.
    parser = ArgumentParser()
    parser.add_argument("-q","--quiet", help="set logging to ERROR",
                        action="store_const",
                        dest="loglevel",
                        const=logging.ERROR,
                        default=logging.INFO)
    parser.add_argument("-d","--debug", help="set logging to DEBUG",
                        action="store_const",
                        dest="loglevel",
                        const=logging.DEBUG,
                        default=logging.INFO)

    # JID and password options.
    parser.add_argument("-j", "--jid", dest="jid",
                        help="JID to use")
    parser.add_argument("-p", "--password", dest="password",
                        help="password to use")

    # Other options.
    parser.add_argument("-r", "--recipient", required=True,
                        help="Recipient JID")
    parser.add_argument("-f", "--file", required=True,
                        help="File to send")

    args = parser.parse_args()

    # Setup logging.
    logging.basicConfig(level=args.loglevel,
                        format='%(levelname)-8s %(message)s')

    if args.jid is None:
        args.jid = input("Username: ")
    if args.password is None:
        args.password = getpass("Password: ")

    xmpp = HttpUpload(args.jid, args.password, args.recipient, args.file)
    xmpp.register_plugin('xep_0071')
    xmpp.register_plugin('xep_0128')
    xmpp.register_plugin('xep_0363')

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process(forever=False)
