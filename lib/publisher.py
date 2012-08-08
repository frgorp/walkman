# -*- coding: utf-8 -*-
import cherrypy
from cherrypy._cptools import HandlerWrapperTool
from lxml.etree import Element, tostring, _Element, parse, XSLT
from copy import deepcopy
import json
import yaml
import os
import sys
from types import GeneratorType

try:
    from pymongo.bson import ObjectId
except:
    class ObjectId(object): pass


if sys.version[0] == '2':
    dtypes = (unicode, str, int, float, ObjectId)
else:
    dtypes = (str, int, float, ObjectId)

def str_format(data):
    if sys.version[0] == '2':
        return unicode(data)
    else:
        if isinstance(data, bytes):
            return data.decode()
        return str(data)

def dict2etree(response_dict):
    document = Element('document')
    def _dict2etree(data, et=None):
        '''Iterates over a dict and produces a basic xml file'''
        if isinstance(data, dtypes):
            et.text = str_format(data)

        elif isinstance(data, list):
            for i,x in enumerate(data):
                tag = deepcopy(et)
                et.getparent().extend([tag])
                _dict2etree(x, tag)
            et.getparent().remove(et)

        elif isinstance(data, dict):
            for k, v in data.items():
                tag = Element(k)
                if et is None:
                    document.append(tag)
                else:
                    et.append(tag)
                _dict2etree(v, tag)
    _dict2etree(response_dict)
    return document


class Publisher(HandlerWrapperTool):
    lxmlext = None
    
    def __init__(self):
        self.extend = {}
        HandlerWrapperTool.__init__(self, self.publish)

    def _setup(self, *args, **kwargs):
        if cherrypy.request.config.get('tools.staticdir.on', False) or \
            cherrypy.request.config.get('tools.staticfile.on', False):
            return
        HandlerWrapperTool._setup(self, *args, **kwargs)
    
    def callable(self, format='xslt', template_dir='views/site', template='index.xsl', extend_xml={}):
        cherrypy.request.format = format
        HandlerWrapperTool.callable(self)
    
    def params(self):
        if 'format' in cherrypy.request.params:
            format = cherrypy.request.params.pop('format')
            cherrypy.request.format = format
        
    def publish(self, next_handler, *args, **kwargs):
        self.params()
        response_dict = next_handler(*args, **kwargs)
        if isinstance(response_dict, GeneratorType):
            response_dict = dict(response_dict)
        conf = self._merged_args()
        response = getattr(self, 'render_%s' % cherrypy.request.format)(response_dict, conf)
        return response

    def extend_xml(self, e):
        r = {}
        if isinstance(e, dict):
            for k, v in e.items():
                if hasattr(v, '__call__'):
                    r[k] = v()
                if isinstance(v, dict):
                    r[k] = v
        return r
    
    def render_raw(self, response_dict, conf):
        return response_dict
    
    def render_json(self, response_dict, conf):
        cherrypy.response.headers['Content-Type'] = 'text/json'
        return json.dumps(response_dict)

    def render_yaml(self, response_dict, conf):
        cherrypy.response.headers['Content-Type'] = 'text/yaml'
        return yaml.dump(response_dict)
    
    def render_xml(self, response_dict, conf):
        cherrypy.response.headers['Content-Type'] = 'text/xml'
        
        x = conf.get('extend_xml', False)
        if x:
            response_dict.update(self.extend_xml(x))

        document = dict2etree(response_dict)
        return tostring(document, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    def render_xslt(self, response_dict, conf):
        cherrypy.response.headers['Content-Type'] = 'text/html'
        
        x = conf.get('extend_xml', False)
        if x:
            response_dict.update(self.extend_xml(x))
                    
        document = dict2etree(response_dict)
        template = os.path.join(conf['template_dir'], conf.get('template', 'index.xsl'))
        cherrypy.response.template = template # for use outside of publisher, such as xslt extensions
        
        l = parse(open(template))
        xslt = XSLT(l, extensions=self.lxmlext)
        response = xslt(document)

        return tostring(response, pretty_print=True, method='html', xml_declaration=False, encoding='UTF-8')
