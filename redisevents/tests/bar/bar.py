from redisevents.redisevents import Producer
from datetime import datetime
import json

class Bar():
	#stream = "bar"
	ep = Producer("bar")

	@ep.event("update")
	def bar_action(self):
		print("BAR ACTION")
		#ep.send_event("update", {"test": str(True)})
		return "BAR ACTION"

if __name__ == '__main__':
	Bar().bar_action()