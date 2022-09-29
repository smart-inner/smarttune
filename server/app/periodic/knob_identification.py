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