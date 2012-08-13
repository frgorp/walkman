from sqlalchemy import *
from migrate import *

meta = MetaData()

pandora_keepalive = Table(
	'pandora_keepalive', meta,
	Column('id', Integer, primary_key=True),
	Column('last_heartbeat', DateTime),
	Column('alive', Boolean, nullable=False),
	Column('beats', SmallInteger, nullable=False),
)

def upgrade(migrate_engine):
	meta.bind = migrate_engine
	pandora_users = Table('pandora_users', meta, autoload=True, autoload_with=migrate_engine)
	pandora_keepalive.append_column(Column('user_id', Integer, ForeignKey('pandora_users.id'), nullable=False))
	pandora_keepalive.create()

def downgrade(migrate_engine):
	meta.bind = migrate_engine
	pandora_keepalive.drop()
