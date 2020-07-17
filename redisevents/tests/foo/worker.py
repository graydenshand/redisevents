from redisevents.redisevents import Worker

worker = Worker()

@worker.on('bar', "update")
def handle_bar_update():	
	print("Foo handled event from bar")

if __name__ == "__main__":
	worker.listen()
