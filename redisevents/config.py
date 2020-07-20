import os

redis_url = os.environ.get("REDIS_URL")
if redis_url is None:
	redis_url = "redis://localhost:6379"

pending_event_timeout = os.environ.get("PENDING_MESSAGE_TIMEOUT")
if pending_event_timeout is None:
	pending_event_timeout = 30000

worker_timeout = os.environ.get("WORKER_TIMEOUT")
if worker_timeout is None:
	worker_timeout = 30000
