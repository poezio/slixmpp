# -*- coding: utf-8 -*-
"""
    slixmpp.util
    ~~~~~~~~~~~~~~

    Part of Slixmpp: The Slick XMPP Library

    :copyright: (c) 2012 Nathanael C. Fritz, Lance J.T. Stout
    :license: MIT, see LICENSE for more details
"""


from slixmpp.util.misc_ops import bytes, unicode, hashes, hash, \
                                    num_to_bytes, bytes_to_num, quote, \
                                    XOR


# =====================================================================
# Standardize import of Queue class:

try:
    import queue
except ImportError:
    import Queue as queue
Queue = queue.Queue

QueueEmpty = queue.Empty
