import cherrypy
import rsa
import json
from pandora import Pandora
from lib.utils import retrieve_user_info
from models.pandora import *
from sqlalchemy.orm.exc import NoResultFound

class Root(object):
	def __init__(self, pool, Connector, templates, privKey, pubKey):
		self.pool = pool
		self.Connector = Connector
		self.templates = templates
		self.privKey = privKey
		self.pubKey = pubKey

	@cherrypy.expose
	def index(self):
		session = cherrypy.session
		return self.portal() if session.has_key('user') else self.login()
	@cherrypy.expose
	def login(self):
		return self.templates.get_template("login.html").render(
			pub_key = self.pubKey
		)

	@cherrypy.expose
	def authenticate(self, crypted):
		pandora = Pandora(self.pool.getAgent())
		try:
			raw = rsa.decrypt(crypted.decode("hex"), self.privKey)
			info = json.loads(raw)
			user = pandora.authenticate(info['username'], info['password'])
			cherrypy.session['user'] = {'userId': user['userId'], 'userAuthToken': user['userAuthToken']}
			connector = self.Connector()
			try:
				walkman_user = connector.query(PandoraUser).filter_by(user_id=int(user['userId'])).one()
				walkman_user.user_auth_token = user['userAuthToken']
				if walkman_user.keepalive:
					walkman_user.keepalive_info.resetBeats()
					walkman_user.keepalive_info.setLive(True)
			except NoResultFound:
				walkman_user = PandoraUser(user['userId'], user['userAuthToken'])

			connector.add(walkman_user)
			connector.commit() 
			cherrypy.session['walkmanId'] = walkman_user.id
			#print songs
			#return self.portal()
			return self.templates.get_template("login_success.html").render()
	#	except NameError:
	#		return "foo"
		except ValueError:
			return "Login failed, please do an 180"
			

	@cherrypy.expose
	def logout(self):
		cherrypy.session.delete()
		return self.templates.get_template("logout.html").render()
	
	@cherrypy.expose
	def portal(self):
		pandora = Pandora(self.pool.getAgent())
		user, walkman_user, connector = retrieve_user_info(cherrypy.session, self.Connector)
		try:
			stations = pandora.get_station_list(user)
			stations = [{'stationName': s['stationName'], 'stationId': s['stationId']} for s in stations]
			stationIds = [long(station['stationId']) for station in stations]
			chosenStation = walkman_user.station_id if walkman_user.station_id in stationIds else stationIds[0]
			walkman_user.station_id = chosenStation
			connector.commit()
			return self.templates.get_template("portal.html").render(
				userId = user['userId'], 
				userToken = user['userAuthToken'], 
				stations = stations,
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


