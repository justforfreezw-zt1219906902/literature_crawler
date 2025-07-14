from app.config.config import get_env
from extensions.ext_redis import redis_client



def add_to_array(key, value,timeout):

    redis_client.rpush(key, value)
    if redis_client.ttl(key) <= 0:
        redis_client.expire(key, timeout)


def get_array(key):
    elements = redis_client.lrange(key, 0, -1)
    redis_client.expire(key, 3600)
    return [element.decode('utf-8') for element in elements]


def get_hash_field(key, field):

    value = redis_client.hget(key, field)
    return value.decode('utf-8') if value else None

def get_hash_map(key):
    value = redis_client.hgetall(key)
    decoded_value = {k.decode('utf-8'): v.decode('utf-8') for k, v in value.items()}
    return decoded_value


def batch_hash_set(key, map,timeout):
    redis_client.hmset(key,map)
    redis_client.expire(key, timeout)
def get_hash_map_fields(key):

    fields = redis_client.hgetall(key)
    decoded_fields = {k.decode('utf-8'): v.decode('utf-8') for k, v in fields.items()}
    return decoded_fields





