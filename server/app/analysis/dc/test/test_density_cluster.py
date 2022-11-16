import numpy as np
from app.analysis.dc import DensityCluster
import matplotlib.pyplot as plt

Compound = './Compound.txt'
X = np.loadtxt(Compound, delimiter='\t', usecols=[0, 1])
y_pred = DensityCluster(percent=1.1).fit_predict(X)
print(y_pred)
plt.scatter(X[:, 0], X[:, 1], c=y_pred)
plt.show()
