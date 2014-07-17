try:
    from collections import OrderedDict
except:
    from slixmpp.thirdparty.ordereddict import OrderedDict

try:
    from gnupg import GPG
except:
    from slixmpp.thirdparty.gnupg import GPG

from slixmpp.thirdparty import socks
from slixmpp.thirdparty.mini_dateutil import tzutc, tzoffset, parse_iso
