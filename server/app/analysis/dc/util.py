import numpy as np

def _labels(X, sample_weight, centers, return_inertia=True):
    """
    Compute the labels and the inertia of the given samples and centers.
    Parameters
    ----------
    X : {ndarray, sparse matrix} of shape (n_samples, n_features)
        The input samples to assign to the labels. If sparse matrix, must
        be in CSR format.
    sample_weight : ndarray of shape (n_samples,)
        The weights for each observation in X.
    centers : ndarray of shape (n_clusters, n_features)
        The cluster centers.
    return_inertia : bool, default=True
        Whether to compute and return the inertia.
    Returns
    -------
    labels : ndarray of shape (n_samples,)
        The resulting assignment.
    inertia : float
        Sum of squared distances of samples to their closest cluster center.
        Inertia is only returned if return_inertia is True.
    """
    points = np.multiply(X.T, sample_weight).T
    distance = np.array([])
    for point in points:
        distance = np.append(distance, np.linalg.norm(centers - point, axis=1), axis=0)
    distance = distance.reshape(len(points), len(centers))
    labels = np.argmin(distance, axis=1)
    if return_inertia:
        return labels, distance
    return labels