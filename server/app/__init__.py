from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_executor import Executor
from flask_apscheduler import APScheduler

db = SQLAlchemy()
executor = Executor()
scheduler = APScheduler()

from .views import *

def create_app(config_obj):
    app = Flask(__name__)
    app.config.from_object(config_obj)
    db.init_app(app)
    db.app = app
    executor.init_app(app)
    scheduler.init_app(app)
    scheduler.start()
    app.register_blueprint(account, url_prefix='/api/account')
    app.register_blueprint(session, url_prefix='/api/session')
    app.register_blueprint(result, url_prefix='/api/result')
    app.register_blueprint(system, url_prefix='/api/system')
    app.register_blueprint(knob, url_prefix='/api/knob')
    app.register_blueprint(metric, url_prefix='/api/metric')
    with app.app_context():
        db.create_all()
    return app
