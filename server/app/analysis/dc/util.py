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
    closest_leader: ndarray of shape (n_samples, )
        The closest point for every point
    """
    delta = np.zeros(shape=len(distance))
    closest_leader = np.zeros(shape=len(distance), dtype=np.int32)
    for i, _ in enumerate(distance):
        density_larger_than_point = np.squeeze(np.argwhere(rho > rho[i]))
        if density_larger_than_point.size != 0:
            distance_between_larger_point = distance[i][density_larger_than_point]
            delta[i] = np.min(distance_between_larger_point)
            min_distance_index = np.squeeze(np.argwhere(distance_between_larger_point == delta[i]))
            if min_distance_index.size >= 2:
                min_distance_index = np.random.choice(a=min_distance_index)
            if distance_between_larger_point.size > 1:
                closest_leader[i] = density_larger_than_point[min_distance_index]
            else:
                closest_leader[i] = density_larger_than_point
        else:
            delta[i] = np.max(distance)
            closest_leader[i] = i
    return delta, closest_leader

def _clustering(closest_leader, chose_list):
    for i in range(len(closest_leader)):
            while closest_leader[i] not in chose_list:
                j = closest_leader[i]
                closest_leader[i] = closest_leader[j]
    labels = np.zeros(shape=len(closest_leader), dtype=np.int32)
    for i, A in enumerate(chose_list):
        for j, B in enumerate(closest_leader):
            if A == B:
                labels[j] = i
    return labels

def cal_cluster_centers(X, sample_weight, closest_leader, sigma, min_centers, max_centers):
    X = np.multiply(X.T, sample_weight).T
    score = 0.0
    best_centers = None
    best_labels = None
    for i in range(min_centers, max_centers+1):
        chose_list = heapq.nlargest(i, range(len(sigma)), sigma.take)
        centers = X.take(chose_list, axis=0)
        closest_leader_copy = closest_leader.copy()
        labels = _clustering(closest_leader_copy, chose_list)
        if metrics.calinski_harabaz_score(X, labels) > score:
            score = metrics.calinski_harabaz_score(X, labels)
            best_centers = centers
            best_labels = labels
    return best_centers, best_labels
