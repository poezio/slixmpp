from slixmpp.plugins.base import register_plugin

from slixmpp.plugins.xep_0356 import stanza
from slixmpp.plugins.xep_0356.stanza import Perm, Privilege
from slixmpp.plugins.xep_0356.privilege import XEP_0356

register_plugin(XEP_0356)
