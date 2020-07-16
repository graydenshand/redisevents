import os

redis_url = os.environ.get("REDIS_URL")
if redis_url is None:
	redis_url = "redis://localhost:6379?db=0"