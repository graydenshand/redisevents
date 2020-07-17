# RedisEvents

A simple package for coordinating microservices using redis streams.

# Installation
Install using pip ([redisevents](https://pypi.org/project/redisevents/)):
```
pip install redisevents
```

# Usage
There are three classes in this module: [Producer](#producer), [Worker](#worker), and [Event](#event).

A Worker listens for Events sent by a Producer, and will envoke functions depending on the events set.

## Configuration
The only thing to configure is the connection string for your redis server. It defaults to `redis://localhost:6379`, but you can change this by setting your `REDIS_URL` environment variable.

## Example Worker
Here's a simple example of a worker module.
```{python}
# worker.py
worker = Worker()

@worker.on('bar', "update")
def test(foo, test=False):
	if bool(test) == False:
		print('test')
	else:
		print('tested')

if __name__ == "__main__":
	worker.listen(host='127.0.0.1', port=6379, db=0)

```
In the first line, we initialize the Worker class. Then we register functions as event listeners using the `@worker.on()` wrapper function. `@worker.on()` takes two parameters, `stream` and `action`. These two parameters uniquely define an event that will be sent by a producer. When this event is delivered to redis, this worker will envoke the `test()` function. In essence, this is similar to how you would set up a simple web application in Flask. However, instead of definining HTTP endpoints to route, you define a set of events to route. 

Finally, the last two lines of the file run the event loop that listens for the events specified above, and calls the functions we have mapped to those events. 

Run the file with `python worker.py` to start listening. 


## Example Producer
A producer is just a module that emits events about itself, specifically about changes to it's state. Here is a simple example of a producer module.

```{python}
# bar.py
class Bar():
	ep = Producer("bar")

	@ep.event("update")
	def bar_action(self, foo, **kwargs):
		print("BAR ACTION")
		return "BAR ACTION"

if __name__ == '__main__':
	Bar().bar_action("test", test="True")
```
We create a class, `Bar` that has one method, `bar_action()`. On line 2, we instantiate a Producer as a class-variable of Bar. This ensures that all instances of the class share the same redis connection. We pass "bar" as the Producer's stream, meaning that all events from this producer will be emitted into the "bar" stream. 

We then register `Bar.bar_action()` as an event. After it runs, it will send emit an event to the "bar" stream with `action="update"`. Looking back at the example Worker, you'll see that this event will trigger the worker's `test()` function. Additionally, the args and kwargs of `bar_action` (`foo="test"` and `test=False`) are sent as kwargs to the event handler (`test()`).

Finally, the last two lines merely trigger a test, calling `Bar.bar_action()`. Run this with `python bar.py`


# API
## Event
## Producer
## Worker
