#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Slixmpp: The Slick XMPP Library
    Copyright (C) 2011  Dann Martens
    This file is part of Slixmpp.

    See the file LICENSE for copying permission.
"""

from slixmpp.plugins.xep_0009.remote import Endpoint, remote, Remote, \
    ANY_ALL, Future
import time

class Boomerang(Endpoint):

    def FQN(self):
        return 'boomerang'

    @remote
    def throw(self):
        print("Duck!")



def main():

    session = Remote.new_session('kangaroo@xmpp.org/rpc', '*****')

    session.new_handler(ANY_ALL, Boomerang)

    boomerang = session.new_proxy('kangaroo@xmpp.org/rpc', Boomerang)

    callback = Future()

    boomerang.async(callback).throw()

    time.sleep(10)

    session.close()



if __name__ == '__main__':
    main()

