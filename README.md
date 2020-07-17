# RedisEvents

A simple package for coordinating microservices using redis streams.

# Installation
Install using pip ([redisevents](https://pypi.org/project/redisevents/)):
```
pip install redisevents
```

# Usage
There are three classes in this module: [Producer](#producer), [Worker](#worker), and [Event](#event).

A Worker listens for Events sent by a Producer, and will envoke functions depending on the events sent.

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
*class* **Event**(*`stream="", action="", data={}, event=None`*)

A simple abstraction for Events. It implements a common interface used by the Producer and Worker classes to communicate.

### Attributes
**stream** *&lt;str&gt;* - the name of the redis stream the event was or will be published to

**action** *&lt;str&gt;* - an identifying name to classify the event. The `stream` and `action` attributes uniquely identify an event type

**data** *&lt;dict&gt;* - a dictionary of data associated with this event

**event_id** *&lt;str&gt;* - a unique event id assigned by redis


### Methods

**parse_event**(*`event`*)
* Parses the redis event message into an Event object, called by the worker when handling events.

**publish**(*`redis_conn`*)
* Publish this event to the passed redis connection.

## Producer
*class* **Producer**(*`stream`*)

A simple abstraction to produce/emit events. See [Example Producer](#example-producer) for an example.

### Attributes
**stream** *&lt;str&gt;* -- the name of the redis stream to which to publish events. 

### Methods
**send_event**(*`action, data={}`*)
* Creates and publishes an Event with the passed action and data to the stream defined upon instantiation.

**event**(*`action`*)
* Wrapper function that calls `send_event()` internally after running the wrapped function. Any args and kwargs passed to the wrapped function will be added to the Event's data attribute. The resulting code is often cleaner that calling the `send_event()` function inline, though it is less flexible in what data you can send. 

```{python}
# Publishing an event using send_event()

def bar_action(self, foo, **kwargs):
  print("BAR ACTION")
  kwargs['foo'] = foo
  ep.send_event("update", kwargs)
  return "BAR ACTION"


# Vs. Publishing an event with wrapper @event() function

@ep.event("update")
def bar_action(self, foo, **kwargs)
  print("BAR ACTION")
  return "BAR ACTION"

```

## Worker
Register event callbacks, and listen for events. See [Example Worker](#example-worker) for an example. 

### Methods
**register_event**(*`stream, action, func`*)
* Register a callback function for an event with a given stream and action.

**on**(*`stream, action`*)
* Wrapper function that calls `register_event` internally. This usually results in cleaner code that using the function inline.

**listen**()
* Runs the main event loop, listening for events and envoking the mapped callback functions. 

