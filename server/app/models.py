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
    conversion = db.Column(db.Text, default='''{
        "BYTES_SYSTEM": {
            "PB": "1024 ** 5",
            "TB": "1024 ** 4",
            "GB": "1024 ** 3",
            "MB": "1024 ** 2",
            "KB": "1024 ** 1"
        },
        "MIN_BYTES_UNIT": "KB",
        "TIME_SYSTEM": {
            "d": "1000 * 60 * 60 * 24",
            "h": "1000 * 60 * 60",
            "min": "1000 * 60",
            "s": "1000",
            "ms": "1"
        },
        "MIN_TIME_UNIT": "ms",
        "BOOLEAN_SYSTEM": {
            "true_value": "on",
            "false_value": "off"
        }
    }''')

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
    hyper_parameters = db.Column(db.Text, default='''{
        "DDPG_ACTOR_HIDDEN_SIZES": [128, 128, 64],
        "DDPG_ACTOR_LEARNING_RATE": 0.02,
        "DDPG_CRITIC_HIDDEN_SIZES": [64, 128, 64],
        "DDPG_CRITIC_LEARNING_RATE": 0.001,
        "DDPG_BATCH_SIZE": 32,
        "DDPG_GAMMA": 0.0,
        "DDPG_SIMPLE_REWARD": true,
        "DDPG_UPDATE_EPOCHS": 30,
        "DDPG_USE_DEFAULT": false,
        "DNN_DEBUG": true,
        "DNN_DEBUG_INTERVAL": 100,
        "DNN_EXPLORE": false,
        "DNN_EXPLORE_ITER": 500,
        "DNN_GD_ITER": 100,
        "DNN_NOISE_SCALE_BEGIN": 0.1,
        "DNN_NOISE_SCALE_END": 0.0,
        "DNN_TRAIN_ITER": 100,
        "FLIP_PROB_DECAY": 0.5,
        "GPR_BATCH_SIZE": 3000,
        "GPR_DEBUG": true,
        "GPR_EPS": 0.001,
        "GPR_EPSILON": 1e-06,
        "GPR_LEARNING_RATE": 0.01,
        "GPR_LENGTH_SCALE": 2.0,
        "GPR_MAGNITUDE": 1.0,
        "GPR_MAX_ITER": 500,
        "GPR_MAX_TRAIN_SIZE": 7000,
        "GPR_MU_MULTIPLIER": 1.0,
        "GPR_MODEL_NAME": "BasicGP",
        "GPR_HP_LEARNING_RATE": 0.001,
        "GPR_HP_MAX_ITER": 5000,
        "GPR_RIDGE": 1.0,
        "GPR_SIGMA_MULTIPLIER": 1.0,
        "GPR_UCB_SCALE": 0.2,
        "GPR_USE_GPFLOW": true,
        "GPR_UCB_BETA": "get_beta_td",
        "IMPORTANT_KNOB_NUMBER": 10000,
        "INIT_FLIP_PROB": 0.3,
        "NUM_SAMPLES": 30,
        "TF_NUM_THREADS": 4,
        "TOP_NUM_CONFIG": 10}''')
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
    workload_id = db.Column(db.Integer, db.ForeignKey("workload.id"))
    #workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"))

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
