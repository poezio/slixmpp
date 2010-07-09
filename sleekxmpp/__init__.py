#!/usr/bin/python2.5

"""
	SleekXMPP: The Sleek XMPP Library
	Copyright (C) 2010  Nathanael C. Fritz
	This file is part of SleekXMPP.

	See the file license.txt for copying permission.
"""
from __future__ import absolute_import, unicode_literals
from . basexmpp import basexmpp
from xml.etree import cElementTree as ET
from . xmlstream.xmlstream import XMLStream
from . xmlstream.xmlstream import RestartStream
from . xmlstream.matcher.xmlmask import MatchXMLMask
from . xmlstream.matcher.xpath import MatchXPath
from . xmlstream.matcher.many import MatchMany
from . xmlstream.handler.callback import Callback
from . xmlstream.stanzabase import StanzaBase
from . xmlstream import xmlstream as xmlstreammod
from . stanza.message import Message
from . stanza.iq import Iq
import time
import logging
import base64
import sys
import random
import copy
from . import plugins
from xml.etree.cElementTree import tostring
from xml.etree.cElementTree import Element
from cStringIO import StringIO

#from . import stanza
srvsupport = True
try:
	import dns.resolver
	import dns.rdatatype
	import dns.exception
except ImportError:
	srvsupport = False


class ClientXMPP(basexmpp, XMLStream):
	"""SleekXMPP's client class.  Use only for good, not evil."""

	def __init__(self, jid, password, ssl=False, plugin_config = {}, plugin_whitelist=[], escape_quotes=True):
		XMLStream.__init__(self)
		self.default_ns = 'jabber:client'
		basexmpp.__init__(self)
		self.plugin_config = plugin_config
		self.escape_quotes = escape_quotes
		self.set_jid(jid)
		self.port = 5222 # not used if DNS SRV is used
		self.plugin_whitelist = plugin_whitelist
		self.auto_reconnect = True
		self.srvsupport = srvsupport
		self.password = password
		self.registered_features = []
		self.stream_header = """<stream:stream to='%s' xmlns:stream='http://etherx.jabber.org/streams' xmlns='%s' version='1.0'>""" % (self.domain,self.default_ns)
		self.stream_footer = "</stream:stream>"
		#self.map_namespace('http://etherx.jabber.org/streams', 'stream')
		#self.map_namespace('jabber:client', '')
		self.features = []
		#TODO: Use stream state here
		self.authenticated = False
		self.sessionstarted = False
		self.bound = False
		self.bindfail = False
		self.digest_auth_started = False
		XMLStream.registerHandler(self, Callback('Stream Features', MatchXPath('{http://etherx.jabber.org/streams}features'), self._handleStreamFeatures, thread=True))
		XMLStream.registerHandler(self, Callback('Roster Update', MatchXPath('{%s}iq/{jabber:iq:roster}query' % self.default_ns), self._handleRoster, thread=True))
		#SASL Auth handlers
		basexmpp.add_handler(self, "<challenge xmlns='urn:ietf:params:xml:ns:xmpp-sasl' />", self.handler_sasl_digest_md5_auth, instream=True)
		basexmpp.add_handler(self, "<response xmlns='urn:ietf:params:xml:ns:xmpp-sasl'/>", self.handler_sasl_digest_md5_auth_fail, instream=True)
		basexmpp.add_handler(self, "<success xmlns='urn:ietf:params:xml:ns:xmpp-sasl' />", self.handler_auth_success, instream=True)
		basexmpp.add_handler(self, "<failure xmlns='urn:ietf:params:xml:ns:xmpp-sasl' />", self.handler_auth_fail, instream=True)
		#self.registerHandler(Callback('Roster Update', MatchXMLMask("<presence xmlns='%s' type='subscribe' />" % self.default_ns), self._handlePresenceSubscribe, thread=True))
		self.registerFeature("<starttls xmlns='urn:ietf:params:xml:ns:xmpp-tls' />", self.handler_starttls, True)
		self.registerFeature("<mechanisms xmlns='urn:ietf:params:xml:ns:xmpp-sasl' />", self.handler_sasl_auth, True)
		self.registerFeature("<bind xmlns='urn:ietf:params:xml:ns:xmpp-bind' />", self.handler_bind_resource)
		self.registerFeature("<session xmlns='urn:ietf:params:xml:ns:xmpp-session' />", self.handler_start_session)
		
		#self.registerStanzaExtension('PresenceStanza', PresenceStanzaType)
		#self.register_plugins()
	
	def __getitem__(self, key):
		if key in self.plugin:
			return self.plugin[key]
		else:
			logging.warning("""Plugin "%s" is not loaded.""" % key)
			return False
	
	def get(self, key, default):
		return self.plugin.get(key, default)

	def connect(self, host=None, port=None):
		"""Connect to the Jabber Server.  Attempts SRV lookup, and if it fails, uses
		the JID server.  You can optionally specify a host/port if you're not using 
		DNS and want to connect to a server address that is different from the XMPP domain."""

		if self.state['connected']: return True

		if host: # if a host was specified, don't attempt a DNS lookup.
			if port is None: port = self.port
		else:
			if not self.srvsupport:
				logging.warn("Did not supply (address, port) to connect to and no SRV support is installed (http://www.dnspython.org).  Continuing to attempt connection, using domain from JID.")
			else:
				logging.debug("Since no address is supplied, attempting SRV lookup.")
				try:
					answers = dns.resolver.query("_xmpp-client._tcp.%s" % self.domain, dns.rdatatype.SRV)
				except dns.resolver.NXDOMAIN:
					logging.info("No appropriate SRV record found for %s.  Using domain as server address.", self.domain)
				except dns.exception.DNSException:
					# this could be a timeout or other DNS error. Worth retrying?
					logging.exception("DNS error during SRV query for %s.  Using domain as server address.", self.domain)
				else:
					# pick a random answer, weighted by priority
					# there are less verbose ways of doing this (random.choice() with answer * priority), but I chose this way anyway 
					# suggestions are welcome
					addresses = {}
					intmax = 0
					priorities = []
					for answer in answers:
						intmax += answer.priority
						addresses[intmax] = (answer.target.to_text()[:-1], answer.port)
						priorities.append(intmax) # sure, I could just do priorities = addresses.keys()\n priorities.sort()
					picked = random.randint(0, intmax)
					for priority in priorities:
						if picked <= priority:
							(host,port) = addresses[priority]
							break

		if not host:
			# if all else fails take server from JID.
			(host,port) = (self.domain, self.port)

		logging.debug('Attempting connection to %s:%d', host, port )
		result = XMLStream.connect(self, host, port)
		if result:
			self.event("connected")
		else:
			logging.warning("Failed to connect")
			self.event("disconnected")
		return result
	
	# overriding reconnect and disconnect so that we can get some events
	# should events be part of or required by xmlstream?  Maybe that would be cleaner
	def reconnect(self):
		self.disconnect(reconnect=True)
	
	def disconnect(self, reconnect=False, error=False):
		self.event("disconnected")
		self.authenticated = False
		self.sessionstarted = False
		XMLStream.disconnect(self, reconnect, error)

	def sendRaw(self, data, priority=5, init=False):
		if not init and not self.sessionstarted:
			logging.warn("Attempt to send stanza before session has started:\n%s", data)
			return False
		XMLStream.sendRaw(self, data, priority, init)
	
	def registerFeature(self, mask, pointer, breaker = False):
		"""Register a stream feature."""
		self.registered_features.append((MatchXMLMask(mask), pointer, breaker))

	def updateRoster(self, jid, name=None, subscription=None, groups=[]):
		"""Add or change a roster item."""
		iq = self.Iq().setValues({'type': 'set'})
		iq['roster'] = {jid: {'name': name, 'subscription': subscription, 'groups': groups}}
		#self.send(iq, self.Iq().setValues({'id': iq['id']}))
		r = iq.send()
		return r['type'] == 'result'
	
	def getRoster(self):
		"""Request the roster be sent."""
		iq = self.Iq().setValues({'type': 'get'}).enable('roster').send()
		self._handleRoster(iq, request=True)
	
	def _handleStreamFeatures(self, features):
		logging.debug('handling stream features')
		self.features = []
		for sub in features.xml:
			self.features.append(sub.tag)
		for subelement in features.xml:
			for feature in self.registered_features:
				if feature[0].match(subelement):
				#if self.maskcmp(subelement, feature[0], True):
					# This calls the feature handler & optionally breaks
					if feature[1](subelement) and feature[2]: #if breaker, don't continue
						return True
	
	def handler_starttls(self, xml):
		logging.debug( 'TLS start handler; SSL support: %s', self.ssl_support )
		if not self.authenticated and self.ssl_support:
			_stanza = "<proceed xmlns='urn:ietf:params:xml:ns:xmpp-tls' />"
			if not self.event_handlers.get(_stanza,None): # don't add handler > once
				self.add_handler( _stanza, self.handler_tls_start, instream=True )
			self.sendRaw(self.tostring(xml), priority=1, init=True)
			return True
		else:
			logging.warning("The module tlslite is required in to some servers, and has not been found.")
			return False

	def handler_tls_start(self, xml):
		logging.debug("Starting TLS")
		if self.startTLS():
			raise RestartStream()
	
	def handler_sasl_auth(self, xml):
		if '{urn:ietf:params:xml:ns:xmpp-tls}starttls' in self.features:
			return False
		logging.debug("Starting SASL Auth")
		sasl_mechs = xml.findall('{urn:ietf:params:xml:ns:xmpp-sasl}mechanism')
		if len(sasl_mechs):
			for sasl_mech in sasl_mechs:
				self.features.append("sasl:%s" % sasl_mech.text)
			if 'sasl:DIGEST-MD5' in self.features:
				self.sendRaw("<auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='DIGEST-MD5'/>", priority=1, init=True)
			elif 'sasl:PLAIN' in self.features:
				if sys.version_info < (3,0):
					self.sendRaw("<auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='PLAIN'>%s</auth>" \
							% base64.b64encode(b'\x00' + bytes(self.username) + b'\x00' + bytes(self.password)).decode('utf-8'), 
							priority=1, init=True)
				else:
					self.sendRaw("<auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='PLAIN'>%s</auth>" \
							% base64.b64encode(b'\x00' + bytes(self.username, 'utf-8') + b'\x00' + bytes(self.password, 'utf-8')).decode('utf-8'), 
							priority=1, init=True)
			else:
				logging.error("No appropriate login method.")
				self.disconnect()
				#if 'sasl:DIGEST-MD5' in self.features:
				#	self._auth_digestmd5()
		return True
	
	def handler_sasl_digest_md5_auth(self, xml):
		if self.digest_auth_started == False:
			challenge = [item.split('=', 1) for item in base64.b64decode(xml.text).replace("\"", "").split(',', 6) ]
			challenge = dict(challenge)
			logging.debug("MD5 auth challenge: %s", challenge)
			
			if challenge.get('rspauth'): #authenticated success... send response
				self.sendRaw("""<response xmlns='urn:ietf:params:xml:ns:xmpp-sasl'/>""", priority=1, init=True )
				return
			
			#TODO: use realm is supplied by server, use default qop unless supplied by server
			#Realm, nonce, qop should all be present
			if not challenge.get('qop') or not challenge.get('nonce'):
				logging.error("Error during digest-md5 authentication. Challenge missing critical information. Challenge: %s" %base64.b64decode(xml.text))
				self.disconnect()
				self.event("failed_auth")
				return
			#TODO: charset can be either UTF-8 or if not present use ISO 8859-1 defaulting for UTF-8 for now
			#Compute the cnonce - a unique hex string only used in this request
			cnonce = ""
			for i in range(7):
				cnonce+=hex(int(random.random()*65536*4096))[2:]
			cnonce = base64.encodestring(cnonce)[0:-1]
			a1 = b"%s:%s:%s" %(md5("%s:%s:%s" % (self.username, self.domain, self.password)), challenge["nonce"].encode("UTF-8"), cnonce.encode("UTF-8") )
			a2 = "AUTHENTICATE:xmpp/%s" %self.domain
			responseHash = md5digest("%s:%s:00000001:%s:auth:%s" %(md5digest(a1), challenge["nonce"], cnonce, md5digest(a2) ) )
			response = 'charset=utf-8,username="%s",realm="%s",nonce="%s",nc=00000001,cnonce="%s",digest-uri="%s",response=%s,qop=%s,' \
				% (self.username, self.domain, challenge["nonce"], cnonce, "xmpp/%s" % self.domain, responseHash, challenge["qop"])
			self.sendRaw("<response xmlns='urn:ietf:params:xml:ns:xmpp-sasl'>%s</response>" % base64.encodestring(response)[:-1],
					priority=1, init=True )
		else:
			logging.warn("handler_sasl_digest_md5_auth called while digest_auth_started is True (has already begun)")
	
	def handler_sasl_digest_md5_auth_fail(self, xml):
		self.digest_auth_started = False
		self.handler_auth_fail(xml)
	
	def handler_auth_success(self, xml):
		logging.debug("Authentication successful.")
		self.authenticated = True
		self.features = []
		raise RestartStream()

	def handler_auth_fail(self, xml):
		logging.warning("Authentication failed.")
		logging.debug(tostring(xml, 'utf-8'))
		self.disconnect()
		self.event("failed_auth")
	
	def handler_bind_resource(self, xml):
		logging.debug("Requesting resource: %s" % self.resource)
		iq = self.Iq(stype='set')
		res = ET.Element('resource')
		res.text = self.resource
		xml.append(res)
		iq.append(xml)
		response = iq.send(priority=2,init=True)
		#response = self.send(iq, self.Iq(sid=iq['id']))
		self.set_jid(response.xml.find('{urn:ietf:params:xml:ns:xmpp-bind}bind/{urn:ietf:params:xml:ns:xmpp-bind}jid').text)
		self.bound = True
		logging.info("Node set to: %s" % self.fulljid)
		if "{urn:ietf:params:xml:ns:xmpp-session}session" not in self.features or self.bindfail:
			logging.debug("Established Session")
			self.sessionstarted = True
			self.event("session_start")
	
	def handler_start_session(self, xml):
		if self.authenticated and self.bound:
			iq = self.makeIqSet(xml)
			response = iq.send(priority=2,init=True)
			logging.debug("Established Session")
			self.sessionstarted = True
			self.event("session_start")
		else:
			logging.warn("Bind has failed; not starting session!")
			self.bindfail = True
	
	def _handleRoster(self, iq, request=False):
		if iq['type'] == 'set' or (iq['type'] == 'result' and request):
			for jid in iq['roster']['items']:
				if not jid in self.roster:
					self.roster[jid] = {'groups': [], 'name': '', 'subscription': 'none', 'presence': {}, 'in_roster': True}
				self.roster[jid].update(iq['roster']['items'][jid])
			if iq['type'] == 'set':
				self.send(self.Iq().setValues({'type': 'result', 'id': iq['id']}).enable('roster'))
		self.event("roster_update", iq)

def md5(data):
	try:
		import hashlib
		md5 = hashlib.md5(data)
	except ImportError:
		import md5
		md5 = md5.new(data)
	return md5.digest()

def md5digest(data):
	try:
		import hashlib
		md5 = hashlib.md5(data)
	except ImportError:
		import md5
		md5 = md5.new(data)
	return md5.hexdigest()
