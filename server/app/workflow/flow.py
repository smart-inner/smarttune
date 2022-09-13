from prefect import flow
from app.analysis import *
from .preprocessing import *

@flow
def api_flow(url):
    fact_json = call_api(url)
    fact_text = parse_fact(fact_json)
    return fact_text