import numpy as np
from app.analysis.dc import DensityCluster
import matplotlib.pyplot as plt

Compound = './Compound.txt'
X = np.loadtxt(Compound, delimiter='\t', usecols=[0, 1])
y_pred = DensityCluster(percent=2.0).fit_predict(X)
print(y_pred)
#dc = DensityCluster().fit(X)
#print(dc.predict([[1, 2], [12, 3]], sample_weight=[1.0, 3.0]))
#plt.scatter(X[:, 0], X[:, 1], c=y_pred)
#plt.show()
