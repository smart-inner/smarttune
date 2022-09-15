from prefect import task
from app.analysis import *

@task
def aggregate_target_results(target_data):
    return