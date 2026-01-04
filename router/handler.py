import redis
from rq import Queue
import os
import dotenv

dotenv.load_dotenv()

r_conn = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    decode_responses=False,
    username=os.getenv("REDIS_USERNAME"),
    password=os.getenv("REDIS_PASSWORD"),
)

q = Queue(connection=r_conn)