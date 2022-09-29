from loguru import logger
import time, copy
from app.utils import *

def aggregate_data(wkld_results):
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
    aggregated_data = DataProcess.aggregate_data(wkld_results)

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
    exec_time = TaskUtil.save_execution_time("periodic_task", start_ts, "aggregate_data")
    logger.info("Done aggregate data (%.1f seconds)." % exec_time)
    return knob_data, metric_data