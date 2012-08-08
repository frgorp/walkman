#!/usr/bin/env python2
import cherrypy
import os
import urllib2
import json
import rsa
from mako.template import Template
from mako.lookup import TemplateLookup
from pandora import Pandora
from lib.pandora_pool import PandoraPool
from lib.song_processor import SongProcessor
#proxy_support = urllib2.ProxyHandler({"http" : "127.0.0.1:8118"})
#opener = urllib2.build_opener(proxy_support)
#urllib2.install_opener(opener)
templates = TemplateLookup(directories = ['html'])
pool_size = 2

pool = PandoraPool(pool_size, proxy = "127.0.0.1:8118")
processor = SongProcessor("spool/")

with open('crypto/privkey.pem') as privFile:
	privData = privFile.read()
key = rsa.PrivateKey.load_pkcs1(privData)
with open('crypto/pubkey.mod') as pubFile:
	pubModulus = pubFile.read()[:-1]

class PandoraApi(object):
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
		return	self.respond_success(self.process_songs(pandora.get_next_song(user, u"%s" % stationId)))

	@cherrypy.expose
	def stations(self):
		pandora = Pandora(pool.getAgent())
		user = cherrypy.session.get('user')
		return self.respond_success(pandora.get_station_list(user))

	@cherrypy.expose
	def downvote(self, trackToken):
		return self.respond_success()

	@cherrypy.expose
	def upvote(self, trackToken):
		return self.respond_success()

	@cherrypy.expose
	def generateDownloadLink(self, title, artist, mp3Url, poster):
		result = processor.downloadSong(title, artist, mp3Url, poster)
		return self.respond_success(result)
		
	def respond_success(self, data={}):
		data['success'] = True
		return json.dumps(data)

	def respond_failure(self, data):
		data['success'] = False
		return json.dumps(data)

	def process_songs(self, songs):
		songs = filter(lambda x: x.has_key('songName'), songs)
		return {'songs': [
			{
				'title': song['songName'],
				'artist': song['artistName'],
				'mp3': song['additionalAudioUrl'],
				'm4a': song['audioUrlMap']['highQuality']['audioUrl'],
				'poster': song['albumArtUrl'],
				'trackToken': song['trackToken'],
				'free': True
			}
			for song in songs
		]}

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
			songs = pandora.get_next_song(user, chosenStation)
			print chosenStation
			#songs = [{'name': s['songName'], 'm4a': s['audioUrlMap']['highQuality']['audioUrl'], 'mp3': s['additionalAudioUrl']} if s.has_key('songName') else None for s in songs]
			songs = filter(lambda x: x.has_key('songName'), songs)

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
