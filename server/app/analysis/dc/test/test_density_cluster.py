import numpy as np
from app.analysis.dc.density_cluster import DensityCluster
import matplotlib.pyplot as plt

Compound = './Compound.txt'
X = np.loadtxt(Compound, delimiter='\t', usecols=[0, 1])
y_pred = DensityCluster(percent=2.0, kernel='gaussian').fit_predict(X)
dc = DensityCluster().fit(X)
print(dc.predict([[0, 0], [12, 3]], sample_weight=[2.0, 3.0]))
plt.scatter(X[:, 0], X[:, 1], c=y_pred)
plt.show()
