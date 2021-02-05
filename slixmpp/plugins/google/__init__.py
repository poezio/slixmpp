
# Slixmpp: The Slick XMPP Library
# Copyright (C) 2013 Nathanael C. Fritz, Lance J.T. Stout
# This file is part of slixmpp.
# See the file LICENSE for copying permission.
from slixmpp.plugins.base import register_plugin, BasePlugin

from slixmpp.plugins.google.gmail import Gmail
from slixmpp.plugins.google.auth import GoogleAuth
from slixmpp.plugins.google.settings import GoogleSettings
from slixmpp.plugins.google.nosave import GoogleNoSave


class Google(BasePlugin):

    """
    Google: Custom GTalk Features

    Also see: <https://developers.google.com/talk/jep_extensions/extensions>
    """

    name = 'google'
    description = 'Google: Custom GTalk Features'
    dependencies = set([
        'gmail',
        'google_settings',
        'google_nosave',
        'google_auth'
    ])

    def __getitem__(self, attr):
        if attr in ('settings', 'nosave', 'auth'):
            return self.xmpp['google_%s' % attr]
        elif attr == 'gmail':
            return self.xmpp['gmail']
        else:
            raise KeyError(attr)


register_plugin(Gmail)
register_plugin(GoogleAuth)
register_plugin(GoogleSettings)
register_plugin(GoogleNoSave)
register_plugin(Google)
