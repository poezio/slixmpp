try:
    from gnupg import GPG
except:
    from slixmpp.thirdparty.gnupg import GPG

from slixmpp.thirdparty.mini_dateutil import tzutc, tzoffset, parse_iso
from slixmpp.thirdparty.orderedset import OrderedSet
