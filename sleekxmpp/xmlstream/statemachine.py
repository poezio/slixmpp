"""
    SleekXMPP: The Sleek XMPP Library
    Copyright (C) 2010  Nathanael C. Fritz
    This file is part of SleekXMPP.

    See the file license.txt for copying permission.
"""
from __future__ import with_statement
import threading
import time
import logging


class StateMachine(object):

	def __init__(self, states=[]):
		self.lock = threading.Condition(threading.RLock())
		self.__states= []
		self.addStates(states)
		self.__default_state = self.__states[0]
		self.__current_state = self.__default_state
	
	def addStates(self, states):
		with self.lock:
			for state in states:
				if state in self.__states:
					raise IndexError("The state '%s' is already in the StateMachine." % state)
				self.__states.append( state )
	
	
	def transition(self, from_state, to_state, wait=0.0, func=None, args=[], kwargs={} ):
		'''
		Transition from the given `from_state` to the given `to_state`.  
		This method will return `True` if the state machine is now in `to_state`.  It
		will return `False` if a timeout occurred the transition did not occur.  
		If `wait` is 0 (the default,) this method returns immediately if the state machine 
		is not in `from_state`.

		If you want the thread to block and transition once the state machine to enters
		`from_state`, set `wait` to a non-negative value.  Note there is no 'block 
		indefinitely' flag since this leads to deadlock.  If you want to wait indefinitely, 
		choose a reasonable value for `wait` (e.g. 20 seconds) and do so in a while loop like so:

		::

			while not thread_should_exit and not state_machine.transition('disconnected', 'connecting', wait=20 ):
					pass # timeout will occur every 20s unless transition occurs
			if thread_should_exit: return
			# perform actions here after successful transition

		This allows the thread to be responsive by setting `thread_should_exit=True`.

		The optional `func` argument allows the user to pass a callable operation which occurs
		within the context of the state transition (e.g. while the state machine is locked.)
		If `func` returns a True value, the transition will occur.  If `func` returns a non-
		True value or if an exception is thrown, the transition will not occur.  Any thrown
		exception is not caught by the state machine and is the caller's responsibility to handle.
		If `func` completes normally, this method will return the value returned by `func.`  If
		values for `args` and `kwargs` are provided, they are expanded and passed like so:  
		`func( *args, **kwargs )`.
		'''

		return self.transition_any( (from_state,), to_state, wait=wait, 
		                            func=func, args=args, kwargs=kwargs )
	
	
	def transition_any(self, from_states, to_state, wait=0.0, func=None, args=[], kwargs={} ):
		'''
		Transition from any of the given `from_states` to the given `to_state`.
		'''

		if not (isinstance(from_states,tuple) or isinstance(from_states,list)): 
				raise ValueError( "from_states should be a list or tuple" )

		for state in from_states:
			if not state in self.__states: 
				raise ValueError( "StateMachine does not contain from_state %s." % state )
		if not to_state in self.__states: 
			raise ValueError( "StateMachine does not contain to_state %s." % to_state )

		with self.lock:
			start = time.time()
			while not self.__current_state in from_states: 
				# detect timeout:
				if time.time() >= start + wait: return False
				self.lock.wait(wait)
			
			if self.__current_state in from_states: # should always be True due to lock
				
				return_val = True
				# Note that func might throw an exception, but that's OK, it aborts the transition
				if func is not None: return_val = func(*args,**kwargs)

				# some 'false' value returned from func, 
				# indicating that transition should not occur:
				if not return_val: return return_val 

				logging.debug(' ==== TRANSITION %s -> %s', self.__current_state, to_state)
				self.__current_state = to_state
				self.lock.notifyAll()
				return return_val  # some 'true' value returned by func or True if func was None
			else:
				logging.error( "StateMachine bug!!  The lock should ensure this doesn't happen!" )
				return False


	def transition_ctx(self, from_state, to_state, wait=0.0):
		if not from_state in self.__states: 
			raise ValueError( "StateMachine does not contain from_state %s." % state )
		if not to_state in self.__states: 
			raise ValueError( "StateMachine does not contain to_state %s." % to_state )

		return _StateCtx(self, from_state, to_state, wait)

	
	def ensure(self, state, wait=0.0):
		'''
		Ensure the state machine is currently in `state`, or wait until it enters `state`.
		'''
		return self.ensure_any( (state,), wait=wait )


	def ensure_any(self, states, wait=0.0):
		'''
		Ensure we are currently in one of the given `states`
		'''
		if not (isinstance(states,tuple) or isinstance(states,list)): 
			raise ValueError('states arg should be a tuple or list')

		for state in states:
			if not state in self.__states: 
				raise ValueError( "StateMachine does not contain state '%s'" % state )

		with self.lock:
			start = time.time()
			while not self.__current_state in states: 
				# detect timeout:
				if time.time() >= start + wait: return False
				self.lock.wait(wait)
			return self.__current_state in states # should always be True due to lock

	
	def reset(self):
		# TODO need to lock before calling this? 
		self.transition(self.__current_state, self._default_state)


	def _set_state(self, state): #unsynchronized, only call internally after lock is acquired
		self.__current_state = state
		return state


	def current_state(self):
		'''
		Return the current state name.
		'''
		return self.__current_state


	def __getitem__(self, state):
		'''
		Non-blocking, non-synchronized test to determine if we are in the given state.
		Use `StateMachine.ensure(state)` to wait until the machine enters a certain state.
		'''
		return self.__current_state == state
	

class _StateCtx:

	def __init__( self, state_machine, from_state, to_state, wait ):
		self.state_machine = state_machine
		self.from_state = from_state
		self.to_state = to_state
		self.wait = wait
		self._timeout = False

	def __enter__(self):
		self.state_machine.lock.acquire()
		start = time.time()
		while not self.state_machine[ self.from_state ]: 
			# detect timeout:
			if time.time() >= start + self.wait: 
				logging.debug('StateMachine timeout while waiting for state: %s', self.from_state )
				self._timeout = True # to indicate we should not transition
				break
			self.state_machine.lock.wait(self.wait)

		logging.debug('StateMachine entered context in state: %s', 
				self.state_machine.current_state() )
		return self.state_machine

	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_val is not None:
			logging.exception( "StateMachine exception in context, remaining in state: %s\n%s:%s", 
				self.state_machine.current_state(), exc_type.__name__, exc_val )			
		elif not self._timeout:
			logging.debug(' ==== TRANSITION %s -> %s', 
					self.state_machine.current_state(), self.to_state)
			self.state_machine._set_state( self.to_state )

		self.state_machine.lock.notifyAll()
		self.state_machine.lock.release()
		return False # re-raise any exception

