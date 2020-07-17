import redis
from datetime import datetime
import functools
from .config import redis_url
import json

class Worker:
	# streams = {
	# 	"bar": {
	# 		"update": Foo.foo_action
	# 	},
	# }

	def __init__(self):
		self._events = {}


	def on(self, stream, action):
		"""
		Wrapper to register a function to an event
		"""
		def decorator(func):
			self.register_event(stream, action, func)
			return func
		return decorator

	def register_event(self, stream, action, func):
		"""
		Map an event to a function
		"""
		if stream in self._events.keys():
			self._events[stream][action] = func
		else:
			self._events[stream] = {action: func}

	def listen(self):
		"""	
		Main event loop
		Establish redis connection from passed parameters
		Wait for events from the specified streams
		Dispatch to appropriate event handler
		"""
		self._r = redis.Redis.from_url(redis_url)
		streams = {key: "$" for key in self._events.keys()}
		print(streams)
		while True:
			event = self._r.xread(streams, None, 0) 
			# Call function that is mapped to this event
			self._dispatch(event)

	def _dispatch(self, event):
		"""
		Call a function given an event

		If the event has been registered, the registered function will be called with the passed params.
		"""
		e = Event(event=event)
		if e.action in self._events[e.stream].keys():
			func = self._events[e.stream][e.action]
			print(f"{datetime.now()} - Stream: {e.stream} - {e.event_id}: {e.action} {e.data}")
			return func(**e.data)


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
		e = Event(stream=self.stream, action=action, data=data)
		e.publish(self._r)

	def event(self, action):
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

worker = Worker()

@worker.on('bar', "update")
def test(test):
	if bool(test) == False:
		print('test')
	else:
		print('tested')

if __name__ == "__main__":
	worker.listen()



