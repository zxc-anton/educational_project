from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
import sqlalchemy as sa
from app import db
from app.models import User
from app.api.errors import error_responce


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

@basic_auth.verify_password
def verify_password(username, password):
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if user and user.check_password(password):
        return user
    
@token_auth.verify_token
def verify_token(token):
    return User.check_token(token) if token else None

@token_auth.error_handler
def token_auth_error(status):
    return error_responce(status)
    
@basic_auth.error_handler
def basic_auth_error(status):
    return error_responce(status)