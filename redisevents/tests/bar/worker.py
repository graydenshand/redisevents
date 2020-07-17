from redisevents.redisevents import Worker
from .bar import Bar

worker = Worker()

@worker.on('foo', "update")
def test(test):
	if bool(test) == False:
		print('test')
	else:
		print('tested')


@worker.on('test', 'initiate')
def handle_test():
	print("Bar handled event from test")
	return Bar().bar_action()

if __name__ == "__main__":
	print(worker._events)
	worker.listen()
