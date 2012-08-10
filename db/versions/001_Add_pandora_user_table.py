from sqlalchemy import *
from migrate import *

meta = MetaData()

pandora_user = Table(
	'pandora_users', meta,
	Column('id', Integer, primary_key=True),
	Column('user_id', Integer, nullable=False),
	Column('user_auth_token', String(50)),
	Column('last_heartbeat', DateTime),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
	meta.bind = migrate_engine
	pandora_user.create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
	meta.bind = migrate_engine
	pandora_user.drop()
