import numpy as np
import heapq
from sklearn import metrics

def cal_labels(X, sample_weight, centers, return_inertia=True):
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

def cal_distance(X, sample_weight):
    """
    Calculate the distance between any two points in X
    Parameters:
    -----------
    X : {ndarray, sparse matrix} of shape (n_samples, n_features)
        The input samples to assign to the labels. If sparse matrix, must
        be in CSR format.
    sample_weight : array-like of shape (n_samples,), default=None
            The weights for each observation in X. If None, all observations
            are assigned equal weight.
    Returns
    --------
    distance: ndarray of shape (n_samples, n_samples)
        The distance matrix for any two points
    """
    X = np.multiply(X.T, sample_weight).T
    distance = np.zeros(shape=(len(X), len(X)))
    for i in range(len(X)):
        for j in range(len(X)):
            if i > j:
                distance[i][j] = distance[j][i]
            elif i < j:
                distance[i][j] = np.sqrt(np.sum(np.power(X[i] - X[j], 2)))
    return distance

def cal_dc(distance, percent):
    """
    Calculate the dc for clustering
    Parameters:
    -----------
    distance: ndarray of shape (n_samples, n_samples)
        The distance matrix for samples
    percent: float
        sort all distances in ascending order, and use 'percent' position as dc.
    Returns
    --------
    dc: float
        The cutoff distance for calculating rho.
    """
    temp = []
    for i in range(len(distance[0])):
        for j in range(i + 1, len(distance[0])):
            temp.append(distance[i][j])
    temp.sort()
    return temp[int(len(temp) * percent / 100)]

def cal_rho(distance, dc):
    """
    Calculate the density for every point
    Parameters:
    -----------
    distance: ndarray of shape (n_samples, n_samples)
        The distance matrix for samples
    dc: float
        The cutoff distance
    Returns
    --------
    rho: ndarray of shape (n_samples, )
        The density for every point.
    """
    rho = np.zeros(shape=len(distance))
    for i, dis in enumerate(distance):
        rho[i] = np.sum(np.exp(-(dis / dc) ** 2))
    
    return rho

def cal_delta(distance, rho):
    """
    Calculate the delta for every point
    Parameters:
    -----------
    distance: ndarray of shape (n_samples, n_samples)
        The distance matrix for samples
    rho: ndarray of shape (n_samples, )
        The density for every point.
    Returns
    --------
    delta: ndarray of shape (n_samples, )
        The delta for every point.
    """
    delta = np.zeros(shape=len(distance))
    for i, _ in enumerate(distance):
        density_larger_than_point = np.squeeze(np.argwhere(rho > rho[i]))
        if density_larger_than_point.size != 0:
            distance_between_larger_point = distance[i][density_larger_than_point]
            delta[i] = np.min(distance_between_larger_point)
            min_distance_index = np.squeeze(np.argwhere(distance_between_larger_point == delta[i]))
            if min_distance_index.size >= 2:
                min_distance_index = np.random.choice(a=min_distance_index)
        else:
            delta[i] = np.max(distance)
    return delta

def cal_cluster_centers(X, sample_weight, rho, delta, min_centers, max_centers):
    sigma = np.multiply(rho, delta)
    X_weight = np.multiply(X.T, sample_weight).T
    score = 0.0
    best_centers = None
    for i in range(min_centers, max_centers+1):
        centers = X_weight.take(heapq.nlargest(i, range(len(sigma)), sigma.take), axis=0)
        labels = cal_labels(X, sample_weight, centers, return_inertia=False)
        if metrics.silhouette_score(X_weight, labels) > score:
            score = metrics.silhouette_score(X_weight, labels)
            best_centers = centers
    return best_centers
