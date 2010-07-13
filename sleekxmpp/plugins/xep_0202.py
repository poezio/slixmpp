"""
	SleekXMPP: The Sleek XMPP Library
	Copyright (C) 2007  Nathanael C. Fritz
	This file is part of SleekXMPP.

	SleekXMPP is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 2 of the License, or
	(at your option) any later version.

	SleekXMPP is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with SleekXMPP; if not, write to the Free Software
	Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

from . import base
from xml.etree import cElementTree as ET
from datetime import datetime

XMLNS = 'urn:xmpp:time'
_XMLNS = '{%s}' % XMLNS

class xep_0202(base.base_plugin):
	"""
	Implements XEP-0202 Entity Time

	TODO currently no support for the user's 'local' timezone; `<tzo>` is always reported as `Z` (UTC).
	"""
	
	def plugin_init(self):
		self.xep = '0202'
		self.description = "Entity Time"
		self.xmpp.add_handler("<iq type='get'><time xmlns='%s' /></iq>" % XMLNS, self._handle_get)
	
	def post_init(self):
		base.base_plugin.post_init(self)
		disco = self.xmpp.plugin.get('xep_0030',None)
		if disco: disco.add_feature(XMLNS)

	def send_request(self,to):
		iq = self.xmpp.Iq( stream=self.xmpp, sto=to, stype='get',
				xml = ET.Element(_XMLNS + 'time') )
		resp = iq.send(iq) # wait for response
		time_str = resp.find(_XMLNS + 'time/utc').text
		dt_format = '%Y-%m-%dT%H:%M:%S'
		if time_str.find('.') > -1: dt_format += '.%f' # milliseconds in format 
		return TimeElement( 
			datetime.strptime( time_str, dt_format + 'Z' ), 
			xml.find(_XMLNS + 'time/tzo').text ) 

	def _handle_get(self,xml):
		iq = self.xmpp.Iq( sid=xml.get('id'), sto=xml.get('from'), stype='result' )
		iq.append( TimeElement().to_xml() )
		self.xmpp.send(iq)
		


class TimeElement:
	"""
	Time response data
	"""

	def __init__(self, utc=None, tzo="Z"):
		self.utc = datetime.utcnow() if utc is None else utc
		self.tzo = tzo

	def to_xml(self):
		time = ET.Element(_XMLNS+'time')
		child = ET.Element('tzo')
		child.text = str(self.tzo)
		time.append( child )
		child = ET.Element('utc')
		child.text = datetime.isoformat(self.utc) + "Z"
		time.append( child )
		return time
