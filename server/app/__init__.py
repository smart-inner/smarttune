from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .models import *
from .views import session, account, result

def create_app(config_obj):
    app = Flask(__name__)
    app.config.from_object(config_obj)
    db.init_app(app)
    app.register_blueprint(account.account, url_prefix='/account')
    app.register_blueprint(session.session, url_prefix='/session')
    app.register_blueprint(result.result, url_prefix='/result')
    with app.app_context():
        db.create_all()
    return app
