from pandora import Pandora
from pandora.connection import PandoraConnection
from datetime import datetime
from datetime import timedelta
from threading import Lock

class PandoraAgent(PandoraConnection):
	def __init__(self, expireDate, proxy):
		super(PandoraAgent, self).__init__(proxies={'http': proxy} if proxy else {})
		self.expire = expireDate

	def isExpired(self):
		return self.expire <= datetime.now()

	def setExpireDate(self, expireDate):
		self.expire = expireDate

class PandoraPool(object):
	def __init__(self, poolSize, proxy=None, expireTime=3600):
		self.size = poolSize
		self.proxy = proxy
		self.expire = expireTime
		self.pool = [self.createPandoraAgent() for i in xrange(self.size)]
		self.mutex = Lock()

	def createPandoraAgent(self):
		return PandoraAgent(datetime.now() + timedelta(0, self.expire), self.proxy)

	def refreshPandoraAgent(self, agent):
		if agent.isExpired():
			agent.authenticate_connection()
			agent.setExpireDate(datetime.now() + timedelta(0, self.expire))
		return agent

	def getAgent(self):
		try:
			return self.refreshPandoraAgent(self.pool.pop())
		except IndexError:
			return self.createPandoraAgent()

	def hasAvailableConnections(self):
		return len(self.pool) > 0

	def releaseAgent(self, agent):
		self.mutex.acquire()
		if len(self.pool) < self.size:
			self.pool.append(agent)
		self.mutex.release()
		
