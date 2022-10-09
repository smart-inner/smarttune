from app.analysis import *
from app.types import AlgorithmType
from .preprocessing import *
from .aggregate_target_results import *
from .map_workload import *
from .recommendation import *

def gaussian_process_bandits(result_id):
    preprocess_data = preprocessing(result_id, AlgorithmType.GPB)
    agg_data = aggregate_target_results(result_id, AlgorithmType.GPB, preprocess_data)
    map_data = map_workload(agg_data, AlgorithmType.GPB)
    recommendation = configuration_recommendation(map_data, AlgorithmType.GPB)
    return recommendation