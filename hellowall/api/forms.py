from datetime import timedelta
from uuid import uuid4 as uuid
from redis import StrictRedis
from redis.exceptions import ConnectionError
import bleach

__REDIS_HOST__ = 'localhost'
__REDIS_PORT__ = 6379

class WallException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class WallMessage:
	def __init__(self, prefix='msg', timeout=timedelta(minutes=60)):
		self.prefix = prefix
		self.timeout = timeout
		self.r = StrictRedis(__REDIS_HOST__, port=__REDIS_PORT__)

	def post(self, message):
		try:
			key = '%(prefix)s:%(hash)s' % {'prefix': self.prefix, 'hash': uuid()}
			return {'result': True, 'message': self.r.setex(key, self.timeout, bleach.clean(message))}, 200
		except ConnectionError, e:
			return {'result': False, 'error': 'Could not connect to redis, is the server started and accepting connections on %s:%s?' % (__REDIS_HOST__, __REDIS_PORT__)}, 503
		except Exception, e:
			return {'result': False, 'error': str(e)}, 500

	def read(self, simple=False):
		try:
			keys = self.r.keys(self.prefix + '*')
			result = list()
			for key in keys:
				value = self.r.get(key)
				if value not in result:
					if simple:
						result.append(value)
					else:
						result.append((value, key))
			return {'result': True if len(result) > 0 else False, 'data': result}, 200
		except ConnectionError, e:
			return {'result': False, 'error': 'Could not connect to redis, is the server started and accepting connections on %s:%s?' % (__REDIS_HOST__, __REDIS_PORT__)}, 503
		except Exception, e:
			return {'result': False, 'error': str(e)}, 500

	def sticky(self, key):
		try:
			result = self.r.persist(key)
			if result > 0:
				return {'result': True, 'message': 'Post stickied.'}, 200
			else:
				return {'result': False, 'error': 'Key not found or key does not have a timeout.'}, 404
		except Exception, e:
			return {'result': False, 'error': str(e)}, 500

	def delete(self, key):
		try:
			result = self.r.delete(key)
			if result > 0:
				return {'result': True, 'message': 'Post deleted.'}, 200
			else:
				return {'result': False, 'error': 'No posts found.'}, 404
		except Exception, e:
			return {'result': False, 'error': str(e)}, 500
