from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_executor import Executor

db = SQLAlchemy()
executor = Executor()

from .models import *
from .views import *

def create_app(config_obj):
    app = Flask(__name__)
    app.config.from_object(config_obj)
    db.init_app(app)
    executor.init_app(app)
    app.register_blueprint(account, url_prefix='/api/account')
    app.register_blueprint(session, url_prefix='/api/session')
    app.register_blueprint(result, url_prefix='/api/result')
    app.register_blueprint(system, url_prefix='/api/system')
    app.register_blueprint(knob, url_prefix='/api/knob')
    app.register_blueprint(metric, url_prefix='/api/metric')
    with app.app_context():
        db.create_all()
    return app
