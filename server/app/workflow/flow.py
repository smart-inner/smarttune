from pydoc import describe
from prefect import flow
from app.analysis import *
from .preprocessing import *
from .algo_type import AlgorithmType

@flow(name="GPB", description="Gaussian Process Bandits")
def gaussian_process_bandits(result_id):
    preprocess_data = preprocessing(result_id, AlgorithmType.GPB)
    return "hello world"