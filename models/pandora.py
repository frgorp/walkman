from sqlalchemy import *
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PandoraUser(Base):
	__tablename__ = 'pandora_users'
	
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, nullable=False)
	user_auth_token = Column(String(50))
	last_heartbeat = Column('last_heartbeat', DateTime)

	listenedSongs = relationship("PandoraListenedSong", order_by="PandoraListenedSong.id", backref="pandora_users")

	def __init__(self, userId, userAuthToken=None, lastHeartbeat=None):
		self.userId = userId
		self.userAuthToken = userAuthToken
		self.lastHeartbeat = lastHeartbeat
	

class PandoraListenedSong(Base):
	__tablename__ = 'pandora_listened_songs'

	id = Column(Integer, primary_key=True)
	title = Column('title', String(32), nullable=False)
	artist = Column('artist', String(32), nullable=False)
	album = Column('album', String(32), nullable=False)
	pandoraTrackToken = Column('pandora_track_token', String(120), nullable=False)
	liked = Column('liked', Boolean)
	
	pandoraUser = relationship("PandoraUser", backref=backref('pandora_listened_songs', order_by=id))

	def __init__(self, title, artist, album, pandoraTrackToken, liked=None):
		self.title = title
		self.artist = artist
		self.album = album
		self.pandora_track_token = pandoraTrackToken
		self.liked = liked

