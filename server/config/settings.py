class BaseConfig(object):
    SQLALCHEMY_DATABASE_URI = "mysql://<username>:<password>@<server>/<database>"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
    JOBS = [
        {
            'id': 'periodic_task',
            'func': 'app.periodic.tasks:run_background_tasks',
            'args': (),
            'trigger': 'interval',
            'seconds': 300
        }
    ]

class ProductionConfig(BaseConfig):
    pass

class TestingConfig(BaseConfig):
    SQLALCHEMY_ECHO = True


