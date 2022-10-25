from app.models import *
from app.types import VarType
from pyDOE import lhs
from scipy.stats import uniform
import numpy as np
from loguru import logger
import random, json

class DataProcess(object):

    @staticmethod
    def get_knobs_for_session(session_id):
        session_knobs = SessionKnob.query.filter(SessionKnob.session_id == session_id)
        knob_ids = [s.knob_id for s in session_knobs]
        knobs = KnobCatalog.query.filter(KnobCatalog.id.in_(knob_ids)).all()
        knob_infos = []
        for knob in knobs:
            knob_info = {}
            knob_info['id'] = knob.id
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
            knob_infos.append(knob_info)

        return knob_infos

    @staticmethod
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
                if types[fidx] == VarType.INTEGER.value:
                    lhs_samples[-1][names[fidx]] = int(round(samples[sidx][fidx]))
                elif types[fidx] == VarType.ENUM.value:
                    lhs_samples[-1][names[fidx]] = int(round(samples[sidx][fidx]))
                elif types[fidx] == VarType.REAL.value:
                    lhs_samples[-1][names[fidx]] = float(samples[sidx][fidx])
                else:
                    logger.warning("LHS: vartype not supported: %s (knob name: %s).",
                                   VarType.name(types[fidx]), names[fidx])
        random.shuffle(lhs_samples)

        return lhs_samples

    @staticmethod
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
    
    @staticmethod
    def clean_knob_data(knob_matrix, knob_labels, session_ids):
        # Filter and amend knob_matrix and knob_labels according to the tunable knobs in the session
        knob_matrix = np.array(knob_matrix)
        session_knobs = []
        knob_cat = []
        for session_id in session_ids:
            knobs_for_this_session = DataProcess.get_knobs_for_session(session_id)
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
                    if knob['var_type'] == VarType.ENUM.value:
                        default_val = knob['enum_vals'].split(',').index(default_val)
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

    @staticmethod
    def dummy_encoder_helper(featured_knobs, system_id):
        n_values = []
        cat_knob_indices = []
        cat_knob_names = []
        noncat_knob_names = []
        binary_knob_indices = []
        system = SystemCatalog.query.filter(SystemCatalog.id == system_id).first()

        if system is None:
            raise Exception("SystemCatalog cannot find system_id: {}".format(system_id))

        for i, knob_name in enumerate(featured_knobs):
            # knob can be uniquely identified by (system, knob_name)
            filters = {
                KnobCatalog.name == knob_name,
                KnobCatalog.system_id == system_id
            }
            knobs = KnobCatalog.query.filter(*filters).all()
            if len(knobs) == 0:
                raise Exception(
                    "KnobCatalog cannot find knob of name {} in {}@{}".format(
                        knob_name, system.type, system.version))
            knob = knobs[0]
            # check if knob is ENUM
            if knob.var_type == VarType.ENUM.value:
                # enum_vals is a comma delimited list
                enum_vals = knob.enum_vals.split(",")
                if len(enum_vals) > 2:
                    # more than 2 values requires dummy encoding
                    n_values.append(len(enum_vals))
                    cat_knob_indices.append(i)
                    cat_knob_names.append(knob_name)
                else:
                    # knob is binary
                    noncat_knob_names.append(knob_name)
                    binary_knob_indices.append(i)
            else:
                noncat_knob_names.append(knob_name)

        n_values = np.array(n_values)
        cat_knob_indices = np.array(cat_knob_indices)
        categorical_info = {'n_values': n_values,
                            'categorical_features': cat_knob_indices,
                            'cat_columnlabels': cat_knob_names,
                            'noncat_columnlabels': noncat_knob_names,
                            'binary_vars': binary_knob_indices}
        return categorical_info

    @staticmethod
    def load_pipeline_data(workload_id, pipeline_run_id, task_type):
        filters = {
            PipelineData.workload_id == workload_id,
            PipelineData.pipeline_run_id == pipeline_run_id,
            PipelineData.task_type == task_type
        }
        return json.loads(PipelineData.query.filter(*filters).first().data)
    
    @staticmethod
    def combine_duplicate_rows(X_matrix, y_matrix, rowlabels):
        X_unique, idxs, invs, cts = np.unique(X_matrix,
                                              return_index=True,
                                              return_inverse=True,
                                              return_counts=True,
                                              axis=0)
        num_unique = X_unique.shape[0]
        if num_unique == X_matrix.shape[0]:
            # No duplicate rows

            # For consistency, tuple the rowlabels
            rowlabels = np.array([tuple([x]) for x in rowlabels])  # pylint: disable=bad-builtin,deprecated-lambda
            return X_matrix, y_matrix, rowlabels

        # Combine duplicate rows
        y_unique = np.empty((num_unique, y_matrix.shape[1]))
        rowlabels_unique = np.empty(num_unique, dtype=tuple)
        ix = np.arange(X_matrix.shape[0])
        for i, count in enumerate(cts):
            if count == 1:
                y_unique[i, :] = y_matrix[idxs[i], :]
                rowlabels_unique[i] = (rowlabels[idxs[i]],)
            else:
                dup_idxs = ix[invs == i]
                y_unique[i, :] = np.median(y_matrix[dup_idxs, :], axis=0)
                rowlabels_unique[i] = tuple(rowlabels[dup_idxs])
        return X_unique, y_unique, rowlabels_unique