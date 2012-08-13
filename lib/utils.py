from models.pandora import *

def retrieve_user_info(session, Connector):
	user = session.get('user')
	walkmanId = session.get('walkmanId')
	connector = Connector()
	return user, connector.query(PandoraUser).filter_by(id=walkmanId).one(), connector

def transform_walkman_to_user(walkman_user):
	return {'userId': str(walkman_user.user_id), 'userAuthToken': walkman_user.user_auth_token}
