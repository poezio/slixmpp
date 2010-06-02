import unittest
import time, threading

if __name__ == '__main__': 
	import sys, os
	sys.path.insert(0, os.getcwd())
	import sleekxmpp.xmlstream.statemachine as sm


class testStateMachine(unittest.TestCase):

	def setUp(self): pass
	
	
	def testDefaults(self):
		"Test ensure transitions occur correctly in a single thread"
		s = sm.StateMachine(('one','two','three'))
#		self.assertTrue(s.one)
		self.assertTrue(s['one'])
#		self.failIf(s.two)
		self.failIf(s['two'])
		try:
			s.booga
			self.fail('s.booga is an invalid state and should throw an exception!')
		except: pass #expected exception

	
	def testTransitions(self):
		"Test ensure transitions occur correctly in a single thread"
		s = sm.StateMachine(('one','two','three'))
#		self.assertTrue(s.one)

		self.assertTrue( s.transition('one', 'two') )
#		self.assertTrue( s.two )
		self.assertTrue( s['two'] )
#		self.failIf( s.one )
		self.failIf( s['one'] )

		self.assertTrue( s.transition('two', 'three') )
		self.assertTrue( s['three'] )
		self.failIf( s['two'] )

		self.assertTrue( s.transition('three', 'one') )
		self.assertTrue( s['one'] )
		self.failIf( s['three'] )

		# should return False immediately w/ no wait:
		self.failIf( s.transition('three', 'one') )
		self.assertTrue( s['one'] )
		self.failIf( s['three'] )

		# test fail condition w/ a short delay:
		self.failIf( s.transition('two', 'three') )

		# Ensure bad states are weeded out: 
		try: 
			s.transition('blah', 'three')
			s.fail('Exception expected')
		except: pass

		try: 
			s.transition('one', 'blahblah')
			s.fail('Exception expected')
		except: pass


	def testTransitionsBlocking(self):
		"Test that transitions block from more than one thread"

		s = sm.StateMachine(('one','two','three'))
		self.assertTrue(s['one'])

		now = time.time()
		self.failIf( s.transition('two', 'one', wait=5.0) )
		self.assertTrue( time.time() > now + 4 )
		self.assertTrue( time.time() < now + 7 )

	def testThreadedTransitions(self):
		"Test that transitions are atomic in > one thread"

		s = sm.StateMachine(('one','two','three'))
		self.assertTrue(s['one'])

		thread_state = {'ready': False, 'transitioned': False}
		def t1():
			# this will block until the main thread transitions to 'two'
			if s['two']:
				print 'thread has already transitioned!'
				self.fail()
			thread_state['ready'] = True
			print 'Thread is ready'
			self.assertTrue( s.transition('two','three', wait=20) )
			print 'transitioned to three!'
			thread_state['transitioned'] = True

		thread = threading.Thread(target=t1)
		thread.daemon = True
		thread.start()
		start = time.time()
		while not thread_state['ready']:
			print 'not ready'
			if time.time() > start+10: self.fail('Timeout waiting for thread to init!')
			time.sleep(0.1)
		time.sleep(0.2) # the thread should be blocking on the 'transition' call at this point.
		self.failIf( thread_state['transitioned'] ) # ensure it didn't 'go' yet.
		print 'transitioning to two!'
		self.assertTrue( s.transition('one','two') )
		time.sleep(0.2) # second thread should have transitioned now:
		self.assertTrue( thread_state['transitioned'] )
		



suite = unittest.TestLoader().loadTestsFromTestCase(testStateMachine)

if __name__ == '__main__': unittest.main()
