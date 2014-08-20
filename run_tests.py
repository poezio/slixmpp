#!/usr/bin/env python3

import sys
import logging
import unittest

from argparse import ArgumentParser
from distutils.core import Command
from importlib import import_module
from pathlib import Path


def run_tests(filenames=None):
    """
    Find and run all tests in the tests/ directory.

    Excludes live tests (tests/live_*).
    """
    if not filenames:
        filenames = [i for i in Path('tests').glob('test_*')]
    else:
        filenames = [Path(i) for i in filenames]

    modules = ['.'.join(test.parts[:-1] + (test.stem,)) for test in filenames]

    suites = []
    for filename in modules:
        module = import_module(filename)
        suites.append(module.suite)

    tests = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)

    # Disable logging output
    logging.basicConfig(level=100)
    logging.disable(100)

    result = runner.run(tests)
    return result


# Add a 'test' command for setup.py

class TestCommand(Command):

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        run_tests()


if __name__ == '__main__':
    parser = ArgumentParser(description='Run unit tests.')
    parser.add_argument('tests', metavar='TEST', nargs='*', help='list of tests to run, or nothing to run them all')
    args = parser.parse_args()

    result = run_tests(args.tests)
    print("<tests %s ran='%s' errors='%s' fails='%s' success='%s'/>" % (
        "xmlns='http//andyet.net/protocol/tests'",
        result.testsRun, len(result.errors),
        len(result.failures), result.wasSuccessful()))

    sys.exit(not result.wasSuccessful())
