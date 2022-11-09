import numpy as np
import tensorflow as tf
from gpflow import settings
from sklearn.utils import assert_all_finite, check_array
from sklearn.utils.validation import FLOAT_DTYPES
from loguru import logger

class GPRGDResult():

    def __init__(self, ypreds=None, sigmas=None, minl=None, minl_conf=None):
        self.ypreds = ypreds
        self.sigmas = sigmas
        self.minl = minl
        self.minl_conf = minl_conf


def tf_optimize(model, Xnew_arr, learning_rate=0.01, maxiter=100, ucb_beta=3.,
                active_dims=None, bounds=None, debug=True):
    Xnew_arr = check_array(Xnew_arr, copy=False, warn_on_dtype=True, dtype=FLOAT_DTYPES)

    Xnew = tf.Variable(Xnew_arr, name='Xnew', dtype=settings.float_type)
    if bounds is None:
        lower_bound = tf.constant(-np.infty, dtype=settings.float_type)
        upper_bound = tf.constant(np.infty, dtype=settings.float_type)
    else:
        lower_bound = tf.constant(bounds[0], dtype=settings.float_type)
        upper_bound = tf.constant(bounds[1], dtype=settings.float_type)
    Xnew_bounded = tf.minimum(tf.maximum(Xnew, lower_bound), upper_bound)

    if active_dims:
        indices = []
        updates = []
        n_rows = Xnew_arr.shape[0]
        for c in active_dims:
            for r in range(n_rows):
                indices.append([r, c])
                updates.append(Xnew_bounded[r, c])
        part_X = tf.scatter_nd(indices, updates, Xnew_arr.shape)
        Xin = part_X + tf.stop_gradient(-part_X + Xnew_bounded)
    else:
        Xin = Xnew_bounded

    beta_t = tf.constant(ucb_beta, name='ucb_beta', dtype=settings.float_type)
    fmean, fvar, kvar, kls, lvar = model._build_predict(Xin)  # pylint: disable=protected-access
    y_mean_var = model.likelihood.predict_mean_and_var(fmean, fvar)
    y_mean = y_mean_var[0]
    y_var = y_mean_var[1]
    y_std = tf.sqrt(y_var)
    loss = tf.subtract(y_mean, tf.multiply(beta_t, y_std), name='loss_fn')
    opt = tf.train.AdamOptimizer(learning_rate, epsilon=1e-6)
    train_op = opt.minimize(loss)
    variables = opt.variables()
    init_op = tf.variables_initializer([Xnew] + variables)
    session = model.enquire_session(session=None)
    with session.as_default():
        session.run(init_op)
        for i in range(maxiter):
            session.run(train_op)
        Xnew_value = session.run(Xnew_bounded)
        y_mean_value = session.run(y_mean)
        y_std_value = session.run(y_std)
        loss_value = session.run(loss)
        assert_all_finite(Xnew_value)
        assert_all_finite(y_mean_value)
        assert_all_finite(y_std_value)
        assert_all_finite(loss_value)
        if debug:
            logger.info("kernel variance: %f" % session.run(kvar))
            logger.info("kernel lengthscale: %f" % session.run(kls))
            logger.info("likelihood variance: %f" % session.run(lvar))
        return GPRGDResult(y_mean_value, y_std_value, loss_value, Xnew_value)