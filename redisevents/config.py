import os

redis_url = os.environ.get("RE_REDIS_URL")
if redis_url is None:
	redis_url = "redis://localhost:6379"

max_stream_length = os.environ.get("RE_MAX_STREAM_LENGTH")
if max_stream_length is None:
	max_stream_length = 1000 # Truncate streams to appx 1000 events