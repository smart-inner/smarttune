from app.analysis.preprocessing import Bin, get_shuffle_indices
from app.analysis.factor_analysis import FactorAnalysis
from app.analysis.cluster import KMeansClusters, create_kselection_model
from app.utils import *
from loguru import logger
import numpy as np
import time

def run_workload_characterization(metric_data, system_id=None):
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

    # Remove any duplicate columns
    unique_matrix, unique_idxs = np.unique(nonconst_matrix, axis=1, return_index=True)
    unique_columnlabels = [nonconst_columnlabels[idx] for idx in unique_idxs]

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

    logger.info("Found optimal number of clusters: %d" % gapk.optimal_num_clusters_)

    # Get pruned metrics, cloest samples of each cluster center
    pruned_metrics = kmeans_models.cluster_map_[gapk.optimal_num_clusters_].get_closest_samples()

    # Return pruned metrics
    exec_time = TaskUtil.save_execution_time("periodic_task", start_ts, "run_workload_characterization")
    logger.info("Workload characterization finished in %.0f seconds." % exec_time)
    return pruned_metrics