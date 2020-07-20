from redisevents.redisevents import Worker
from .bar import Bar

worker = Worker("bar")

@worker.on('foo', "update")
def test():
	print('tested')


@worker.on('test', 'initiate')
def handle_test():
	print("Bar handled event from test")
	return Bar().bar_action()

if __name__ == "__main__":
	worker.listen()
