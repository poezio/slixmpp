# -*- coding: utf-8 -*-
# cython: language_level = 3
# distutils: libraries = idn
"""
    slixmpp.stringprep
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module wraps libidn’s stringprep and idna functions using Cython.

    Part of Slixmpp: The Slick XMPP Library

    :copyright: (c) 2015 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
    :license: MIT, see LICENSE for more details
"""

from libc.stdlib cimport free


# Those are Cython declarations for the C function we’ll be using.

cdef extern from "stringprep.h" nogil:
    int stringprep_profile(const char* in_, char** out, const char* profile,
                           int flags)

cdef extern from "idna.h" nogil:
    int idna_to_ascii_8z(const char* in_, char** out, int flags)
    int idna_to_unicode_8z8z(const char* in_, char** out, int flags)


class StringprepError(Exception):
    pass


cdef str _stringprep(str in_, const char* profile):
    """Python wrapper for libidn’s stringprep."""
    cdef char* out
    ret = stringprep_profile(in_.encode('utf-8'), &out, profile, 0)
    if ret != 0:
        raise StringprepError(ret)
    unicode_out = out.decode('utf-8')
    free(out)
    return unicode_out


def nodeprep(str node):
    """The nodeprep profile of stringprep used to validate the local, or
    username, portion of a JID."""
    return _stringprep(node, 'Nodeprep')


def resourceprep(str resource):
    """The resourceprep profile of stringprep, which is used to validate the
    resource portion of a JID."""
    return _stringprep(resource, 'Resourceprep')


def idna(str domain):
    """The idna conversion functions, which are used to validate the domain
    portion of a JID."""

    cdef char* ascii_domain
    cdef char* utf8_domain

    ret = idna_to_ascii_8z(domain.encode('utf-8'), &ascii_domain, 0)
    if ret != 0:
        raise StringprepError(ret)

    ret = idna_to_unicode_8z8z(ascii_domain, &utf8_domain, 0)
    free(ascii_domain)
    if ret != 0:
        raise StringprepError(ret)

    unicode_domain = utf8_domain.decode('utf-8')
    free(utf8_domain)
    return unicode_domain


def punycode(str domain):
    """Converts a domain name to its punycode representation."""

    cdef char* ascii_domain
    cdef bytes bytes_domain

    ret = idna_to_ascii_8z(domain.encode('utf-8'), &ascii_domain, 0)
    if ret != 0:
        raise StringprepError(ret)
    bytes_domain = ascii_domain
    free(ascii_domain)
    return bytes_domain
