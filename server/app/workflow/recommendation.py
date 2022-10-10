from app.models import *
from app.utils import *
from app.types import *
from app.analysis.nn_tf import NeuralNet
from app.analysis.gpr import gpr_models
from app.analysis.gpr.optimize import tf_optimize
from app.analysis.gp_tf import GPRGD
from app.analysis.gpr import ucb
from app.analysis.preprocessing import DummyEncoder
from app.analysis.constraints import ParamConstraintHelper
from sklearn.preprocessing import StandardScaler
from loguru import logger
import numpy as np
import tensorflow as tf
import time, json, queue, gpflow

def process_training_data(data):
    newest_result = Result.query.filter(Result.id == data['newest_result_id']).first()
    latest_pipeline_run = PipelineRun.query.filter(PipelineRun.id == data['pipeline_run']).first()
    session = Session.query.filter(Session.id == newest_result.session_id).first()
    params = json.loads(session.hyper_parameters)
    pipeline_data_knob = None
    pipeline_data_metric = None

    # Load mapped workload data
    if data['mapped_workload'] is not None:
        mapped_workload_id = data['mapped_workload'][0]
        mapped_workload = Workload.query.filter(Workload.id == mapped_workload_id).first()
        workload_knob_data = DataProcess.load_pipeline_data(mapped_workload_id, 
            latest_pipeline_run.id, PipelineTaskType.KNOB_DATA.value)
        
        workload_metric_data = DataProcess.load_pipeline_data(mapped_workload_id, 
            latest_pipeline_run.id, PipelineTaskType.METRIC_DATA.value)
        
        cleaned_workload_knob_data = DataProcess.clean_knob_data(workload_knob_data["data"], 
            workload_knob_data["columnlabels"], [session.id])
        X_workload = np.array(cleaned_workload_knob_data[0])
        X_columnlabels = np.array(cleaned_workload_knob_data[1])
        y_workload = np.array(workload_metric_data['data'])
        y_columnlabels = np.array(workload_metric_data['columnlabels'])
        rowlabels_workload = np.array(workload_metric_data['rowlabels'])
    else:
        # combine the target_data with itself is actually adding nothing to the target_data
        X_workload = np.array(data['X_matrix'])
        X_columnlabels = np.array(data['X_columnlabels'])
        y_workload = np.array(data['y_matrix'])
        y_columnlabels = np.array(data['y_columnlabels'])
        rowlabels_workload = np.array(data['rowlabels'])

    # Target workload data
    X_target = data['X_matrix']
    y_target = data['y_matrix']
    rowlabels_target = np.array(data['rowlabels'])

    if not np.array_equal(X_columnlabels, data['X_columnlabels']):
        raise Exception(('The workload and target data should have '
                         'identical X columnlabels (sorted knob names)'),
                        X_columnlabels, data['X_columnlabels'])
    if not np.array_equal(y_columnlabels, data['y_columnlabels']):
        raise Exception(('The workload and target data should have '
                         'identical y columnlabels (sorted metric names)'),
                        y_columnlabels, data['y_columnlabels'])

    # Filter ys by current target objective metric
    target_objective = session.target_objective
    target_obj_idx = [i for i, cl in enumerate(y_columnlabels) if cl == target_objective]
    if len(target_obj_idx) == 0:
        raise Exception(('Could not find target objective in metrics '
                         '(target_obj={})').format(target_objective))
    elif len(target_obj_idx) > 1:
        raise Exception(('Found {} instances of target objective in '
                         'metrics (target_obj={})').format(len(target_obj_idx),
                                                           target_objective))

    y_workload = y_workload[:, target_obj_idx]
    y_target = y_target[:, target_obj_idx]
    y_columnlabels = y_columnlabels[target_obj_idx]

    # Combine duplicate rows in the target/workload data (separately)
    X_workload, y_workload, rowlabels_workload = DataProcess.combine_duplicate_rows(
        X_workload, y_workload, rowlabels_workload)
    X_target, y_target, rowlabels_target = DataProcess.combine_duplicate_rows(
        X_target, y_target, rowlabels_target)

    # Delete any rows that appear in both the workload data and the target
    # data from the workload data
    dups_filter = np.ones(X_workload.shape[0], dtype=bool)
    target_row_tups = [tuple(row) for row in X_target]
    for i, row in enumerate(X_workload):
        if tuple(row) in target_row_tups:
            dups_filter[i] = False
    X_workload = X_workload[dups_filter, :]
    y_workload = y_workload[dups_filter, :]
    rowlabels_workload = rowlabels_workload[dups_filter]

    # Combine target & workload Xs for preprocessing
    X_matrix = np.vstack([X_target, X_workload])

    # Dummy encode categorial variables
    if ENABLE_DUMMY_ENCODER:
        categorical_info = DataProcess.dummy_encoder_helper(X_columnlabels, newest_result.dbms)
        dummy_encoder = DummyEncoder(categorical_info['n_values'],
                                     categorical_info['categorical_features'],
                                     categorical_info['cat_columnlabels'],
                                     categorical_info['noncat_columnlabels'])
        X_matrix = dummy_encoder.fit_transform(X_matrix)
        binary_encoder = categorical_info['binary_vars']
        # below two variables are needed for correctly determing max/min on dummies
        binary_index_set = set(categorical_info['binary_vars'])
        total_dummies = dummy_encoder.total_dummies()
    else:
        dummy_encoder = None
        binary_encoder = None
        binary_index_set = []
        total_dummies = 0

    # Scale to N(0, 1)
    X_scaler = StandardScaler()
    X_scaled = X_scaler.fit_transform(X_matrix)
    if y_target.shape[0] < 5:  # FIXME
        # FIXME (dva): if there are fewer than 5 target results so far
        # then scale the y values (metrics) using the workload's
        # y_scaler. I'm not sure if 5 is the right cutoff.
        y_target_scaler = None
        y_workload_scaler = StandardScaler()
        y_matrix = np.vstack([y_target, y_workload])
        y_scaled = y_workload_scaler.fit_transform(y_matrix)
    else:
        # FIXME (dva): otherwise try to compute a separate y_scaler for
        # the target and scale them separately.
        try:
            y_target_scaler = StandardScaler()
            y_workload_scaler = StandardScaler()
            y_target_scaled = y_target_scaler.fit_transform(y_target)
            y_workload_scaled = y_workload_scaler.fit_transform(y_workload)
            y_scaled = np.vstack([y_target_scaled, y_workload_scaled])
        except ValueError:
            y_target_scaler = None
            y_workload_scaler = StandardScaler()
            y_scaled = y_workload_scaler.fit_transform(y_target)
    # Maximize the throughput, moreisbetter
    # Use gradient descent to minimize -throughput
    if session.more_is_better:
        y_scaled = -y_scaled

    # Set up constraint helper
    constraint_helper = ParamConstraintHelper(scaler=X_scaler,
                                              encoder=dummy_encoder,
                                              binary_vars=binary_encoder,
                                              init_flip_prob=params['INIT_FLIP_PROB'],
                                              flip_prob_decay=params['FLIP_PROB_DECAY'])

    # FIXME (dva): check if these are good values for the ridge
    # ridge = np.empty(X_scaled.shape[0])
    # ridge[:X_target.shape[0]] = 0.01
    # ridge[X_target.shape[0]:] = 0.1

    X_min = np.empty(X_scaled.shape[1])
    X_max = np.empty(X_scaled.shape[1])
    X_scaler_matrix = np.zeros([1, X_scaled.shape[1]])

    session_knobs = DataProcess.get_knobs_for_session(session.id)

    # Set min/max for knob values
    for i in range(X_scaled.shape[1]):
        if i < total_dummies or i in binary_index_set:
            col_min = 0
            col_max = 1
        else:
            col_min = X_scaled[:, i].min()
            col_max = X_scaled[:, i].max()
            for knob in session_knobs:
                if X_columnlabels[i] == knob["name"]:
                    X_scaler_matrix[0][i] = knob["min_val"]
                    col_min = X_scaler.transform(X_scaler_matrix)[0][i]
                    X_scaler_matrix[0][i] = knob["max_val"]
                    col_max = X_scaler.transform(X_scaler_matrix)[0][i]
        X_min[i] = col_min
        X_max[i] = col_max

    return X_columnlabels, X_scaler, X_scaled, y_scaled, X_max, X_min,\
        dummy_encoder, constraint_helper, pipeline_data_knob, pipeline_data_metric

def configuration_recommendation(data, algorithm):
    start_ts = time.time()
    newest_result = Result.query.filter(Result.id == data['newest_result_id']).first()
    session = Session.query.filter(Session.id == newest_result.session_id).first()
    task_name = TaskUtil.get_task_name(session, data['newest_result_id'])

    early_return, target_data_res = TaskUtil.check_early_return(data)
    if early_return:
        logger.info("%s: Returning early from config recommendation." % task_name)
        return target_data_res

    logger.info("%s: Recommending the next configuration..." % task_name)
    params = json.loads(session.hyper_parameters)

    X_columnlabels, X_scaler, X_scaled, y_scaled, X_max, X_min,\
        dummy_encoder, constraint_helper, pipeline_knobs,\
        pipeline_metrics = process_training_data(data)

    # FIXME: we should generate more samples and use a smarter sampling technique
    num_samples = params['NUM_SAMPLES']
    X_samples = np.empty((num_samples, X_scaled.shape[1]))
    for i in range(X_scaled.shape[1]):
        X_samples[:, i] = np.random.rand(num_samples) * (X_max[i] - X_min[i]) + X_min[i]

    q = queue.PriorityQueue()
    for x in range(0, y_scaled.shape[0]):
        q.put((y_scaled[x][0], x))

    i = 0
    while i < params['TOP_NUM_CONFIG']:
        try:
            item = q.get_nowait()
            # Tensorflow get broken if we use the training data points as
            # starting points for GPRGD. We add a small bias for the
            # starting points. GPR_EPS default value is 0.001
            # if the starting point is X_max, we minus a small bias to
            # make sure it is within the range.
            dist = sum(np.square(X_max - X_scaled[item[1]]))
            if dist < 0.001:
                X_samples = np.vstack((X_samples, X_scaled[item[1]] - abs(params['GPR_EPS'])))
            else:
                X_samples = np.vstack((X_samples, X_scaled[item[1]] + abs(params['GPR_EPS'])))
            i = i + 1
        except queue.Empty:
            break

    res = None
    info_msg = 'INFO: training data size is {}. '.format(X_scaled.shape[0])
    if algorithm == AlgorithmType.DNN:
        info_msg += 'Recommended by DNN.'
        # neural network model
        model_nn = NeuralNet(n_input=X_samples.shape[1],
                             batch_size=X_samples.shape[0],
                             explore_iters=params['DNN_EXPLORE_ITER'],
                             noise_scale_begin=params['DNN_NOISE_SCALE_BEGIN'],
                             noise_scale_end=params['DNN_NOISE_SCALE_END'],
                             debug=params['DNN_DEBUG'],
                             debug_interval=params['DNN_DEBUG_INTERVAL'])
        if session.dnn_model is not None:
            model_nn.set_weights_bin(session.dnn_model)
        model_nn.fit(X_scaled, y_scaled, fit_epochs=params['DNN_TRAIN_ITER'])
        res = model_nn.recommend(X_samples, X_min, X_max,
                                 explore=params['DNN_EXPLORE'],
                                 recommend_epochs=params['DNN_GD_ITER'])
        session.dnn_model = model_nn.get_weights_bin()
        session.save()

    elif algorithm == AlgorithmType.GPR:
        info_msg += 'Recommended by GPR.'
        # default gpr model
        if params['GPR_USE_GPFLOW']:
            model_kwargs = {}
            model_kwargs['model_learning_rate'] = params['GPR_HP_LEARNING_RATE']
            model_kwargs['model_maxiter'] = params['GPR_HP_MAX_ITER']
            opt_kwargs = {}
            opt_kwargs['learning_rate'] = params['GPR_LEARNING_RATE']
            opt_kwargs['maxiter'] = params['GPR_MAX_ITER']
            opt_kwargs['bounds'] = [X_min, X_max]
            opt_kwargs['debug'] = params['GPR_DEBUG']
            opt_kwargs['ucb_beta'] = ucb.get_ucb_beta(params['GPR_UCB_BETA'],
                                                      scale=params['GPR_UCB_SCALE'],
                                                      t=i + 1., ndim=X_scaled.shape[1])
            tf.reset_default_graph()
            graph = tf.get_default_graph()
            gpflow.reset_default_session(graph=graph)
            m = gpr_models.create_model(params['GPR_MODEL_NAME'], X=X_scaled, y=y_scaled,
                                        **model_kwargs)
            res = tf_optimize(m.model, X_samples, **opt_kwargs)
        else:
            model = GPRGD(length_scale=params['GPR_LENGTH_SCALE'],
                          magnitude=params['GPR_MAGNITUDE'],
                          max_train_size=params['GPR_MAX_TRAIN_SIZE'],
                          batch_size=params['GPR_BATCH_SIZE'],
                          num_threads=params['TF_NUM_THREADS'],
                          learning_rate=params['GPR_LEARNING_RATE'],
                          epsilon=params['GPR_EPSILON'],
                          max_iter=params['GPR_MAX_ITER'],
                          sigma_multiplier=params['GPR_SIGMA_MULTIPLIER'],
                          mu_multiplier=params['GPR_MU_MULTIPLIER'],
                          ridge=params['GPR_RIDGE'])
            model.fit(X_scaled, y_scaled, X_min, X_max)
            res = model.predict(X_samples, constraint_helper=constraint_helper)

    best_config_idx = np.argmin(res.minl.ravel())
    best_config = res.minl_conf[best_config_idx, :]
    best_config = X_scaler.inverse_transform(best_config)

    if ENABLE_DUMMY_ENCODER:
        # Decode one-hot encoding into categorical knobs
        best_config = dummy_encoder.inverse_transform(best_config)

    # Although we have max/min limits in the GPRGD training session, it may
    # lose some precisions. e.g. 0.99..99 >= 1.0 may be True on the scaled data,
    # when we inversely transform the scaled data, the different becomes much larger
    # and cannot be ignored. Here we check the range on the original data
    # directly, and make sure the recommended config lies within the range
    X_min_inv = X_scaler.inverse_transform(X_min)
    X_max_inv = X_scaler.inverse_transform(X_max)
    best_config = np.minimum(best_config, X_max_inv)
    best_config = np.maximum(best_config, X_min_inv)

    conf_map = {k: best_config[i] for i, k in enumerate(X_columnlabels)}
    newest_result.pipeline_knobs = pipeline_knobs
    newest_result.pipeline_metrics = pipeline_metrics

    conf_map_res = TaskUtil.create_and_save_recommendation(
        recommended_knobs=conf_map, result=newest_result,
        status='good', info=info_msg, pipeline_run=data['pipeline_run'])

    exec_time = TaskUtil.save_execution_time("async_task", start_ts, "configuration_recommendation", newest_result.id)
    logger.info("%s: Done recommending the next configuration (%.1f seconds)." % (task_name, exec_time))
    return conf_map_res
