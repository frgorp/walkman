from sqlalchemy import *
from migrate import *

meta = MetaData()


pandora_listened_song = Table(
	'pandora_listened_songs', meta,
	Column('id', Integer, primary_key=True),
	Column('title', String(32), nullable=False),
	Column('artist', String(32), nullable=False),
	Column('album', String(32), nullable=False),
	Column('pandora_track_token', String(120), nullable=False),
	Column('liked', Boolean),
#	Column('pandora_user_id', Integer, ForeignKey('pandora_user.id')),
)

def upgrade(migrate_engine):
	meta.bind = migrate_engine
	pandora_users = Table('pandora_users', meta, autoload=True, autoload_with=migrate_engine)
	pandora_listened_song.append_column(Column('pandora_user_id', Integer, ForeignKey('pandora_users.id')))
	pandora_listened_song.create()

def downgrade(migrate_engine):
	meta.bind = migrate_engine
	pandora_listened_song.drop()
