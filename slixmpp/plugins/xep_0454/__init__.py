#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8 et ts=4 sts=4 sw=4
#
# Copyright © 2022 Maxime “pep” Buquet <pep@bouah.net>
#
# See the LICENSE file for copying permissions.

"""
    XEP-0454: OMEMO Media Sharing
"""

from typing import IO, Optional, Tuple

from os import urandom
from pathlib import Path
from io import BytesIO, SEEK_END

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from slixmpp.plugins import BasePlugin
from slixmpp.plugins.base import register_plugin


class InvalidURL(Exception):
    """Raised for URLs that either aren't HTTPS or already contain a fragment."""


class XEP_0454(BasePlugin):
    """
        XEP-0454: OMEMO Media Sharing
    """

    name = 'xep_0454'
    description = 'XEP-0454: OMEMO Media Sharing'
    dependencies = {'xep_0363'}

    @classmethod
    def encrypt(cls, input_file: Optional[IO[bytes]] = None, filename: Optional[Path] = None) -> Tuple[bytes, str]:
        """
            Encrypts file as specified in XEP-0454 for use in file sharing

            :param input_file: Binary file stream on the file.
            :param filename: Path to the file to upload.

            One of input_file or filename must be specified. If both are
            passed, input_file will be used and filename ignored.
        """
        aes_gcm_iv = urandom(12)
        aes_gcm_key = urandom(32)

        aes_gcm = Cipher(
            algorithms.AES(aes_gcm_key),
            modes.GCM(aes_gcm_iv),
        ).encryptor()

        if not input_file:
            input_file = open(filename, 'rb')

        payload = b''
        while True:
            buf = input_file.read(4096)
            if not buf:
                break
            payload += aes_gcm.update(buf)

        aes_gcm.finalize()
        payload += aes_gcm.tag
        fragment = aes_gcm_iv.hex() + aes_gcm_key.hex()
        return (payload, fragment)

    @classmethod
    def decrypt(cls, input_file: IO[bytes], fragment: str) -> bytes:
        """
            Decrypts file-like.

            :param input_file: Binary file stream on the file, containing the
                               tag (16 bytes) at the end.
            :param fragment: 88 hex chars string composed of iv (24 chars)
                             + key (64 chars).
        """

        assert len(fragment) == 88
        aes_gcm_iv = bytes.fromhex(fragment[:24])
        aes_gcm_key = bytes.fromhex(fragment[24:])

        # Find 16 bytes tag
        input_file.seek(-16, SEEK_END)
        tag = input_file.read()

        aes_gcm = Cipher(
            algorithms.AES(aes_gcm_key),
            modes.GCM(aes_gcm_iv, tag),
        ).decryptor()

        size = input_file.seek(0, SEEK_END)
        input_file.seek(0)

        count = size - 16
        plain = b''
        while count >= 0:
            buf = input_file.read(4096)
            count -= len(buf)
            if count <= 0:
                buf += input_file.read()
                buf = buf[:-16]
            plain += aes_gcm.update(buf)
        plain += aes_gcm.finalize()

        return plain

    @classmethod
    def format_url(cls, url: str, fragment: str) -> str:
        """Helper to format a HTTPS URL to an AESGCM URI"""
        if not url.startswith('https://') or url.find('#') != -1:
            raise InvalidURL
        url = 'aesgcm://' + url.removeprefix('https://') + '#' + fragment

    async def upload_file(self, **kwargs) -> str:
        """
            Wrapper to xep_0363 (HTTP Upload)'s upload_file method.

            :param input_file: Binary file stream on the file.
            :param filename: Path to the file to upload.

            Same as `XEP_0454.encrypt`, one of input_file or filename must be
            specified. If both are passed, input_file will be used and
            filename ignored.

            Other arguments passed in are passed to the actual
            `XEP_0363.upload_file` call.
        """
        input_file = kwargs.get('input_file')
        filename = kwargs.get('filename')

        payload, fragment = self.encrypt(input_file, filename)

        # Prepare kwargs for upload_file call
        filename = urandom(12).hex()  # Random filename to hide user-provided path
        kwargs['filename'] = filename

        input_enc = BytesIO(payload)
        kwargs['input_file'] = input_enc

        # Size must also be overriden if provided
        size = input_enc.seek(0, SEEK_END)
        input_enc.seek(0)
        kwargs['size'] = size

        url = await self['xep_0363'].upload_file(**kwargs)
        return self.format_url(url, fragment)

register_plugin(XEP_0454)
