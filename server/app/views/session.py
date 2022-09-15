from flask import Blueprint
from app.workflow import flow
from app.models import *
from app import db

session = Blueprint('session', __name__)

@session.route('/', methods=['POST'])
def create_session():
   user_list = db.session.query(models.User).all()
   db.session.close()
   for item in user_list:
       print(item.username)
   return "success"

@session.route('/<session_name>', methods=['DELETE'])
def delete_session(session_name):
    return "success"

