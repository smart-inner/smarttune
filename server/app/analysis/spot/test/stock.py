import numpy as np
import matplotlib.pyplot as plt
from app.analysis.spot import bidSPOT, biSPOT, ESPOT, momSPOT, DRSPOT
import pandas as pd
import time
f = './edf_stocks.csv'
import pickle

P = pd.read_csv(f)

# stream
u_data = (P['DATE'] == '2017-02-09')
data = P['LOW'][u_data].values

# initial batch
u_init_data = (P['DATE'] == '2017-02-08') | (P['DATE'] == '2017-02-07') | (P['DATE'] == '2017-02-06')
init_data = P['LOW'][u_init_data].values



q = 1e-5             # risk parameter
d = 10                # depth
start = time.clock()
#s = ESPOT(q,d)     # bidSPOT object
#s = bidSPOT(q)  
#s = biSPOT(q)  
#s =DRSPOT(q)
s = momSPOT(q)
s.fit(init_data)     # data import
#s.initialize()             # initialization step
#with open('spot.pickle', 'wb') as f:
#    pickle.dump(s, f)
results = s.predict(data)     # run
end = time.clock()
t=end-start
print("Runtime is:",t) 
#del results['upper_thresholds'] # we can delete the upper thresholds
fig = s.plot(data, results)            # plot
