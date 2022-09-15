from prefect import task, get_run_logger
from app.analysis import *

@task(name="preprocessing")
def preprocessing(result_id, algorithm):
    logger = get_run_logger()
    logger.error("hello world")
    return algorithm
