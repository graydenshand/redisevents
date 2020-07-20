import redis
from redis.exceptions import ResponseError
from datetime import datetime
import functools
from .config import redis_url, pending_event_timeout, worker_timeout
import json
import uuid

class Worker:
	# self._evnets = {
	# 	"bar": {
	# 		"update": Foo.foo_action
	# 	},
	# 	"stream": {
	# 		"action": func
	# 	}
	# }

	def __init__(self, name):
		"""
		name: string name for consumer group
		"""
		self._events = {}
		self.name = name


	def on(self, stream, action):
		"""
		Wrapper to register a function to an event

		Usage:
		@worker.on("foo", "bar")
		def foo_bar_handler(arg1, arg2, kwarg1=val):
			...

		"""
		def decorator(func):
			self.register_event(stream, action, func)
			return func
		return decorator

	def register_event(self, stream, action, func):
		"""
		Map an event (stream + action) to a function

		Usage:
		def foo_bar_handler(arg1, arg2, kwarg1=val):
			...
		worker.register_event("foo", "bar", foo_bar_handler)
		"""
		if stream in self._events.keys():
			self._events[stream][action] = func
		else:
			self._events[stream] = {action: func}

	def listen(self):
		"""	
		- - Main Event Loop - -
		Establish redis connection
		Create consumer group if it doesn't already exist
		Generate a unique string to set as consumer/worker id
		Claim and handleany pending events from idle/failed workers
		Delete records of idle/failed workers
		Run forever:
			Wait for an event from the specified streams
			Dispatch to appropriate event handler
			Claim and handle any pending events from idle/failed workers
		"""
		self._r = redis.Redis.from_url(redis_url)
		self._create_consumer_group()
		streams = {key: ">" for key in self._events.keys()}
		self._generate_worker_id()
		self._claim_and_handle_pending_events()
			self._clear_idle_workers()
		while True:
			event = self._r.xreadgroup(self.name, self._worker_id, streams, 1, 0)
			self._dispatch(event)
			self._claim_and_handle_pending_events()

	def _dispatch(self, event):
		"""
		Call a function given an event

		If the event has been registered, the registered function will be called with the passed params.
		
		After running function, acknowledge the event has been processed. 
		"""
		e = Event(event=event)
		if e.action in self._events[e.stream].keys():
			func = self._events[e.stream][e.action]
			print(f"{datetime.now()} - Stream: {e.stream} - {e.event_id}: {e.action} {e.data}")
			self._r.xack(e.stream, self.name, e.event_id)
			result = func(**e.data)
			return result

	def _create_consumer_group(self):
		"""
		Create consumer groups for specified streams

		Indempotent, fails silently if groups already createed
		"""	
		for key in self._events.keys():
			try:
				# check if stream exists already
				self._r.xinfo_stream(key)
				mkstream = False
			except ResponseError:
				mkstream = True
			try:
				self._r.xgroup_create(key, self.name,id=u'$', mkstream=mkstream)
			except ResponseError:
				pass

	def _generate_worker_id(self):
		"""
		Create a unique name for this worker to register with the redis consumer group
		"""
		self._worker_id = self.name + f"-{uuid.uuid4()}"
		print(self._worker_id)
		return self._worker_id

	def _claim_and_handle_pending_events(self):
		"""
		Claim pending events that have been idle for > 30 secods, process immediately.

		Delete workers that appear to have stalled permanently (12 hours)
		"""
		for k in self._events.keys():
			pending_events = self._r.xpending_range(k, self.name, min="-", max="+", count=1000)
			if len(pending_events) > 0:
				event_ids = [event['message_id'] for event in pending_events]
				self._r.xclaim(k, self.name, self._worker_id, pending_event_timeout, event_ids)
				streams = {key: "0" for key in self._events.keys()}
				pending_events = self._r.xreadgroup(self.name, self._worker_id, streams, None, 0)
				for stream in pending_events:
					for event in stream[1]:
						formatted_event = [[stream[0], [event]]]
						self._dispatch(formatted_event)
		
	def _clear_idle_workers(self):	
		"""
		Delete consumers from redis consumergroups that have been idle
		for longer than WORKER_TIMEOUT milliseconds.
		"""
		for k in self._events.keys():
			existing_workers = self._r.xinfo_consumers(k, self.name)
			for worker in existing_workers:
				if worker['idle'] > worker_timeout:
					self._r.xgroup_delconsumer(k, self.name, worker['name'])


class Event():
	"""
	Abstraction for an event 
	"""
	def __init__(self, stream="", action="", data={}, event=None):
		self.stream = stream
		self.action = action
		self.data = data
		self.event_id=None
		if event:
			self.parse_event(event)

	def parse_event(self, event):
		"""
		Given a redis event, create an Event object
		"""
		# event = [[b'bar', [(b'1594764770578-0', {b'action': b'update', b'test': b'True'})]]]
		self.stream = event[0][0].decode('utf-8')
		self.event_id = event[0][1][0][0].decode('utf-8')
		self.data = event[0][1][0][1]
		self.action = self.data.pop(b'action').decode('utf-8')
		params = {}
		for k, v in self.data.items():
			params[k.decode('utf-8')] = json.loads(v.decode('utf-8'))
		self.data = params

	def publish(self, redis_conn):
		"""
		Given a redis connection, publish this event
		"""
		body = {
			"action": self.action
		}
		for k, v in self.data.items():
			body[k] = json.dumps(v, default=str)

		redis_conn.xadd(self.stream, body)



class Producer:
	"""
	Abstraction for a service (module) that publishes events about itself

	Manages stream information and can publish events
	"""
	# stream = None
	# _r = redis.Redis(host="localhost", port=6379, db=0)

	def __init__(self, stream):
		self.stream = stream
		self._r = redis.Redis.from_url(redis_url)

	def send_event(self, action, data={}):
		"""
		Create an event and publish it to this producer's stream
		"""
		e = Event(stream=self.stream, action=action, data=data)
		e.publish(self._r)

	def event(self, action):
		"""
		Wrap a function, declaring it as an event.

		An event with the specified action (along with any args and kwargs of the wrapped function)
		is published after the wrapped function runs

		Usage
		@producer.event('update')
		def some_action(arg1, arg2, kwarg1=val):
			...

		"""
		def decorator(func):
			@functools.wraps(func)
			def wrapped(*args, **kwargs):
				result = func(*args, **kwargs)
				arg_keys = func.__code__.co_varnames[1:-1]
				for i in range(1, len(args)):
					kwargs[arg_keys[i-1]] = args[i]
				self.send_event(action, kwargs)
				return result			
			return wrapped
		return decorator




#####################
###### DEMO #########
#####################

worker = Worker("foo-bar")

@worker.on('bar', "update")
def test(test):
	if bool(test) == False:
		print('test')
	else:
		print('tested')

if __name__ == "__main__":
	worker.listen()



