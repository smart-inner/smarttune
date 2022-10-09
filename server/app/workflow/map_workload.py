from app.models import *
from app.utils import *
from app.types import *
from app.analysis.preprocessing import Bin
from app.analysis.gpr import gpr_models
from app.analysis.gpr.predict import gpflow_predict
from app.analysis.gp import GPRNP
from sklearn.preprocessing import StandardScaler
from loguru import logger
import numpy as np
import tensorflow as tf
import time, json, gpflow

def map_workload(data, algorithm):
    start_ts = time.time()
    newest_result = Result.query.filter(Result.id == data['newest_result_id']).first()
    session = Session.query.filter(Session.id == newest_result.session_id).first()
    task_name = TaskUtil.get_task_name(session, data['newest_result_id'])
    target_workload = Workload.query.filter(Workload.id == newest_result.workload_id).first()

    if data['status'] != 'good':
        logger.info("%s: Skipping workload mapping (status: %s)." % (task_name, data['status']))
        return data

    logger.info("%s: Mapping the workload..." % task_name)

    params = json.loads(session.hyper_parameters)
    y_columnlabels = np.array(data['y_columnlabels'])

    # Find all pipeline data belonging to the latest version with the same
    # system as the target
    pipeline_data = PipelineData.query.filter(PipelineData.workload_id == newest_result.workload_id).all()
    pipeline_run_ids = [data.pipeline_run_id for data in pipeline_data]
    filters = {
        PipelineRun.end_time != None,
        PipelineRun.id.in_(pipeline_run_ids)
    }
    latest_pipeline_run = PipelineRun.query.filter(*filters).order_by(PipelineRun.id.desc()).first()
    assert latest_pipeline_run is not None
    data['pipeline_run'] = latest_pipeline_run.id

    pipeline_data = PipelineData.query.filter(PipelineData.pipeline_run_id == latest_pipeline_run.id).all()

    # pruned metrics but we just use those from the first workload for now
    initialized = False
    global_pruned_metrics = None
    pruned_metric_idxs = None
    
    unique_workloads = list(set([data.workload_id for data in pipeline_data]))
    workload_data = {}
    # Compute workload mapping data for each unique workload
    for unique_workload in unique_workloads:
        # do not include the workload of the current session
        if newest_result.workload_id == unique_workload:
            continue
        workload_obj = Workload.query.filter(Workload.id == unique_workload).first()
        if workload_obj.system_id != target_workload.system_id:
            continue
        wkld_results = Result.query.filter(Result.workload_id == unique_workload).all()
        if len(wkld_results) == 0:
            db.session.delete(workload_obj)
            db.session.commit()
            continue

        # Load knob & metric data for this workload
        knob_data = DataProcess.load_pipeline_data(unique_workload, latest_pipeline_run.id, 
                                                   PipelineTaskType.KNOB_DATA.value)
        knob_data["data"], knob_data["columnlabels"] = \
            DataProcess.clean_knob_data(knob_data["data"], knob_data["columnlabels"],
                                        [session.id])

        metric_data = DataProcess.load_pipeline_data(unique_workload, latest_pipeline_run.id, 
                                                     PipelineTaskType.METRIC_DATA.value)
        X_matrix = np.array(knob_data["data"])
        y_matrix = np.array(metric_data["data"])
        rowlabels = np.array(knob_data["rowlabels"])
        assert np.array_equal(rowlabels, metric_data["rowlabels"])

        if not initialized:
            # For now set pruned metrics to be those computed for the first workload
            global_pruned_metrics = DataProcess.load_pipeline_data(unique_workload, latest_pipeline_run.id,
                                                                   PipelineTaskType.PRUNED_METRICS.value)
            pruned_metric_idxs = [i for i in range(y_matrix.shape[1]) if y_columnlabels[
                i] in global_pruned_metrics]

            # Filter y columnlabels by pruned_metrics
            y_columnlabels = y_columnlabels[pruned_metric_idxs]
            initialized = True

        # Filter y matrices by pruned_metrics
        y_matrix = y_matrix[:, pruned_metric_idxs]

        # Combine duplicate rows (rows with same knob settings)
        X_matrix, y_matrix, rowlabels = DataProcess.combine_duplicate_rows(
            X_matrix, y_matrix, rowlabels)

        workload_data[unique_workload] = {
            'X_matrix': X_matrix,
            'y_matrix': y_matrix,
            'rowlabels': rowlabels,
        }

    if len(workload_data) == 0:
        # The background task that aggregates the data has not finished running yet
        data.update(mapped_workload=None, scores=None)
        logger.info('%s: Skipping workload mapping because no different workload is available.' % task_name)
        return data

    # Stack all X & y matrices for preprocessing
    Xs = np.vstack([entry['X_matrix'] for entry in list(workload_data.values())])
    ys = np.vstack([entry['y_matrix'] for entry in list(workload_data.values())])

    # Scale the X & y values, then compute the deciles for each column in y
    X_scaler = StandardScaler(copy=False)
    X_scaler.fit(Xs)
    y_scaler = StandardScaler(copy=False)
    y_scaler.fit_transform(ys)
    y_binner = Bin(bin_start=1, axis=0)
    y_binner.fit(ys)
    del Xs
    del ys

    X_target = data['X_matrix']
    # Filter the target's y data by the pruned metrics.
    y_target = data['y_matrix'][:, pruned_metric_idxs]

    # Now standardize the target's data and bin it by the deciles we just
    # calculated
    X_target = X_scaler.transform(X_target)
    y_target = y_scaler.transform(y_target)
    y_target = y_binner.transform(y_target)

    scores = {}
    for workload_id, workload_entry in list(workload_data.items()):
        predictions = np.empty_like(y_target)
        X_workload = workload_entry['X_matrix']
        X_scaled = X_scaler.transform(X_workload)
        y_workload = workload_entry['y_matrix']
        y_scaled = y_scaler.transform(y_workload)
        for j, y_col in enumerate(y_scaled.T):
            # Using this workload's data, train a Gaussian process model
            # and then predict the performance of each metric for each of
            # the knob configurations attempted so far by the target.
            y_col = y_col.reshape(-1, 1)
            if params['GPR_USE_GPFLOW']:
                model_kwargs = {'lengthscales': params['GPR_LENGTH_SCALE'],
                                'variance': params['GPR_MAGNITUDE'],
                                'noise_variance': params['GPR_RIDGE']}
                tf.reset_default_graph()
                graph = tf.get_default_graph()
                gpflow.reset_default_session(graph=graph)
                m = gpr_models.create_model(params['GPR_MODEL_NAME'], X=X_scaled, y=y_col,
                                            **model_kwargs)
                gpr_result = gpflow_predict(m.model, X_target)
            else:
                model = GPRNP(length_scale=params['GPR_LENGTH_SCALE'],
                              magnitude=params['GPR_MAGNITUDE'],
                              max_train_size=params['GPR_MAX_TRAIN_SIZE'],
                              batch_size=params['GPR_BATCH_SIZE'])
                model.fit(X_scaled, y_col, ridge=params['GPR_RIDGE'])
                gpr_result = model.predict(X_target)
            predictions[:, j] = gpr_result.ypreds.ravel()
        # Bin each of the predicted metric columns by deciles and then
        # compute the score (i.e., distance) between the target workload
        # and each of the known workloads
        predictions = y_binner.transform(predictions)
        dists = np.sqrt(np.sum(np.square(
            np.subtract(predictions, y_target)), axis=1))
        scores[workload_id] = np.mean(dists)

    # Find the best (minimum) score
    best_score = np.inf
    best_workload_id = None
    best_workload_name = None
    scores_info = {}
    for workload_id, similarity_score in list(scores.items()):
        workload_name = Workload.objects.get(pk=workload_id).name
        if similarity_score < best_score:
            best_score = similarity_score
            best_workload_id = workload_id
            best_workload_name = workload_name
        scores_info[workload_id] = (workload_name, similarity_score)
    data.update(mapped_workload=(best_workload_id, best_workload_name, best_score),
                scores=scores_info)
    exec_time = TaskUtil.save_execution_time("async_task", start_ts, "map_workload", newest_result.id)
    logger.info('%s: Done mapping the workload (%.1f seconds).' % (task_name, exec_time))

    return data