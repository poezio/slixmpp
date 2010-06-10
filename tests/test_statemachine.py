import unittest
import time, threading, random, functools

if __name__ == '__main__': 
	import sys, os
	sys.path.insert(0, os.getcwd())
	import sleekxmpp.xmlstream.statemachine as sm


class testStateMachine(unittest.TestCase):

	def setUp(self): pass
	
	
	def testDefaults(self):
		"Test ensure transitions occur correctly in a single thread"
		s = sm.StateMachine(('one','two','three'))
		self.assertTrue(s['one'])
		self.failIf(s['two'])
		try:
			s['booga']
			self.fail('s.booga is an invalid state and should throw an exception!')
		except: pass #expected exception

		# just make sure __str__ works, no reason to test its exact value:
		print str(s)


	def testTransitions(self):
		"Test ensure transitions occur correctly in a single thread"
		s = sm.StateMachine(('one','two','three'))

		self.assertTrue( s.transition('one', 'two') )
		self.assertTrue( s['two'] )
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
			if s['two']:
				print 'thread has already transitioned!'
				self.fail()
			thread_state['ready'] = True
			print 'Thread is ready'
			# this will block until the main thread transitions to 'two'
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
		

	def testForRaceCondition(self):
		"""Attempt to allow two threads to perform the same transition; 
		only one should ever make it."""

		s = sm.StateMachine(('one','two','three'))

		def t1(num):
			while True:
				if not trigger['go'] or thread_state[num] in (True,False):
					time.sleep( random.random()/100 ) # < .01s
					if thread_state[num] == 'quit': break
					continue

				thread_state[num] = s.transition('one','two' )
#				print '-',

		thread_count = 20
		threads = []
		thread_state = {}
		def reset(): 
			for c in range(thread_count): thread_state[c] = "reset"
		trigger = {'go':False} # use of a plain boolean seems to be non-volatile between threads.

		for c in range(thread_count):
			thread_state[c] = "reset"
			thread = threading.Thread( target= functools.partial(t1,c) )
			threads.append( thread )
			thread.daemon = True
			thread.start()

		for x in range(100): # this will take 10s to execute
#			print "+",
			trigger['go'] = True
			time.sleep(.1)
			trigger['go'] = False
			winners = 0
			for (num, state) in thread_state.items():
				if state == True: winners = winners +1
				elif state != False: raise Exception( "!%d!%s!" % (num,state) )
			
			self.assertEqual( 1, winners, "Expected one winner! %d" % winners )
			self.assertTrue( s.ensure('two') )
			self.assertTrue( s.transition('two','one') ) # return to the first state.
			reset()

		# now let the threads quit gracefully:
		for c in range(thread_count): thread_state[c] = 'quit'
		time.sleep(2)


	def testTransitionFunctions(self):
		"test that a `func` argument allows or blocks the transition correctly."

		s = sm.StateMachine(('one','two','three'))
		
		def alwaysFalse(): return False
		def alwaysTrue(): return True

		self.failIf( s.transition('one','two', func=alwaysFalse) )
		self.assertTrue(s['one'])
		self.failIf(s['two'])

		self.assertTrue( s.transition('one','two', func=alwaysTrue) )
		self.failIf(s['one'])
		self.assertTrue(s['two'])


	def testTransitionFuncException(self):
		"if a transition function throws an exeption, ensure we're in a sane state"

		s = sm.StateMachine(('one','two','three'))
		
		def alwaysException(): raise Exception('whups!')

		try:
			self.failIf( s.transition('one','two', func=alwaysException) )
			self.fail("exception should have been thrown")
		except: pass #expected exception

		self.assertTrue(s['one'])
		self.failIf(s['two'])

		# ensure a subsequent attempt completes normally:
		self.assertTrue( s.transition('one','two') )
		self.failIf(s['one'])
		self.assertTrue(s['two'])


	def testContextManager(self):

		s = sm.StateMachine(('one','two','three'))

		with s.transition_ctx('one','two'):
			self.assertTrue( s['one'] )
			self.failIf( s['two'] )

		#successful transition b/c no exception was thrown
		self.assertTrue( s['two'] )
		self.failIf( s['one'] )

		# failed transition because exception is thrown:
		try:
			with s.transition_ctx('two','three'):
				raise Exception("boom!")
			self.fail('exception expected')
		except: pass

		self.failIf( s.current_state() in ('one','three') )
		self.assertTrue( s['two'] )

	def testCtxManagerTransitionFailure(self):

		s = sm.StateMachine(('one','two','three'))

		with s.transition_ctx('two','three') as result:
			self.failIf( result )
			self.assertTrue( s['one'] )
			self.failIf( s.current_state in ('two','three') )

		self.assertTrue( s['one'] )
		
		def r1():
			print 'thread 1 started'
			self.assertTrue( s.transition('one','two') )
			print 'thread 1 transitioned'

		def r2():
			print 'thread 2 started'
			self.failIf( s['two'] )
			with s.transition_ctx('two','three', 10) as result:
				self.assertTrue( result )
				self.assertTrue( s['two'] )
				print 'thread 2 will transition on exit from the context manager...'
			self.assertTrue( s['three'] )
			print 'transitioned to %s' % s.current_state()

		t1 = threading.Thread(target=r1)
		t2 = threading.Thread(target=r2)

		t2.start() # this should block until r1 goes
		time.sleep(1)
		t1.start()

		t1.join()
		t2.join()

		self.assertTrue( s['three'] )


suite = unittest.TestLoader().loadTestsFromTestCase(testStateMachine)

if __name__ == '__main__': unittest.main()
