"""
This class represents the core modules of an individual service.

It can be envoked by both the web and worker processes.
This pattern abstracts the handling of events / requests from 
the actual work of the module

The module should be aware of it's own event stream,
and it should publish events detailing its behavior (changes to data). 
"""
from redisevents.redisevents import Producer



class Foo:

	ep = Producer("foo")

	@classmethod
	def foo_action(cls):
		"""
		This method represents some work that a service will do. 

		After doing the work, it publishes an event to alert other services of the change.
		"""
		print("FOO ACTION")
		return "FOO ACTION"
