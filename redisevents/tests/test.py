"""
To run this test

1. Start the bar worker with `python bar/worker.py`
2. Open a new terminal window and start the foo worker with `python foo/worker.py`
3. Open a new terminal window and run this script `python test.py`

"""
from redisevents.redisevents import Producer



if __name__ == "__main__":
	
	p = Producer("test")

	p.send_event("initiate", {})