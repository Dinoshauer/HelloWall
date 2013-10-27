from datetime import timedelta
from uuid import uuid4 as uuid
from redis import StrictRedis
from redis.exceptions import ConnectionError

__REDIS_HOST__ = 'localhost'
__REDIS_PORT__ = 6379

class WallMessage:
	def __init__(self, prefix='msg', timeout=timedelta(minutes=5)):
		self.prefix = prefix
		self.timeout = timeout
		self.r = StrictRedis(__REDIS_HOST__, port=__REDIS_PORT__)

	def post(self, message):
		key = '%(prefix)s:%(hash)s' % {'prefix': self.prefix, 'hash': uuid()}
		return self.r.setex(key, self.timeout, message)

	def read(self):
		try:
			keys = self.r.keys(self.prefix + '*')
			result = list()
			for key in keys:
				result.append((self.r.get(key), self.r.ttl(key)))
			return {'result': True if len(result) > 0 else False, 'data': result}, 200
		except ConnectionError, e:
			return {'result': False, 'error': 'Could not connect to redis, is the server started and accepting connections on %s:%s?' % (__REDIS_HOST__, __REDIS_PORT__)}, 503
		except Exception, e:
			return {'result': False, 'error': str(e)}, 500