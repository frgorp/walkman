#!/usr/bin/env python2
import cherrypy
import urllib2
from mako.template import Template
from mako.lookup import TemplateLookup
from pandora import Pandora
from pandora.connection import PandoraConnection
proxy_support = urllib2.ProxyHandler({"http" : "127.0.0.1:8118"})
opener = urllib2.build_opener(proxy_support)
urllib2.install_opener(opener)
templates = TemplateLookup(directories = ['html'])
pool_size = 2

pool = [PandoraConnection() for i in xrange(pool_size)]

class Resource(object):
    def __init__(self, content):
        self.content = content

    exposed = True

    def GET(self):
        return self.to_html()

    def PUT(self):
        self.content = self.from_html(cherrypy.request.body.read())

    def to_html(self):
        html_item = lambda (name,value): '<div>{name}:{value}</div>'.format(**vars())
        items = map(html_item, self.content.items())
        items = ''.join(items)
        return '<html>{items}</html>'.format(**vars())

    @staticmethod
    def from_html(data):
        pattern = re.compile(r'\<div\>(?P<name>.*?)\:(?P<value>.*?)\</div\>')
        items = [match.groups() for match in pattern.finditer(data)]
        return dict(items)

class ResourceIndex(Resource):
    def to_html(self):
        html_item = lambda (name,value): '<div><a href="{value}">{name}</a></div>'.format(**vars())
        items = map(html_item, self.content.items())
        items = ''.join(items)
        return '<html>{items}</html>'.format(**vars())

class Root(object):
	@cherrypy.expose
	def index(self):
		session = cherrypy.session
		session.load()
		print session.keys()
		return self.portal() if session.has_key('user') else templates.get_template("login.html").render()
	@cherrypy.expose
	def login(self):
		return templates.get_template("login.html").render()
	@cherrypy.expose
	def authenticate(self, username, password):
		pandora = Pandora(pool[0])
		user = pandora.authenticate(username, password)
		try:
			cherrypy.session['user'] = {'userId': user['userId'], 'userAuthToken': user['userAuthToken']}
			#print songs
			#return self.portal()
			return templates.get_template("login_success.html").render()
		except ValueError:
			return "Login failed, please do an 180"
	
	@cherrypy.expose
	def player(self):
		return templates.get_template("player.html").render()
	@cherrypy.expose
	def register(self):
		return urllib2.urlopen("http://www.pandora.com/account/register")
	@cherrypy.expose
	def portal(self):
		pandora = Pandora(pool[0])
		user = cherrypy.session.get('user')
		try:
			stations = pandora.get_station_list(user)
			stations = [{'stationName': s['stationName'], 'stationId': s['stationId']} for s in stations]
			songs = pandora.get_next_song(user, stations[0]['stationId'])
			#songs = [{'name': s['songName'], 'm4a': s['audioUrlMap']['highQuality']['audioUrl'], 'mp3': s['additionalAudioUrl']} if s.has_key('songName') else None for s in songs]
			songs = filter(lambda x: x.has_key('songName'), songs)

			#print songs
			return templates.get_template("portal.html").render(
				userId = user['userId'], 
				userToken = user['userAuthToken'], 
				stations = stations,
				songs = songs
			)
		except ValueError:
			return "Login failed, please do an 180"
	@cherrypy.expose
	def get_more_songs(self, stationId):
		pandora = Pandora(pool[0])
		user = cherrypy.session.get('user')
		try:
			return pandora.get_next_song(user, u"%s" % stationId)
		except ValueError:
			return "failed"
class Api(object):
	pass

root = Root()
root.api = Api()

cherrypy.quickstart(root, '/', 'walkman.config')
