from sqlalchemy import *
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class PandoraUser(Base):
	__tablename__ = 'pandora_users'
	
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, nullable=False)
	user_auth_token = Column(String(50))
	station_id = Column('station_id', BigInteger)
	keepalive = Column('keepalive', Boolean)
	keepalive_info = relationship('PandoraKeepalive', uselist=False, backref='pandora_users', cascade='all, delete, delete-orphan')

	listened_songs = relationship("PandoraListenedSong", order_by="PandoraListenedSong.id", backref="pandora_users", cascade="all, delete, delete-orphan")

	def __init__(self, userId, userAuthToken=None):
		self.user_id = userId
		self.user_auth_token = userAuthToken
		self.keepalive = False

	def setKeepalive(self, state):
		if not self.keepalive and state:
			self.keepalive_info = PandoraKeepalive(True)
		elif self.keepalive and not state:
			self.keepalive_info = None
		self.keepalive = state
	
	def __repr__(self):
		return "<User('%s','%s', '%s')>" % (self.user_id, self.user_auth_token, self.keepalive)

class PandoraListenedSong(Base):
	__tablename__ = 'pandora_listened_songs'

	id = Column(Integer, primary_key=True)
	title = Column('title', String(32), nullable=False)
	artist = Column('artist', String(32), nullable=False)
	album = Column('album', String(32), nullable=False)
	pandora_track_token = Column('pandora_track_token', String(120), nullable=False)
	liked = Column('liked', Boolean)
	pandora_user_id = Column('pandora_user_id', Integer, ForeignKey('pandora_users.id'))
	
	#pandora_user = relationship("PandoraUser", backref=backref('pandora_listened_songs', order_by=id), cascade="all, delete, delete-orphan")

	def __init__(self, title, artist, album, pandoraTrackToken, liked=None):
		self.title = title
		self.artist = artist
		self.album = album
		self.pandora_track_token = pandoraTrackToken
		self.liked = liked
		
	def __repr__(self):
		return "<Song('%s', '%s', '%s', '%s', '%s')>" % (self.title, self.artist, self.album, self.pandora_track_token, self.liked)

class PandoraKeepalive(Base):
	__tablename__ = 'pandora_keepalive'
	id = Column('id', Integer, primary_key=True)
	last_heartbeat = Column('last_heartbeat', DateTime)
	alive = Column('alive', Boolean, nullable=False)
	beats = Column('beats', SmallInteger, nullable=False)
	user_id = Column('user_id', Integer, ForeignKey('pandora_users.id'))

	user = relationship('PandoraUser', uselist=False, backref='pandora_keepalive')

	def __init__(self, alive=False):
		self.beats = 0
		self.alive = alive
		
	def beat(self):
		if self.alive:
			self.beats += 1
			self.last_heartbeat = datetime.utcnow()

	def setLive(self, state):
		self.alive = state

	def resetBeats(self):
		self.beats = 0
