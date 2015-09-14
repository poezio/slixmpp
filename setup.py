#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Nathanael C. Fritz
# All Rights Reserved
#
# This software is licensed as described in the README.rst and LICENSE
# file, which you should have received as part of this distribution.

from pathlib import Path
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

try:
    from Cython.Build import cythonize
except ImportError:
    print('Cython not found, falling back to the slow stringprep module.')
    ext_modules = None
else:
    ext_modules = cythonize('slixmpp/stringprep.pyx')

from run_tests import TestCommand
from slixmpp.version import __version__

VERSION = __version__
DESCRIPTION = ('Slixmpp is an elegant Python library for XMPP (aka Jabber, '
               'Google Talk, etc).')
with open('README.rst', encoding='utf8') as readme:
    LONG_DESCRIPTION = readme.read()

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.4',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

packages = [str(mod.parent) for mod in Path('slixmpp').rglob('__init__.py')]

setup(
    name="slixmpp",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Florent Le Coz',
    author_email='louiz@louiz.org',
    url='https://dev.louiz.org/projects/slixmpp',
    license='MIT',
    platforms=['any'],
    packages=packages,
    ext_modules=ext_modules,
    install_requires=['aiodns>=1.0', 'pyasn1', 'pyasn1_modules'],
    classifiers=CLASSIFIERS,
    cmdclass={'test': TestCommand}
)
