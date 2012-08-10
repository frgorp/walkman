#!/usr/bin/env python2
import cherrypy
import os
import urllib2
import json
import rsa
from mako.template import Template
from mako.lookup import TemplateLookup
from pandora import Pandora
from pandora.song import Song
from lib.pandora_pool import PandoraPool
from lib.song_processor import SongProcessor
#proxy_support = urllib2.ProxyHandler({"http" : "127.0.0.1:8118"})
#opener = urllib2.build_opener(proxy_support)
#urllib2.install_opener(opener)
templates = TemplateLookup(directories = ['html'])
pool_size = 2

pool = PandoraPool(pool_size, proxy = "http://127.0.0.1:8118")
processor = SongProcessor("spool/")

with open('crypto/privkey.pem') as privFile:
	privData = privFile.read()
key = rsa.PrivateKey.load_pkcs1(privData)
with open('crypto/pubkey.mod') as pubFile:
	pubModulus = pubFile.read()[:-1]

class PandoraApi(object):
	_LOVED = True
	_BAN = False

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
		pandora = Pandora(pool.getAgent())
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
		pandora = Pandora(pool.getAgent())
		user = cherrypy.session.get('user')
		print stationId
		user['stationId'] = stationId;
		fragment = pandora.get_fragment(user, u"%s" % stationId)
		songs = [vars(Song(info)) for info in filter(lambda x: x.has_key('songName'), fragment)]
		return	self.respond_success({'songs': songs})

	@cherrypy.expose
	def stations(self):
		pandora = Pandora(pool.getAgent())
		user = cherrypy.session.get('user')
		return self.respond_success(pandora.get_station_list(user))

	@cherrypy.expose
	def downvote(self, trackToken):
		pandora = Pandora(pool.getAgent())
		user = cherrypy.session.get('user')
		print trackToken
		response = pandora.rate_song(user, trackToken, PandoraApi._BAN)
		print response
		return self.respond_success()

	@cherrypy.expose
	def upvote(self, trackToken):
		pandora = Pandora(pool.getAgent())
		user = cherrypy.session.get('user')
		print trackToken
		response = pandora.rate_song(user, trackToken, PandoraApi._LOVED)
		print response
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

class Root(object):
	@cherrypy.expose
	def index(self):
		session = cherrypy.session
		return self.portal() if session.has_key('user') else self.login()
	@cherrypy.expose
	def login(self):
		return templates.get_template("login.html").render(
			pub_key = pubModulus
		)

	@cherrypy.expose
	def authenticate(self, crypted):
		pandora = Pandora(pool.getAgent())
		try:
			raw = rsa.decrypt(crypted.decode("hex"), key)
			info = json.loads(raw)
			user = pandora.authenticate(info['username'], info['password'])
			cherrypy.session['user'] = {'userId': user['userId'], 'userAuthToken': user['userAuthToken']}
			#print songs
			#return self.portal()
			return templates.get_template("login_success.html").render()
	#	except NameError:
	#		return "foo"
		except ValueError:
			return "Login failed, please do an 180"
			

	@cherrypy.expose
	def logout(self):
		cherrypy.session.delete()
		return templates.get_template("logout.html").render()
	
	#@cherrypy.expose
	#def player(self):
	#	return templates.get_template("player.html").render()

	@cherrypy.expose
	def register(self):
		return urllib2.urlopen("http://www.pandora.com/account/register")

	@cherrypy.expose
	def portal(self):
		pandora = Pandora(pool.getAgent())
		user = cherrypy.session.get('user')
		try:
			stations = pandora.get_station_list(user)
			stations = [{'stationName': s['stationName'], 'stationId': s['stationId']} for s in stations]
			chosenStation = user['stationId'] if user.has_key('stationId') else stations[0]['stationId']
			fragment = pandora.get_fragment(user, chosenStation)
			#print chosenStation
			#print songs[0]
			#songs = [{'name': s['songName'], 'm4a': s['audioUrlMap']['highQuality']['audioUrl'], 'mp3': s['additionalAudioUrl']} if s.has_key('songName') else None for s in songs]
			songs = [Song(info) for info in filter(lambda x: x.has_key('songName'), fragment)]

			#print songs
			return templates.get_template("portal.html").render(
				userId = user['userId'], 
				userToken = user['userAuthToken'], 
				stations = stations,
				songs = songs,
				stationId = chosenStation			)
		except ValueError:
			#return "Login failed, please do an 180"
			return self.login()
	
	@cherrypy.expose
	def download(self, song):
		target = song.split('/')[-1]
		return cherrypy.lib.static.serve_download("%s/%s/%s" % (current_dir, processor.spool, target))
	
	@cherrypy.expose
	def dom(self):
		return open('/root/walkman/html/dom.html')


#	@cherrypy.expose
#	def get_more_songs(self, stationId):
#		pandora = Pandora(pool.getAgent())
#		user = cherrypy.session.get('user')
#		try:
#			return pandora.get_next_song(user, u"%s" % stationId)
#		except ValueError:
#			return "failed"


root = Root()
root.api = PandoraApi()

current_dir = os.path.dirname(os.path.abspath(__file__))
cherrypy.quickstart(root, '/', 'walkman.config')
