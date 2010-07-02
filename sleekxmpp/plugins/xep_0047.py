'''
Created on Jul 1, 2010

@author: bbeggs
'''
from . import base
import logging
import threading
from xml.etree import cElementTree as ET

class xep_0047(base.base_plugin):
    '''
    In-band file transfer for xmpp.
    
    Both message and iq transfer is supported with message being attempted first.
    '''
       
    def plugin_init(self):
        self.xep = 'xep-047'
        self.description = 'in-band file transfer'
        self.acceptTransfers = self.config.get('acceptTransfers', True)
        self.saveDirectory = self.config.get('saveDirectory', '/tmp')
        self.stanzaType = self.config.get('stanzaType', 'message')
        self.maxSendThreads = self.config.get('maxSendThreads', 1)
        self.maxReceiveThreads = self.config.get('maxReceiveThreads', 1)
        
        #thread setup
        self.receiveThreads = {} #id:thread
        self.sendThreads = {}
        
        #add handlers to listen for incoming requests
        self.xmpp.add_handler("<iq><open xmlns='http://jabber.org/protocol/ibb' /></iq>", self._handleIncomingTransferRequest)
    
    def post_init(self):
        self.post_inited = True
        
    
    def sendFile(self, filePath, threaded=True):
        #TODO use this method to send a file
        pass    
    
    def _handleIncomingTransferRequest(self, xml):
        pass
    
class receiverThread(threading.Thread):
    def run(self):
        pass

class senderThread(threading.Thread):
    def run(self):
        pass
    
