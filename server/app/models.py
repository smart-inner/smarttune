from . import db
from app.types import AlgorithmType
from datetime import datetime
from .commons import *

class SystemCatalog(db.Model):
    __tablename__ = "system_catalog"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(64), nullable=False)
    version = db.Column(db.String(64), nullable=False)
    conversion = db.Column(db.Text, default=DEFAULT_CONVERSION)

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
    more_is_better = db.Column(db.Boolean, default=True)
    hyper_parameters = db.Column(db.Text, default=DEFAULT_HYPER_PARAMETERS)
    system_id = db.Column(db.Integer, db.ForeignKey("system_catalog.id"))

class SessionKnob(db.Model):
    __tablename__ = "session_knob"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"))
    knob_id = db.Column(db.Integer, db.ForeignKey("knob_catalog.id"))

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
    workload_id = db.Column(db.Integer, db.ForeignKey("workload.id"))

class Workload(db.Model):
    __tablename__ = "workload"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    system_id = db.Column(db.Integer, db.ForeignKey("system_catalog.id"))

class PipelineRun(db.Model):
    __tablename__ = "pipeline_run"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

class PipelineData(db.Model):
    __tablename__ = "pipeline_data"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_type = db.Column(db.String(32), nullable=False)
    data = db.Column(db.Text, nullable=True)
    creation_time = db.Column(db.DateTime, default=datetime.now)
    workload_id = db.Column(db.Integer, db.ForeignKey("workload.id"))
    pipeline_run_id = db.Column(db.Integer, db.ForeignKey("pipeline_run.id"))

class ExecutionTime(db.Model):
    __tablename__ = "execution_time"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    module = db.Column(db.String(32))
    function = db.Column(db.String(64))
    tag = db.Column(db.String(64), default='')
    start_time = db.Column(db.DateTime)
    execution_time = db.Column(db.Float)
    result_id = db.Column(db.Integer, db.ForeignKey("result.id"))
