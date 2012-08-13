import cherrypy
from lib.utils import retrieve_user_info

class PandoraViews(object):
	def __init__(self, pool, Connector, templates):
		self.templates = templates
		self.Connector = Connector
		self.pool = pool

	@cherrypy.expose
	def index(self):
		return "index"

	@cherrypy.expose
	def history(self):
		user, walkman_user, connector = retrieve_user_info(cherrypy.session, self.Connector)
		return self.templates.get_template("views/history.html").render(
			history = walkman_user.listened_songs
		)

	@cherrypy.expose
	def settings(self):
		user, walkman_user, connector = retrieve_user_info(cherrypy.session, self.Connector)
		walkman_user.setKeepalive(True)
		connector.commit()
		return self.self.templates.get_template("views/settings.html").render(data=walkman_user.keepalive_info)
	
