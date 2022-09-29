from app.analysis import *
from app.models import *
from app.utils import *
from loguru import logger
import time

def aggregate_target_results(result_id, algorithm, preprocess_data):
    start_ts = time.time()
    newest_result = Result.query.filter(Result.id == result_id).first()
    session = Session.query.filter(Session.id == newest_result.session_id).first()
    task_name = TaskUtil.get_task_name(session, result_id)

    if 'config_recommend' in preprocess_data:
        assert 'newest_result_id' in preprocess_data and 'status' in preprocess_data
        logger.info('%s: Skipping aggregate_target_results (status=%s).' % (task_name,
                    preprocess_data.get('status', '')))
        return preprocess_data

    logger.info("%s: Aggregating target results..." % task_name)

    # Aggregate all knob config results tried by the target so far in this
    # tuning session and this tuning workload.
    filters = {
        Result.session_id == newest_result.session_id,
        Result.workload_id == newest_result.workload_id
    }
    target_results = Result.query.filter(*filters).all()
    if len(target_results) == 0:
        raise Exception('Cannot find any results for session_id={}, workload_id={}'
                        .format(newest_result.session_id, newest_result.workload_id))
    
    agg_data = DataProcess.aggregate_data(target_results)
    agg_data['newest_result_id'] = result_id
    agg_data['status'] = 'good'

    # Clean knob data
    cleaned_agg_data = DataProcess.clean_knob_data(agg_data['X_matrix'], agg_data['X_columnlabels'], [session.id])
    agg_data['X_matrix'] = np.array(cleaned_agg_data[0])
    agg_data['X_columnlabels'] = np.array(cleaned_agg_data[1])

    exec_time = TaskUtil.save_execution_time("async_task", start_ts, "aggregate_target_results", newest_result.id)
    logger.info('%s: Finished aggregating target results (%.1f seconds).', task_name, exec_time)
    return agg_data