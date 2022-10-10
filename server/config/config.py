import argparse, json
from .settings import *

def parse_args():
    parser = argparse.ArgumentParser(description='The configuration parameters for smarttune')
    parser.add_argument('--config', dest='config', type=str, help='The config file path')
    return parser.parse_args()

def parse_config(config_file):
    with open(config_file) as f:
        config = json.load(f)
    config_obj = None
    if config["testing"]:
        config_obj = TestingConfig()
    else:
        config_obj = ProductionConfig()
    config_obj.SQLALCHEMY_DATABASE_URI = config["db_url"]
    return config_obj
