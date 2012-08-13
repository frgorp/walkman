#!/usr/bin/env python2
import cherrypy
import os
import rsa
import thread
from controllers import *
from mako.lookup import TemplateLookup
from pandora import Pandora
from pandora.song import Song
from lib.pandora_pool import PandoraPool
from lib.song_processor import SongProcessor
from lib.workers import _worker_paddler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

cherrypy.config.update('walkman.config')
# init some handlers
templates = TemplateLookup(directories = ['html'])
with open('crypto/privkey.pem') as privFile:
	privData = privFile.read()
privKey = rsa.PrivateKey.load_pkcs1(privData)
with open('crypto/pubkey.mod') as pubFile:
	pubKey = pubFile.read()[:-1]

pool = PandoraPool(cherrypy.config['pandora_pool_size'], 
	proxy = cherrypy.config['pandora_proxy'] if 
		cherrypy.config.has_key('pandora_proxy') else None
)
processor = SongProcessor("spool/")

engine = create_engine(cherrypy.config['database'], echo=False)
Connector = sessionmaker(bind=engine)



# bootstrap app
root = Root(pool, Connector, templates, privKey, pubKey)
root.api = PandoraApi(pool, Connector, templates)
root.views = PandoraViews(pool, Connector, templates)
current_dir = os.path.dirname(os.path.abspath(__file__))
cherrypy.tree.mount(root, '/', 'walkman.config')

# start minion threads
thread.start_new_thread(_worker_paddler, (pool, Connector(),))

# main app loop
cherrypy.engine.start()
cherrypy.engine.block()
