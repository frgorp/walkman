from sqlalchemy import *
from migrate import *

meta = MetaData()

def upgrade(migrate_engine):
	meta.bind = migrate_engine
	pandora_users = Table('pandora_users', meta, autoload=True, autoload_with=migrate_engine)
	keepalive = Column('keepalive', Boolean)
	keepalive.create(pandora_users)

def downgrade(migrate_engine):
	meta.bind = migrate_engine
	pandora_users = Table('pandora_users', meta, autoload=True, autoload_with=migrate_engine)
	pandora_users.c.keepalive.drop()
