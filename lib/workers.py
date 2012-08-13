import time
from models.pandora import *
from lib.utils import transform_walkman_to_user
from lib.pandora_pool import Pandora

def _worker_paddler(pool, session, intervalMinutes=30):
	users = session.query(PandoraUser).filter_by(keepalive=True).all()
	_runForever = True
	while _runForever:
		for user in users:
			# make a trivial api call
			try:
				if user.keepalive_info.alive:
					pandoraUser = transform_walkman_to_user(user)
					pandora = Pandora(pool.getAgent())
					pandora.get_station_list(pandoraUser)
					user.keepalive_info.beat()
					print "paddled %s" % user
				else:
					print "skipping paddle for %s because it's dead" % user
			except Exception as e:
				_dead = False
				user.keepalive_info.setLive(_dead)
				print "paddle failed for %s because %s" % (user, e)
		session.commit()
		time.sleep(60 * intervalMinutes)

