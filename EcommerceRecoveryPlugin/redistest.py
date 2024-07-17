import redis

# Replace with your Redis server configuration
redis_host = '127.0.0.1'  # Redis server IP (typically localhost)
redis_port = 6379          # Redis server port

try:
    # Connect to Redis
    r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

    # Test connection by setting and getting a key
    r.set('test_key', 'Hello Redis!')
    value = r.get('test_key')
    print(f'Redis connected successfully. Value retrieved: {value}')

except redis.ConnectionError as e:
    print(f'Error connecting to Redis: {e}')
