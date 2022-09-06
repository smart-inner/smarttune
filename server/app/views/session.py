from flask import Blueprint

from .. import db
from .. import models

session = Blueprint('session', __name__)

@session.route('/create_session')
def create_session():
   user_list = db.session.query(models.User).all()
   db.session.close()
   for item in user_list:
       print(item.username)
   return "success"
