from . import db
from app.types import AlgorithmType
from datetime import datetime


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)

class SystemCatalog(db.Model):
    __tablename__ = "system_catalog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(64), nullable=False)
    version = db.Column(db.String(64), nullable=False)

class KnobCatalog(db.Model):
    __tablename__ = "knob_catalog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    system_id = db.Column(db.Integer, db.ForeignKey("system_catalog.id"))
    var_type = db.Column(db.String(32), nullable=False)
    unit = db.Column(db.String(32), nullable=False)
    category = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=True)
    scope = db.Column(db.String(32))
    min_val = db.Column(db.String(32), nullable=True)
    max_val = db.Column(db.String(32), nullable=True)
    default = db.Column(db.String(32), nullable=False)
    enum_vals = db.Column(db.Text, nullable=True)
    tunable = db.Column(db.Boolean, default=True)
    resource = db.Column(db.String(32), nullable=False)

class MetricCatalog(db.Model):
    __tablename__ = "metric_catalog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    var_type = db.Column(db.String(32), nullable=False)
    unit = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scope = db.Column(db.String(32))
    metric_type = db.Column(db.String(32), nullable=False)
    system_id = db.Column(db.Integer, db.ForeignKey("system_catalog.id"))

class Session(db.Model):
    __tablename__ = "session"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(128), nullable=True)
    algorithm = db.Column(db.String(64), nullable=False, default=AlgorithmType.GPB.value)
    creation_time = db.Column(db.DateTime, default=datetime.now)
    target_objective = db.Column(db.String(64), nullable=False)
    hyper_parameters = db.Column(db.Text, nullable=True)
    system_id = db.Column(db.Integer, db.ForeignKey("system_catalog.id"))
    #user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class SessionKnob(db.Model):
    __tablename__ = "session_knob"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"))
    knob_id = db.Column(db.Integer, db.ForeignKey("knob_catalog.id"))
    
class Workflow(db.Model):
    __tablename__ = "workflow"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)


class Result(db.Model):
    __tablename__ = "result"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    creation_time = db.Column(db.DateTime, default=datetime.now)
    knob_data = db.Column(db.Text, nullable=True)
    metric_data = db.Column(db.Text, nullable=True)
    observation_start_time = db.Column(db.DateTime)
    observation_end_time = db.Column(db.DateTime)
    observation_time = db.Column(db.Float)
    next_configuration = db.Column(db.Text, nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"))
    #workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"))
