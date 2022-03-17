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
from io import BufferedReader, BytesIO

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from slixmpp.plugins import BasePlugin
from slixmpp.plugins.base import register_plugin


class InvalidURLScheme(Exception):
    """Raised for non-HTTPS URLS"""


class XEP_0454(BasePlugin):
    """
        XEP-0454: OMEMO Media Sharing
    """

    name = 'xep_0454'
    description = 'XEP-0454: OMEMO Media Sharing'

    @classmethod
    def encrypt(cls, input_file: Optional[IO[bytes]], filename: Path) -> Tuple[BytesIO, str]:
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
            backend=default_backend(),
        ).encryptor()

        if input_file:
            plain = input_file.read()
        else:
            with filename.open(mode='rb') as file:
                plain = file.read()

        data = aes_gcm.update(plain.read() + aes_gcm.tag) + aes_gcm.finalize()

        payload = BytesIO(data)
        anchor = aes_gcm_iv.hex() + aes_gcm_key.hex()
        return (payload, anchor)

    @classmethod
    def format_url(cls, url: str, anchor: str) -> str:
        """Helper to format a HTTPS URL to an AESGCM URI"""
        if not url.startswith('https://'):
            raise InvalidURLScheme
        url = 'aesgcm://' + url.removeprefix('https://') + '#' + anchor

register_plugin(XEP_0454)
