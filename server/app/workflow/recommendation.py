from prefect import task
from app.analysis import *

@task
def recommendation(target_data):
    return