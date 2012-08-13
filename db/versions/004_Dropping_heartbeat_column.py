from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
	meta.bind = migrate_engine
	pandora_users = Table('pandora_users', meta, autoload=True, autoload_with=migrate_engine)
	pandora_users.c.last_heartbeat.drop()

def downgrade(migrate_engine):
	meta.bind = migrate_engine
	pandora_users = Table('pandora_users', meta, autoload=True, autoload_with=migrate_engine)
	last_heartbeat = Column('last_heartbeat', DateTime)
	last_heartbeat.create(pandora_users)
