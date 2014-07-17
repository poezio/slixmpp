#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Nathanael C. Fritz
# All Rights Reserved
#
# This software is licensed as described in the README.rst and LICENSE
# file, which you should have received as part of this distribution.

import sys
import codecs
try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command
# from ez_setup import use_setuptools

from testall import TestCommand
from slixmpp.version import __version__
# if 'cygwin' in sys.platform.lower():
#     min_version = '0.6c6'
# else:
#     min_version = '0.6a9'
#
# try:
#     use_setuptools(min_version=min_version)
# except TypeError:
#     # locally installed ez_setup won't have min_version
#     use_setuptools()
#
# from setuptools import setup, find_packages, Extension, Feature

VERSION          = __version__
DESCRIPTION      = 'Slixmpp is an elegant Python library for XMPP (aka Jabber, Google Talk, etc).'
with codecs.open('README.rst', 'r', encoding='UTF-8') as readme:
    LONG_DESCRIPTION = ''.join(readme)

CLASSIFIERS      = [ 'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2.6',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3.1',
                     'Programming Language :: Python :: 3.2',
                     'Programming Language :: Python :: 3.3',
                     'Topic :: Software Development :: Libraries :: Python Modules',
                   ]

packages     = [ 'slixmpp',
                 'slixmpp/stanza',
                 'slixmpp/test',
                 'slixmpp/roster',
                 'slixmpp/util',
                 'slixmpp/util/sasl',
                 'slixmpp/xmlstream',
                 'slixmpp/xmlstream/matcher',
                 'slixmpp/xmlstream/handler',
                 'slixmpp/plugins',
                 'slixmpp/plugins/xep_0004',
                 'slixmpp/plugins/xep_0004/stanza',
                 'slixmpp/plugins/xep_0009',
                 'slixmpp/plugins/xep_0009/stanza',
                 'slixmpp/plugins/xep_0012',
                 'slixmpp/plugins/xep_0013',
                 'slixmpp/plugins/xep_0016',
                 'slixmpp/plugins/xep_0020',
                 'slixmpp/plugins/xep_0027',
                 'slixmpp/plugins/xep_0030',
                 'slixmpp/plugins/xep_0030/stanza',
                 'slixmpp/plugins/xep_0033',
                 'slixmpp/plugins/xep_0047',
                 'slixmpp/plugins/xep_0048',
                 'slixmpp/plugins/xep_0049',
                 'slixmpp/plugins/xep_0050',
                 'slixmpp/plugins/xep_0054',
                 'slixmpp/plugins/xep_0059',
                 'slixmpp/plugins/xep_0060',
                 'slixmpp/plugins/xep_0060/stanza',
                 'slixmpp/plugins/xep_0065',
                 'slixmpp/plugins/xep_0066',
                 'slixmpp/plugins/xep_0071',
                 'slixmpp/plugins/xep_0077',
                 'slixmpp/plugins/xep_0078',
                 'slixmpp/plugins/xep_0080',
                 'slixmpp/plugins/xep_0084',
                 'slixmpp/plugins/xep_0085',
                 'slixmpp/plugins/xep_0086',
                 'slixmpp/plugins/xep_0091',
                 'slixmpp/plugins/xep_0092',
                 'slixmpp/plugins/xep_0095',
                 'slixmpp/plugins/xep_0096',
                 'slixmpp/plugins/xep_0107',
                 'slixmpp/plugins/xep_0108',
                 'slixmpp/plugins/xep_0115',
                 'slixmpp/plugins/xep_0118',
                 'slixmpp/plugins/xep_0128',
                 'slixmpp/plugins/xep_0131',
                 'slixmpp/plugins/xep_0152',
                 'slixmpp/plugins/xep_0153',
                 'slixmpp/plugins/xep_0172',
                 'slixmpp/plugins/xep_0184',
                 'slixmpp/plugins/xep_0186',
                 'slixmpp/plugins/xep_0191',
                 'slixmpp/plugins/xep_0196',
                 'slixmpp/plugins/xep_0198',
                 'slixmpp/plugins/xep_0199',
                 'slixmpp/plugins/xep_0202',
                 'slixmpp/plugins/xep_0203',
                 'slixmpp/plugins/xep_0221',
                 'slixmpp/plugins/xep_0224',
                 'slixmpp/plugins/xep_0231',
                 'slixmpp/plugins/xep_0235',
                 'slixmpp/plugins/xep_0249',
                 'slixmpp/plugins/xep_0257',
                 'slixmpp/plugins/xep_0258',
                 'slixmpp/plugins/xep_0279',
                 'slixmpp/plugins/xep_0280',
                 'slixmpp/plugins/xep_0297',
                 'slixmpp/plugins/xep_0308',
                 'slixmpp/plugins/xep_0313',
                 'slixmpp/plugins/xep_0319',
                 'slixmpp/plugins/xep_0323',
                 'slixmpp/plugins/xep_0323/stanza',
                 'slixmpp/plugins/xep_0325',
                 'slixmpp/plugins/xep_0325/stanza',
                 'slixmpp/plugins/google',
                 'slixmpp/plugins/google/gmail',
                 'slixmpp/plugins/google/auth',
                 'slixmpp/plugins/google/settings',
                 'slixmpp/plugins/google/nosave',
                 'slixmpp/features',
                 'slixmpp/features/feature_mechanisms',
                 'slixmpp/features/feature_mechanisms/stanza',
                 'slixmpp/features/feature_starttls',
                 'slixmpp/features/feature_bind',
                 'slixmpp/features/feature_session',
                 'slixmpp/features/feature_rosterver',
                 'slixmpp/features/feature_preapproval',
                 'slixmpp/thirdparty',
                 ]

setup(
    name             = "slixmpp",
    version          = VERSION,
    description      = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    author       = 'Nathanael Fritz',
    author_email = 'fritzy [at] netflint.net',
    url          = 'http://github.com/fritzy/Slixmpp',
    license      = 'MIT',
    platforms    = [ 'any' ],
    packages     = packages,
    requires     = [ 'dnspython', 'pyasn1', 'pyasn1_modules' ],
    classifiers  = CLASSIFIERS,
    cmdclass     = {'test': TestCommand}
)
