import numpy as np
from app.analysis.dc.density_cluster import DensityCluster
import matplotlib.pyplot as plt

Compound = './Compound.txt'
X = np.loadtxt(Compound, delimiter='\t', usecols=[0, 1])
y_pred = DensityCluster(percent=2.0, kernel='gaussian').fit_predict(X)
dc = DensityCluster().fit(X)
print(dc.predict([[1, 2, 1], [12, 3, 2]], sample_weight=[1.0, 3.0]))
plt.scatter(X[:, 0], X[:, 1], c=y_pred)
plt.show()
