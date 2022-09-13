from . import db
from datetime import datetime


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)

class TargetSystemCatalog(db.Model):
    __tablename__ = "target_system_catalog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(64), nullable=False)
    version = db.Column(db.String(64), nullable=False)

class KnobCatalog(db.Model):
    __tablename__ = "knob_catalog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    target_system_id = db.Column(db.Integer, db.ForeignKey("target_system_catalog.id"))

class MetricCatalog(db.Model):
    __tablename__ = "metric_catalog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    target_system_id = db.Column(db.Integer, db.ForeignKey("target_system_catalog.id"))

class Session(db.Model):
    __tablename__ = "session"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    target_system_id = db.Column(db.Integer, db.ForeignKey("target_system_catalog.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class Workflow(db.Model):
    __tablename__ = "workflow"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)


class Result(db.Model):
    __tablename__ = "result"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creation_time = db.Column(db.DateTime, default=datetime.now)
    result = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"))
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"))
