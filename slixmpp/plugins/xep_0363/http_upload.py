"""
    slixmpp: The Slick XMPP Library
    Copyright (C) 2018 Emmanuel Gil Peyrot
    This file is part of slixmpp.

    See the file LICENSE for copying permission.
"""

import logging
import os.path

from aiohttp import ClientSession
from mimetypes import guess_type

from slixmpp import Iq, __version__
from slixmpp.plugins import BasePlugin
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import StanzaPath
from slixmpp.plugins.xep_0363 import stanza, Request, Slot, Put, Get, Header

log = logging.getLogger(__name__)

class FileUploadError(Exception):
    pass

class UploadServiceNotFound(FileUploadError):
    pass

class FileTooBig(FileUploadError):
    pass

class HTTPError(FileUploadError):
    def __str__(self):
        return 'Could not upload file: %d (%s)' % (self.args[0], self.args[1])

class XEP_0363(BasePlugin):
    ''' This plugin only supports Python 3.5+ '''

    name = 'xep_0363'
    description = 'XEP-0363: HTTP File Upload'
    dependencies = {'xep_0030', 'xep_0128'}
    stanza = stanza
    default_config = {
        'upload_service': None,
        'max_file_size': float('+inf'),
        'default_content_type': 'application/octet-stream',
    }

    def plugin_init(self):
        register_stanza_plugin(Iq, Request)
        register_stanza_plugin(Iq, Slot)
        register_stanza_plugin(Slot, Put)
        register_stanza_plugin(Slot, Get)
        register_stanza_plugin(Put, Header, iterable=True)

        self.xmpp.register_handler(
                Callback('HTTP Upload Request',
                         StanzaPath('iq@type=get/http_upload_request'),
                         self._handle_request))

    def plugin_end(self):
        self._http_session.close()
        self.xmpp.remove_handler('HTTP Upload Request')
        self.xmpp.remove_handler('HTTP Upload Slot')
        self.xmpp['xep_0030'].del_feature(feature=Request.namespace)

    def session_bind(self, jid):
        self.xmpp.plugin['xep_0030'].add_feature(Request.namespace)

    def _handle_request(self, iq):
        self.xmpp.event('http_upload_request', iq)

    async def find_upload_service(self, domain=None, timeout=None):
        results = await self.xmpp['xep_0030'].get_info_from_domain(
            domain=domain, timeout=timeout)

        candidates = []
        for info in results:
            for identity in info['disco_info']['identities']:
                if identity[0] == 'store' and identity[1] == 'file':
                    candidates.append(info)
        for info in candidates:
            for feature in info['disco_info']['features']:
                if feature == Request.namespace:
                    return info

    def request_slot(self, jid, filename, size, content_type=None, ifrom=None,
                     timeout=None, callback=None, timeout_callback=None):
        iq = self.xmpp.Iq()
        iq['to'] = jid
        iq['from'] = ifrom
        iq['type'] = 'get'
        request = iq['http_upload_request']
        request['filename'] = filename
        request['size'] = str(size)
        request['content-type'] = content_type or self.default_content_type
        return iq.send(timeout=timeout, callback=callback,
                       timeout_callback=timeout_callback)

    async def upload_file(self, filename, size=None, content_type=None, *,
                          input_file=None, ifrom=None, domain=None, timeout=None,
                          callback=None, timeout_callback=None):
        ''' Helper function which does all of the uploading process. '''
        if self.upload_service is None:
            info_iq = await self.find_upload_service(
                domain=domain, timeout=timeout)
            if info_iq is None:
                raise UploadServiceNotFound()
            self.upload_service = info_iq['from']
            for form in info_iq['disco_info'].iterables:
                values = form['values']
                if values['FORM_TYPE'] == ['urn:xmpp:http:upload:0']:
                    try:
                        self.max_file_size = int(values['max-file-size'])
                    except (TypeError, ValueError):
                        log.error('Invalid max size received from HTTP File Upload service')
                        self.max_file_size = float('+inf')
                break

        if input_file is None:
            input_file = open(filename, 'rb')

        if size is None:
            size = input_file.seek(0, 2)
            input_file.seek(0)

        if size > self.max_file_size:
            raise FileTooBig()

        if content_type is None:
            content_type = guess_type(filename)[0]
            if content_type is None:
                content_type = self.default_content_type

        basename = os.path.basename(filename)
        slot_iq = await self.request_slot(self.upload_service, basename, size,
                                          content_type, ifrom, timeout,
                                          timeout_callback=timeout_callback)
        slot = slot_iq['http_upload_slot']

        headers = {
            'Content-Length': str(size),
            'Content-Type': content_type or self.default_content_type,
            **{header['name']: header['value'] for header in slot['put']['headers']}
        }

        # Do the actual upload here.
        async with ClientSession(headers={'User-Agent': 'slixmpp ' + __version__}) as session:
            response = await session.put(
                    slot['put']['url'],
                    data=input_file,
                    headers=headers,
                    timeout=timeout)
            if response.status >= 400:
                raise HTTPError(response.status, await response.text())
            log.info('Response code: %d (%s)', response.status, await response.text())
            response.close()
            return slot['get']['url']
