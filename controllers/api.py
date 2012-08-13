import cherrypy
import json
from lib.utils import retrieve_user_info
from pandora import Pandora
from pandora.song import Song
from models.pandora import *

class PandoraApi(object):
	_LOVED = True
	_BAN = False

	def __init__(self, pool, connector, templates):
		self.templates = templates
		self.pool = pool
		self.Connector = connector

	@cherrypy.expose
	def index(self):
		cherrypy.lib.jsontools.json_out()
		session = cherrypy.session
		info = {}
		for key in session.keys():
			info[key] = session[key]
		return self.respond_success()

	@cherrypy.expose
	def authenticate(self, crypted):
		pandora = Pandora(self.pool.getAgent())
		try:
			raw = rsa.decrypt(crypted.decode("hex"), key)
			info = json.loads(raw)
			user = pandora.authenticate(info['username'], info['password'])
			cherrypy.session['user'] = {'userId': user['userId'], 'userAuthToken': user['userAuthToken']}
			return self.respond_success()
		except KeyError:
			return self.respond_failure()

	@cherrypy.expose
	def songs(self, stationId):
		user, walkman_user, connector = retrieve_user_info(cherrypy.session, self.Connector)
		pandora = Pandora(self.pool.getAgent())
		walkman_user.station_id = stationId
		fragment = pandora.get_fragment(user, u"%s" % stationId)
		songs = [vars(Song(info)) for info in filter(lambda x: x.has_key('songName'), fragment)]
		for song in songs:
			walkman_user.listened_songs.append(PandoraListenedSong(
				song['title'],
				song['artist'],
				song['album'],
				song['trackToken'],
				liked = song['songRating'] if song['songRating'] else None
			))
		walkman_user.listened_songs = walkman_user.listened_songs[-100:]
		connector.commit()
		connector.close()
		return	self.respond_success({'songs': songs})

	@cherrypy.expose
	def stations(self):
		pandora = Pandora(self.pool.getAgent())
		user = cherrypy.session.get('user')
		return self.respond_success(pandora.get_station_list(user))

	@cherrypy.expose
	def downvote(self, trackToken):
		pandora = Pandora(self.pool.getAgent())
		user, walkman_user, connector = retrieve_user_info(cherrypy.session, self.Connector)
		response = pandora.rate_song(user, trackToken, PandoraApi._BAN)
		try:
			song = session.query(PandoraListenedSong).filter_by(pandora_user_id=walkman_user.id).filter_by(pandora_track_token=trackToken).first()
			song.liked = False
			connector.commit()
		except:
			pass
		finally:
			connector.close()
		return self.respond_success()

	@cherrypy.expose
	def upvote(self, trackToken):
		pandora = Pandora(self.pool.getAgent())
		user, walkman_user, connector = retrieve_user_info(cherrypy.session, self.Connector)
		response = pandora.rate_song(user, trackToken, PandoraApi._LOVED)
		try:
			song = session.query(PandoraListenedSong).filter_by(pandora_user_id=walkman_user.id).filter_by(pandora_track_token=trackToken).first()
			song.liked = True
			connector.commit()
		except:
			pass
		finally:
			connector.close()
		return self.respond_success()

	@cherrypy.expose
	def generateDownloadLink(self, title, artist, mp3Url, poster):
		result = processor.downloadSong(title, artist, mp3Url, poster)
		return self.respond_success(result)

	def respond_success(self, data={}, skip_dump=False):
		data['success'] = True
		return data if skip_dump else json.dumps(data)

	def respond_failure(self, data={}, skip_dump=False):
		data['success'] = False
		return data if skip_dump else json.dumps(data)

