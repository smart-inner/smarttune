import requests
from prefect import task
from app.analysis import *

@task
def call_api(url):
    response = requests.get(url)
    print(response.status_code)
    return response.json()

@task
def parse_fact(response):
   fact = response["fact"]
   print(fact)
   return fact