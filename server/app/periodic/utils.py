from loguru import logger
import time, copy
from datetime import datetime
from pytz import timezone
from pyDOE import lhs
from app import db
from app.models import *
from app.workflow.utils import *

TIME_ZONE = 'Asia/Shanghai'

def save_execution_time(start_ts, fn):
    end_ts = time.time()
    exec_time = end_ts - start_ts
    start_time = datetime.fromtimestamp(int(start_ts), timezone(TIME_ZONE))
    db.session.add(ExecutionTime(module="periodic_tasks", function=fn, tag="",
                                 start_time=start_time, execution_time=exec_time))


def aggregate_knobs_metrics_data(wkld_results):
    # Aggregates both the knob & metric data for the given workload.
    #
    # Parameters:
    #   wkld_results: result data belonging to this specific workload
    #
    # Returns: two dictionaries containing the knob & metric data as
    # a tuple

    # Now call the aggregate_data helper function to combine all knob &
    # metric data into matrices and also create row/column labels
    # (see the DataUtil class in website/utils.py)
    #
    # The aggregate_data helper function returns a dictionary of the form:
    #   - 'X_matrix': the knob data as a 2D numpy matrix (results x knobs)
    #   - 'y_matrix': the metric data as a 2D numpy matrix (results x metrics)
    #   - 'rowlabels': list of result ids that correspond to the rows in
    #         both X_matrix & y_matrix
    #   - 'X_columnlabels': a list of the knob names corresponding to the
    #         columns in the knob_data matrix
    #   - 'y_columnlabels': a list of the metric names corresponding to the
    #         columns in the metric_data matrix
    start_ts = time.time()
    aggregated_data = aggregate_data(wkld_results)

    # Separate knob & workload data into two "standard" dictionaries of the
    # same form
    knob_data = {
        'data': aggregated_data['X_matrix'],
        'rowlabels': aggregated_data['rowlabels'],
        'columnlabels': aggregated_data['X_columnlabels']
    }

    metric_data = {
        'data': aggregated_data['y_matrix'],
        'rowlabels': copy.deepcopy(aggregated_data['rowlabels']),
        'columnlabels': aggregated_data['y_columnlabels']
    }

    # Return the knob & metric data
    save_execution_time(start_ts, "aggregate_data")
    return knob_data, metric_data


def run_workload_characterization(metric_data, system=None):
    # Performs workload characterization on the metric_data and returns
    # a set of pruned metrics.
    #
    # Parameters:
    #   metric_data is a dictionary of the form:
    #     - 'data': 2D numpy matrix of metric data (results x metrics)
    #     - 'rowlabels': a list of identifiers for the rows in the matrix
    #     - 'columnlabels': a list of the metric names corresponding to
    #                       the columns in the data matrix
    start_ts = time.time()

    matrix = metric_data['data']
    columnlabels = metric_data['columnlabels']

    views = None if system is None else VIEWS_FOR_PRUNING.get(system.type, None)
    matrix, columnlabels = DataUtil.clean_metric_data(matrix, columnlabels, views)
    LOG.debug("Workload characterization ~ cleaned data size: %s", matrix.shape)

    # Bin each column (metric) in the matrix by its decile
    binner = Bin(bin_start=1, axis=0)
    binned_matrix = binner.fit_transform(matrix)

    # Remove any constant columns
    nonconst_matrix = []
    nonconst_columnlabels = []
    for col, cl in zip(binned_matrix.T, columnlabels):
        if np.any(col != col[0]):
            nonconst_matrix.append(col.reshape(-1, 1))
            nonconst_columnlabels.append(cl)
    assert len(nonconst_matrix) > 0, "Need more data to train the model"
    nonconst_matrix = np.hstack(nonconst_matrix)
    LOG.debug("Workload characterization ~ nonconst data size: %s", nonconst_matrix.shape)

    # Remove any duplicate columns
    unique_matrix, unique_idxs = np.unique(nonconst_matrix, axis=1, return_index=True)
    unique_columnlabels = [nonconst_columnlabels[idx] for idx in unique_idxs]

    LOG.debug("Workload characterization ~ final data size: %s", unique_matrix.shape)
    n_rows, n_cols = unique_matrix.shape

    # Shuffle the matrix rows
    shuffle_indices = get_shuffle_indices(n_rows)
    shuffled_matrix = unique_matrix[shuffle_indices, :]

    # Fit factor analysis model
    fa_model = FactorAnalysis()
    # For now we use 5 latent variables
    fa_model.fit(shuffled_matrix, unique_columnlabels, n_components=5)

    # Components: metrics * factors
    components = fa_model.components_.T.copy()
    LOG.info("Workload characterization first part costs %.0f seconds.", time.time() - start_ts)

    # Run Kmeans for # clusters k in range(1, num_nonduplicate_metrics - 1)
    # K should be much smaller than n_cols in detK, For now max_cluster <= 20
    kmeans_models = KMeansClusters()
    kmeans_models.fit(components, min_cluster=1,
                      max_cluster=min(n_cols - 1, 20),
                      sample_labels=unique_columnlabels,
                      estimator_params={'n_init': 50})

    # Compute optimal # clusters, k, using gap statistics
    gapk = create_kselection_model("gap-statistic")
    gapk.fit(components, kmeans_models.cluster_map_)

    LOG.debug("Found optimal number of clusters: %d", gapk.optimal_num_clusters_)

    # Get pruned metrics, cloest samples of each cluster center
    pruned_metrics = kmeans_models.cluster_map_[gapk.optimal_num_clusters_].get_closest_samples()

    # Return pruned metrics
    save_execution_time(start_ts, "run_workload_characterization")
    LOG.info("Workload characterization finished in %.0f seconds.", time.time() - start_ts)
    return pruned_metrics


def run_knob_identification(knob_data, metric_data, dbms):
    # Performs knob identification on the knob & metric data and returns
    # a set of ranked knobs.
    #
    # Parameters:
    #   knob_data & metric_data are dictionaries of the form:
    #     - 'data': 2D numpy matrix of knob/metric data
    #     - 'rowlabels': a list of identifiers for the rows in the matrix
    #     - 'columnlabels': a list of the knob/metric names corresponding
    #           to the columns in the data matrix
    #   dbms is the foreign key pointing to target dbms in DBMSCatalog
    #
    # When running the lasso algorithm, the knob_data matrix is set of
    # independent variables (X) and the metric_data is the set of
    # dependent variables (y).
    start_ts = time.time()

    knob_matrix = knob_data['data']
    knob_columnlabels = knob_data['columnlabels']

    metric_matrix = metric_data['data']
    metric_columnlabels = metric_data['columnlabels']

    # remove constant columns from knob_matrix and metric_matrix
    nonconst_knob_matrix = []
    nonconst_knob_columnlabels = []

    for col, cl in zip(knob_matrix.T, knob_columnlabels):
        if np.any(col != col[0]):
            nonconst_knob_matrix.append(col.reshape(-1, 1))
            nonconst_knob_columnlabels.append(cl)
    assert len(nonconst_knob_matrix) > 0, "Need more data to train the model"
    nonconst_knob_matrix = np.hstack(nonconst_knob_matrix)

    nonconst_metric_matrix = []
    nonconst_metric_columnlabels = []

    for col, cl in zip(metric_matrix.T, metric_columnlabels):
        if np.any(col != col[0]):
            nonconst_metric_matrix.append(col.reshape(-1, 1))
            nonconst_metric_columnlabels.append(cl)
    nonconst_metric_matrix = np.hstack(nonconst_metric_matrix)

    if ENABLE_DUMMY_ENCODER:
        # determine which knobs need encoding (enums with >2 possible values)

        categorical_info = DataUtil.dummy_encoder_helper(nonconst_knob_columnlabels,
                                                         dbms)
        # encode categorical variable first (at least, before standardize)
        dummy_encoder = DummyEncoder(categorical_info['n_values'],
                                     categorical_info['categorical_features'],
                                     categorical_info['cat_columnlabels'],
                                     categorical_info['noncat_columnlabels'])
        encoded_knob_matrix = dummy_encoder.fit_transform(
            nonconst_knob_matrix)
        encoded_knob_columnlabels = dummy_encoder.new_labels
    else:
        encoded_knob_columnlabels = nonconst_knob_columnlabels
        encoded_knob_matrix = nonconst_knob_matrix

    # standardize values in each column to N(0, 1)
    standardizer = StandardScaler()
    standardized_knob_matrix = standardizer.fit_transform(encoded_knob_matrix)
    standardized_metric_matrix = standardizer.fit_transform(nonconst_metric_matrix)

    # shuffle rows (note: same shuffle applied to both knob and metric matrices)
    shuffle_indices = get_shuffle_indices(standardized_knob_matrix.shape[0], seed=17)
    shuffled_knob_matrix = standardized_knob_matrix[shuffle_indices, :]
    shuffled_metric_matrix = standardized_metric_matrix[shuffle_indices, :]

    # run lasso algorithm
    lasso_model = LassoPath()
    lasso_model.fit(shuffled_knob_matrix, shuffled_metric_matrix, encoded_knob_columnlabels)

    # consolidate categorical feature columns, and reset to original names
    encoded_knobs = lasso_model.get_ranked_features()
    consolidated_knobs = consolidate_columnlabels(encoded_knobs)

    save_execution_time(start_ts, "run_knob_identification")
    LOG.info("Knob identification finished in %.0f seconds.", time.time() - start_ts)
    return consolidated_knobs
