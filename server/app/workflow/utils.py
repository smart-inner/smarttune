from app.models import *
from app.types import VarType
from app import db
from datetime import datetime
from pytz import timezone
from pyDOE import lhs
from scipy.stats import uniform
import numpy as np
from loguru import logger
import time, random, json

TIME_ZONE = 'Asia/Shanghai'

def get_knobs_for_session(session):
    session_knobs = SessionKnob.query.filter(SessionKnob.session_id == session.id)
    knob_ids = [s.knob_id for s in session_knobs]
    print(knob_ids)
    knobs = KnobCatalog.query.filter(KnobCatalog.id.in_(knob_ids)).all()
    knob_infos = []
    for knob in knobs:
        knob_info = {}
        knob_info['name'] = knob.name
        knob_info['var_type'] = knob.var_type
        knob_info['enum_vals'] = knob.enum_vals
        knob_info['tunable'] = knob.tunable
        knob_info['min_val'] = knob.min_val
        knob_info['max_val'] = knob.max_val
        if knob.var_type == VarType.ENUM.value:
            enum_vals = knob.enum_vals.split(',')
            knob_info['min_val'] = '0'
            knob_info['max_val'] = str(len(enum_vals) - 1)
        if knob.var_type == VarType.BOOL.value:
            knob_info['min_val'] = '0'
            knob_info['max_val'] = '1'
        knob_infos.append(knob_info)

    return knob_infos

def get_task_name(session, result_id):
    return '{}@{}#{}'.format(session.name, session.algorithm, result_id)

def save_execution_time(start_ts, fn, result_id):
    end_ts = time.time()
    exec_time = end_ts - start_ts
    start_time = datetime.fromtimestamp(int(start_ts), timezone(TIME_ZONE))
    db.session.add(ExecutionTime(module="async_tasks", function=fn, tag="",
                                 start_time=start_time, execution_time=exec_time, result_id=result_id))
    return exec_time

def gen_lhs_samples(knobs, nsamples):
    names = []
    maxvals = []
    minvals = []
    types = []

    for knob in knobs:
        names.append(knob['name'])
        if knob['var_type'] == VarType.ENUM.value:
            maxvals.append(float(knob['max_val']) + 0.5)
            minvals.append(float(knob['min_val']) - 0.5)
        else:
            maxvals.append(float(knob['max_val']))
            minvals.append(float(knob['min_val']))
        types.append(knob['var_type'])

    nfeats = len(knobs)
    samples = lhs(nfeats, samples=nsamples, criterion='maximin')
    maxvals = np.array(maxvals)
    minvals = np.array(minvals)
    scales = maxvals - minvals
    for fidx in range(nfeats):
        check_type = types[fidx] in (VarType.INTEGER, VarType.REAL)
        check_minval = minvals[fidx] > 0
        check_minval_zero = minvals[fidx] == 0
        check_quotient = (maxvals[fidx]/minvals[fidx] > 1000) if check_minval else (maxvals[fidx] > 1000)

        if check_type and (check_minval or check_minval_zero) and check_quotient:
            logmin = np.log2(minvals[fidx]) if check_minval else np.log2(minvals[fidx] + 1)
            logmax = np.log2(maxvals[fidx])
            samples[:, fidx] = np.exp2(uniform(loc=logmin, scale=logmax-logmin).ppf(samples[:, fidx]))
        else:
            samples[:, fidx] = uniform(loc=minvals[fidx], scale=scales[fidx]).ppf(samples[:, fidx])
    lhs_samples = []
    for sidx in range(nsamples):
        lhs_samples.append(dict())
        for fidx in range(nfeats):
            if types[fidx] == VarType.INTEGER:
                lhs_samples[-1][names[fidx]] = int(round(samples[sidx][fidx]))
            elif types[fidx] == VarType.BOOL:
                lhs_samples[-1][names[fidx]] = int(round(samples[sidx][fidx]))
            elif types[fidx] == VarType.ENUM:
                lhs_samples[-1][names[fidx]] = int(round(samples[sidx][fidx]))
            elif types[fidx] == VarType.REAL:
                lhs_samples[-1][names[fidx]] = float(samples[sidx][fidx])
            else:
                logger.warning("LHS: vartype not supported: %s (knob name: %s).",
                               VarType.name(types[fidx]), names[fidx])
    random.shuffle(lhs_samples)

    return lhs_samples


def aggregate_data(results):
    knob_labels = sorted(json.loads(results[0].knob_data).keys())
    metric_labels = sorted(json.loads(results[0].metric_data).keys())
    X_matrix = []
    y_matrix = []
    rowlabels = []

    for result in results:
        param_data = json.loads(result.knob_data)
        if len(param_data) != len(knob_labels):
            raise Exception("Incorrect number of knobs "
                            "(expected={}, actual={})".format(len(knob_labels),
                                                              len(param_data)))

        metric_data = json.loads(result.metric_data)
        if len(metric_data) != len(metric_labels):
            raise Exception("Incorrect number of metrics "
                            "(expected={}, actual={})".format(len(metric_labels),
                                                              len(metric_data)))

        X_matrix.append([param_data[l] for l in knob_labels])
        y_matrix.append([metric_data[l] for l in metric_labels])
        rowlabels.append(result.id)
    return {
        'X_matrix': np.array(X_matrix, dtype=np.float64),
        'y_matrix': np.array(y_matrix, dtype=np.float64),
        'rowlabels': rowlabels,
        'X_columnlabels': knob_labels,
        'y_columnlabels': metric_labels,
    }


def clean_knob_data(knob_matrix, knob_labels, sessions):
    # Filter and amend knob_matrix and knob_labels according to the tunable knobs in the session
    knob_matrix = np.array(knob_matrix)
    session_knobs = []
    knob_cat = []
    for session in sessions:
        knobs_for_this_session = get_knobs_for_session(session)
        for knob in knobs_for_this_session:
            if knob['name'] not in knob_cat:
                session_knobs.append(knob)
        knob_cat = [k['name'] for k in session_knobs]

    if len(knob_cat) == 0 or knob_cat == knob_labels:
        return knob_matrix, knob_labels

    logger.info("session_knobs: %s, knob_labels: %s, missing: %s, extra: %s" % (len(knob_cat),
                len(knob_labels), len(set(knob_cat) - set(knob_labels)),
                len(set(knob_labels) - set(knob_cat))))

    nrows = knob_matrix.shape[0]
    new_labels = []
    new_columns = []

    for knob in session_knobs:
        knob_name = knob['name']
        if knob_name not in knob_labels:
            # Add missing column initialized to knob's default value
            default_val = knob['default']
            try:
                if knob['vartype'] == VarType.ENUM:
                    default_val = knob['enumvals'].split(',').index(default_val)
                elif knob['vartype'] == VarType.BOOL:
                    default_val = str(default_val).lower() in ("on", "true", "yes", "0")
                else:
                    default_val = float(default_val)
            except ValueError:
                logger.warning("Error parsing knob '%s' default value: %s. Setting default to 0.",
                                knob_name, default_val, exc_info=True)
                default_val = 0
            new_col = np.ones((nrows, 1), dtype=float) * default_val
            new_lab = knob_name
        else:
            index = knob_labels.index(knob_name)
            new_col = knob_matrix[:, index].reshape(-1, 1)
            new_lab = knob_labels[index]

        new_labels.append(new_lab)
        new_columns.append(new_col)

    new_matrix = np.hstack(new_columns).reshape(nrows, -1)
    assert new_labels == knob_cat, "Expected knobs: {}\nActual knobs:  {}\n".format(
                knob_cat, new_labels)
    assert new_matrix.shape == (nrows, len(knob_cat)), "Expected shape: {}, Actual shape:  {}".format(
                (nrows, len(knob_cat)), new_matrix.shape)

    return new_matrix, new_labels