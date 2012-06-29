#!/usr/bin/env python2
import cherrypy
import pandora
from mako.template import Template
from mako.lookup import TemplateLookup
templates = TemplateLookup(directories = ['html'])

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
		return templates.get_template("index.html").render()
	@cherrypy.expose
	def pandoraLogin(self, username, password):
		return templates.get_template("portal.html").render()

class Api(object):
	pass

root = Root()
root.api = Api()
#root.api.sidewinder = Resource({'color': 'red', 'weight': 176, 'type': 'stable'})
root.api.teebird = Resource({'color': 'green', 'weight': 173, 'type': 'overstable'})
#root.api.blowfly = Resource({'color': 'purple', 'weight': 169, 'type': 'putter'})
#root.api.resource_index = ResourceIndex({'sidewinder': 'sidewinder', 'teebird': 'teebird', 'blowfly': 'blowfly'})

cherrypy.quickstart(root, '/', 'walkman.config')
