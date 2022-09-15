from pydoc import describe
from prefect import flow
from app.analysis import *
from app.types import AlgorithmType
from .preprocessing import *

@flow(name="GPB", description="Gaussian Process Bandits")
def gaussian_process_bandits(result_id):
    preprocess_data = preprocessing(result_id, AlgorithmType.GPB)
    return "hello world"