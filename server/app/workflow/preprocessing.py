from app.analysis import *
from app.models import *
from app.utils import *
from loguru import logger
import time

NUM_LHS_SAMPLES = 10

def preprocessing(result_id, algorithm):
    start_ts = time.time()
    target_data = {}
    target_data['newest_result_id'] = result_id
    newest_result = Result.query.filter(Result.id == result_id).first()
    session = Session.query.filter(Session.id == newest_result.session_id).first()
    knobs = DataProcess.get_knobs_for_session(session.id)
    task_name = TaskUtil.get_task_name(session, result_id)

    has_pipeline_data = PipelineData.query.filter(PipelineData.workload_id == newest_result.workload_id).first()
    session_results = Result.query.filter(Result.session_id == session.id).all()
    results_cnt = len(session_results)

    if has_pipeline_data is None or results_cnt == 0:
        all_samples = DataProcess.gen_lhs_samples(knobs, NUM_LHS_SAMPLES)
        samples = all_samples.pop()
        target_data['status'] = 'lhs'
        target_data['config_recommend'] = samples

    exec_time = TaskUtil.save_execution_time("async_task", start_ts, "preprocessing", result_id)
    logger.info("%s: Done preprocessing data (%.1f seconds)." % (task_name, exec_time))

    return target_data
