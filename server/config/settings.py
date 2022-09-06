class BaseConfig(object):
    SQLALCHEMY_DATABASE_URI = "mysql://<username>:<password>@<server>/<database>"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(BaseConfig):
    pass

class TestingConfig(BaseConfig):
    SQLALCHEMY_ECHO = True


