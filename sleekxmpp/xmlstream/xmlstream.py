"""
	SleekXMPP: The Sleek XMPP Library
	Copyright (C) 2010  Nathanael C. Fritz
	This file is part of SleekXMPP.

	See the file license.txt for copying permission.
"""

from __future__ import with_statement, unicode_literals
try:
	import queue
except ImportError:
	import Queue as queue
from . import statemachine
from . stanzabase import StanzaBase
from xml.etree import cElementTree
from xml.parsers import expat
import logging
import random
import socket
import threading
import time
import traceback
import types
import xml.sax.saxutils
from . import scheduler

HANDLER_THREADS = 1

ssl_support = True
#try:
import ssl
#except ImportError:
#	ssl_support = False
import sys
if sys.version_info < (3, 0):
	#monkey patch broken filesocket object
	from . import filesocket
	#socket._fileobject = filesocket.filesocket
	

class RestartStream(Exception):
	pass

stanza_extensions = {}

RECONNECT_MAX_DELAY = 3600
RECONNECT_QUIESCE_FACTOR = 1.6180339887498948 # Phi
RECONNECT_QUIESCE_JITTER = 0.11962656472 # molar Planck constant times c, joule meter/mole

class XMLStream(object):
	"A connection manager with XML events."

	def __init__(self, socket=None, host='', port=0, escape_quotes=False):
		global ssl_support
		self.ssl_support = ssl_support
		self.escape_quotes = escape_quotes
		self.state = statemachine.StateMachine(('disconnected','connected'))
		self.should_reconnect = True

		self.setSocket(socket)
		self.address = (host, int(port))

		self.__thread = {}

		self.__root_stanza = []
		self.__stanza = {}
		self.__stanza_extension = {}
		self.__handlers = []

		self.__tls_socket = None
		self.filesocket = None
		self.use_ssl = False
		self.use_tls = False
		self.ca_certs=None

		self.stream_header = "<stream>"
		self.stream_footer = "</stream>"

		self.eventqueue = queue.Queue()
		self.sendqueue = queue.PriorityQueue()
		self.scheduler = scheduler.Scheduler(self.eventqueue)

		self.namespace_map = {}

		# booleans are not volatile in Python and changes 
		# do not seem to be detected easily between threads.
		self.quit = threading.Event()
	
	def setSocket(self, socket):
		"Set the socket"
		self.socket = socket
		if socket is not None:
			with self.state.transition_ctx('disconnected','connected') as locked:
				if not locked: raise Exception('Already connected')
				# ElementTree.iterparse requires a file.  0 buffer files have to be binary
				self.filesocket = socket.makefile('rb', 0) 
	
	def setFileSocket(self, filesocket):
		self.filesocket = filesocket
	
	def connect(self, host='', port=0, use_ssl=None, use_tls=None):
		"Establish a socket connection to the given XMPP server."
		
		if not self.state.transition('disconnected','connected',
				func=self.connectTCP, args=[host, port, use_ssl, use_tls] ):
			
			if self.state['connected']: logging.debug('Already connected')
			else: logging.warning("Connection failed" )
			return False

		logging.debug('Connection complete.')
		return True

		# TODO currently a caller can't distinguish between "connection failed" and
		# "we're already trying to connect from another thread"

	def connectTCP(self, host='', port=0, use_ssl=None, use_tls=None, reattempt=True):
		"Connect and create socket"

		# Note that this is thread-safe by merit of being called solely from connect() which
		# holds the state lock.
		
		delay = 1.0 # reconnection delay
		while not self.quit.is_set():
			logging.debug('connecting....')
			try:
				if host and port:
					self.address = (host, int(port))
				if use_ssl is not None:
					self.use_ssl = use_ssl
				if use_tls is not None:
					# TODO this variable doesn't seem to be used for anything!
					self.use_tls = use_tls
				if sys.version_info < (3, 0):
					self.socket = filesocket.Socket26(socket.AF_INET, socket.SOCK_STREAM)
				else:
					self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.socket.settimeout(None) #10)

				if self.use_ssl and self.ssl_support:
					logging.debug("Socket Wrapped for SSL")
					self.socket = ssl.wrap_socket(self.socket,ca_certs=self.ca_certs)
				
				self.socket.connect(self.address)
				self.filesocket = self.socket.makefile('rb', 0)
				
				return True

			except socket.error as serr:
				logging.exception("Socket Error #%s: %s", serr.errno, serr.strerror)
				if not reattempt: return False
			except:
				logging.exception("Connection error")
				if not reattempt: return False				
			
			# quiesce if rconnection fails:
			# This algorithm based loosely on Twisted internet.protocol
			# http://twistedmatrix.com/trac/browser/trunk/twisted/internet/protocol.py#L310
			delay = min(delay * RECONNECT_QUIESCE_FACTOR, RECONNECT_MAX_DELAY)
			delay = random.normalvariate(delay, delay * RECONNECT_QUIESCE_JITTER)
			logging.debug('Waiting %.3fs until next reconnect attempt...', delay)
			time.sleep(delay)


	
	def connectUnix(self, filepath):
		"Connect to Unix file and create socket"

	def startTLS(self):
		"Handshakes for TLS"
		if self.ssl_support:
			logging.info("Negotiating TLS")
#			self.realsocket = self.socket # NOT USED
			self.socket = ssl.wrap_socket(self.socket, 
					ssl_version=ssl.PROTOCOL_TLSv1, 
					do_handshake_on_connect=False, 
					ca_certs=self.ca_certs)
			self.socket.do_handshake()
			if sys.version_info < (3,0):
				from . filesocket import filesocket
				self.filesocket = filesocket(self.socket)
			else:
				self.filesocket = self.socket.makefile('rb', 0)

			logging.debug("TLS negotitation successful")
			return True
		else:
			logging.warning("Tried to enable TLS, but ssl module not found.")
			return False
		raise RestartStream()
	
	def process(self, threaded=True):
		self.quit.clear()
		self.scheduler.process(threaded=True)
		for t in range(0, HANDLER_THREADS):
			th = threading.Thread(name='eventhandle%s' % t, target=self._eventRunner)
			th.setDaemon(True)
			self.__thread['eventhandle%s' % t] = th
			th.start()
		th = threading.Thread(name='sendthread', target=self._sendThread)
		th.setDaemon(True)
		self.__thread['sendthread'] = th
		th.start()
		if threaded:
			th = threading.Thread(name='process', target=self._process)
			th.setDaemon(True)
			self.__thread['process'] = th
			th.start()
		else:
			self._process()
	
	def schedule(self, name, seconds, callback, args=None, kwargs=None, repeat=False):
		self.scheduler.add(name, seconds, callback, args, kwargs, repeat, qpointer=self.eventqueue)
	
	def _process(self):
		"Start processing the socket."
		logging.debug('Process thread starting...')
		while not self.quit.is_set():
			if not self.state.ensure('connected',wait=2, block_on_transition=True): continue
			try:
				logging.debug(' ------------------------------- starting process loop...')
				self.sendPriorityRaw(self.stream_header)
				self.__readXML() # this loops until the stream is terminated.
			except socket.timeout:
				# TODO currently this will re-send a stream header if this exception occurs.  
				# I don't think that's intended behavior.
				logging.warn('socket rcv timeout')
				pass
			except RestartStream:
				logging.debug("Restarting stream...")
				continue # DON'T re-initialize the stream -- this exception is sent 
				# specifically when we've initialized TLS and need to re-send the <stream> header.
			except (KeyboardInterrupt, SystemExit):
				logging.debug("System interrupt detected")
				self.shutdown()
				self.eventqueue.put(('quit', None, None))
			except:
				logging.exception('Unexpected error in RCV thread')

			# if the RCV socket is terminated for whatever reason, our only sane choice of action is an attempt 
			# to re-establish the connection.
			if not self.quit.is_set():
				logging.info( 'about to reconnect..........' )
				logging.info( 'about to reconnect..........' )
				logging.info( 'about to reconnect..........' )
				logging.info( 'about to reconnect..........' )
				try:
					self.disconnect(reconnect=self.should_reconnect, error=True)
				except: 
					logging.exception( "WTF disconnect!" )
				logging.info( 'reconnect complete!' )
				logging.info( 'reconnect complete!' )
				logging.info( 'reconnect complete!' )
				logging.info( 'reconnect complete!' )
				logging.info( 'reconnect complete!' )

		logging.debug('Quitting Process thread')
	
	def __readXML(self):
		"Parses the incoming stream, adding to xmlin queue as it goes"
		#build cElementTree object from expat was we go
		#self.filesocket = self.socket.makefile('rb', 0)
		#print self.filesocket.read(1024) #self.filesocket._sock.recv(1024)
		edepth = 0
		root = None
		for (event, xmlobj) in cElementTree.iterparse(self.filesocket, (b'end', b'start')):
			if edepth == 0: # and xmlobj.tag.split('}', 1)[-1] == self.basetag:
				if event == b'start':
					root = xmlobj
					logging.debug('handling start stream')
					self.start_stream_handler(root)
			if event == b'end':
				edepth += -1
				if edepth == 0 and event == b'end':
					logging.warn("Premature EOF from read socket; Ending readXML loop")
					# this is a premature EOF as far as I can tell; raise an exception so the stream get closed and re-established cleanly.
					return False
				elif edepth == 1:
					#self.xmlin.put(xmlobj)
					self.__spawnEvent(xmlobj)
					if root: root.clear()
			if event == b'start':
				edepth += 1
		logging.warn("Exiting readXML loop")
		# TODO under what conditions will this _ever_ occur?
		return False
	
	def _sendThread(self):
		logging.debug('send thread starting...')
		while not self.quit.is_set():
			if not self.state.ensure('connected',wait=2, block_on_transition=True): continue
			
			data = None
			try:
				data = self.sendqueue.get(True,5)[1]
				logging.debug("SEND: %s" % data)
				self.socket.sendall(data.encode('utf-8'))
			except queue.Empty:
#				logging.debug('Nothing on send queue')
				pass
			except socket.timeout:
				# this is to prevent a thread blocked indefinitely
				logging.debug('timeout sending packet data')
			except:
				logging.warning("Failed to send %s" % data)
				logging.exception("Socket error in SEND thread")
				# TODO it's somewhat unsafe for the sender thread to assume it can just
				# re-intitialize the connection, since the receiver thread could be doing 
				# the same thing concurrently.  Oops!  The safer option would be to throw 
				# some sort of event that could be handled by a common thread or the reader 
				# thread to perform reconnect and then re-initialize the handler threads as well.
				if self.should_reconnect:
					self.disconnect(reconnect=True, error=True)
	
	def sendRaw(self, data):
		self.sendqueue.put((1, data))
		return True
	
	def sendPriorityRaw(self, data):
		self.sendqueue.put((0, data))
		return True
	
	def disconnect(self, reconnect=False, error=False):
		logging.info('AAAAAAAAAAAAAAAAAAAAAAAA')
		with self.state.transition_ctx('connected','disconnected') as locked:
			logging.info('BBBBBBBBBBBBBBBBBBBBBBBBBB')	
			if not locked:
				logging.warning("Already disconnected.")
				return

			logging.debug("Disconnecting...")
			# don't send a footer on error; if the stream is already closed, 
			# this won't get sent until the stream is re-initialized!
			if not error: self.sendRaw(self.stream_footer) #send end of stream
			try:
#				self.socket.shutdown(socket.SHUT_RDWR)
				self.socket.close()
			except socket.error as (errno,strerror):
				logging.exception("Error while disconnecting. Socket Error #%s: %s" % (errno, strerror))
			try:
				self.filesocket.close()
			except socket.error as (errno,strerror):
				logging.exception("Error closing filesocket.")

		if reconnect: self.connect()
	
	def shutdown(self):
		'''
		Disconnects and shuts down all event threads.
		'''
		self.disconnect()
		self.quit.set()
		self.scheduler.run = False

	def incoming_filter(self, xmlobj):
		return xmlobj

	def __spawnEvent(self, xmlobj):
		"watching xmlOut and processes handlers"
		if logging.getLogger().isEnabledFor(logging.DEBUG):
			logging.debug("RECV: %s" % cElementTree.tostring(xmlobj))
		#convert XML into Stanza
		xmlobj = self.incoming_filter(xmlobj)
		stanza = None
		for stanza_class in self.__root_stanza:
			if xmlobj.tag == "{%s}%s" % (self.default_ns, stanza_class.name):
			#if self.__root_stanza[stanza_class].match(xmlobj):
				stanza = stanza_class(self, xmlobj)
				break
		if stanza is None:
			stanza = StanzaBase(self, xmlobj)
		unhandled = True
		# TODO inefficient linear search; performance might be improved by hashtable lookup
		for handler in self.__handlers:
			if handler.match(stanza):
#				logging.debug('matched stanza to handler %s', handler.name)
				handler.prerun(stanza)
				self.eventqueue.put(('stanza', handler, stanza))
				if handler.checkDelete():
#					logging.debug('deleting callback %s', handler.name)
					self.__handlers.pop(self.__handlers.index(handler))
				unhandled = False
		if unhandled:
			stanza.unhandled()
			#loop through handlers and test match
			#spawn threads as necessary, call handlers, sending Stanza

	def _eventRunner(self):
		logging.debug("Loading event runner")
		while not self.quit.is_set():
			try:
				event = self.eventqueue.get(True, timeout=5)
			except queue.Empty:
#				logging.debug('Nothing on event queue')
				event = None
			if event is not None:
				etype = event[0]
				handler = event[1]
				args = event[2:]
				#etype, handler, *args = event #python 3.x way
				if etype == 'stanza':
					try:
						handler.run(args[0])
					except Exception as e:
						logging.exception("Exception in event handler")
						args[0].exception(e)
				elif etype == 'sched':
					try:
						#handler(*args[0])
						handler.run(*args)
					except:
						logging.error(traceback.format_exc())
				elif etype == 'quit':
					logging.debug("Quitting eventRunner thread")
					return False

	def registerHandler(self, handler, before=None, after=None):
		"Add handler with matcher class and parameters."
		self.__handlers.append(handler)

	def removeHandler(self, name):
		"Removes the handler."
		idx = 0
		for handler in self.__handlers:
			if handler.name == name:
				self.__handlers.pop(idx)
				return
			idx += 1
	
	def registerStanza(self, stanza_class):
		"Adds stanza.  If root stanzas build stanzas sent in events while non-root stanzas build substanza objects."
		self.__root_stanza.append(stanza_class)
	
	def registerStanzaExtension(self, stanza_class, stanza_extension):
		if stanza_class not in stanza_extensions:
			stanza_extensions[stanza_class] = [stanza_extension]
		else:
			stanza_extensions[stanza_class].append(stanza_extension)
	
	def removeStanza(self, stanza_class, root=False):
		"Removes the stanza's registration."
		if root:
			del self.__root_stanza[stanza_class]
		else:
			del self.__stanza[stanza_class]
	
	def removeStanzaExtension(self, stanza_class, stanza_extension):
		stanza_extension[stanza_class].pop(stanza_extension)

	def tostring(self, xml, xmlns='', stringbuffer=''):
		newoutput = [stringbuffer]
		#TODO respect ET mapped namespaces
		itag = xml.tag.split('}', 1)[-1]
		if '}' in xml.tag:
			ixmlns = xml.tag.split('}', 1)[0][1:]
		else:
			ixmlns = ''
		nsbuffer = ''
		if xmlns != ixmlns and ixmlns != '':
			if ixmlns in self.namespace_map:
				if self.namespace_map[ixmlns] != '':
					itag = "%s:%s" % (self.namespace_map[ixmlns], itag)
			else:
				nsbuffer = """ xmlns="%s\"""" % ixmlns
		newoutput.append("<%s" % itag)
		newoutput.append(nsbuffer)
		for attrib in xml.attrib:
			newoutput.append(""" %s="%s\"""" % (attrib, self.xmlesc(xml.attrib[attrib])))
		if len(xml) or xml.text or xml.tail:
			newoutput.append(">")
			if xml.text:
				newoutput.append(self.xmlesc(xml.text))
			if len(xml):
				for child in xml.getchildren():
					newoutput.append(self.tostring(child, ixmlns))
			newoutput.append("</%s>" % (itag, ))
			if xml.tail:
				newoutput.append(self.xmlesc(xml.tail))
		elif xml.text:
			newoutput.append(">%s</%s>" % (self.xmlesc(xml.text), itag))
		else:
			newoutput.append(" />")
		return ''.join(newoutput)

	def xmlesc(self, text):
		text = list(text)
		cc = 0
		matches = ('&', '<', '"', '>', "'")
		for c in text:
			if c in matches:
				if c == '&':
					text[cc] = '&amp;'
				elif c == '<':
					text[cc] = '&lt;'
				elif c == '>':
					text[cc] = '&gt;'
				elif c == "'":
					text[cc] = '&apos;'
				elif self.escape_quotes:
					text[cc] = '&quot;'
			cc += 1
		return ''.join(text)
	
	def start_stream_handler(self, xml):
		"""Meant to be overridden"""
		logging.warn("No start stream handler has been implemented.")
