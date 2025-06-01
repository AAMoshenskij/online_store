from redis import Redis
from config.settings import REDIS_HOST, REDIS_PORT

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
