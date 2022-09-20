from app.analysis import *
from app.types import AlgorithmType
from .preprocessing import *

def gaussian_process_bandits(result_id):
    preprocess_data = preprocessing(result_id, AlgorithmType.GPB)
    print('-----------------------')
    print(preprocess_data)
    return "hello world"