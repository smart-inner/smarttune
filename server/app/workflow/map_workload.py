from prefect import task
from app.analysis import *

@task
def map_workload(agg_data):
    return