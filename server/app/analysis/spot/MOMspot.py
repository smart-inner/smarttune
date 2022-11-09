# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import log,floor
import tqdm
from scipy.optimize import minimize
# colors for plot
deep_saffron = '#FF9933'
air_force_blue = '#5D8AA8'

def backMean(X,d):
    M = []
    w = X[:d].sum()
    M.append(w/d)
    for i in range(d,len(X)):
        w = w - X[i-d] + X[i]
        M.append(w/d)
    return np.array(M)
class momSPOT:
    """
    This class allows to run biSPOT algorithm on univariate dataset (upper and lower bounds)
    
    Attributes
    ----------
    proba : float
        Detection level (risk), chosen by the user
        
    extreme_quantile : float
        current threshold (bound between normal and abnormal events)
    
    init_threshold : float
        initial threshold computed during the calibration step
    
    peaks : numpy.array
        array of peaks (excesses above the initial threshold)
    
    n : int
        number of observed values
    
    Nt : int
        number of observed peaks
    """
    def __init__(self, q = 1e-4):
        """
        Constructor
        Parameters
        ----------
        q
            Detection level (risk)
    
        Returns
        ----------
        biSPOT object
        """
        self.proba = q
        self.n = 0
        nonedict =  {'up':None,'down':None}
        
        self.extreme_quantile = dict.copy(nonedict)
        self.init_threshold = dict.copy(nonedict)
        self.peaks = dict.copy(nonedict)
        self.gamma = dict.copy(nonedict)
        self.sigma = dict.copy(nonedict)
        self.Nt = {'up':0,'down':0}
        
        
    def __str__(self):
        s = ''
        s += 'Streaming Peaks-Over-Threshold Object\n'
        s += 'Detection level q = %s\n' % self.proba
            
        if self.n == 0:
            s += 'Algorithm initialized : No\n'
        else:
            s += 'Algorithm initialized : Yes\n'
            s += '\t initial threshold : %s\n' % self.init_threshold
            s += '\t number of peaks  : %s\n' % self.Nt
            s += '\t upper extreme quantile : %s\n' % self.extreme_quantile['up']
            s += '\t lower extreme quantile : %s\n' % self.extreme_quantile['down']
        return s
    
    
    def fit(self,train_data, verbose = True):
        """
        Run the calibration (initialization) step
        
        Parameters
        ----------
        train_data : list, numpy.array or pandas.Series
            initial batch to calibrate the algorithm ()
        
        verbose : bool
            (default = True) If True, gives details about the batch initialization
        """
        if isinstance(train_data,list):
            init_data = np.array(train_data)
        elif isinstance(train_data, np.ndarray):
            init_data = train_data
        elif isinstance(train_data, pd.Series):
            init_data = train_data.values
        else:
            raise TypeError("This train_data format (%s) is not supported." % type(train_data))
        
        n_init = init_data.size
        
        S = np.sort(init_data)     # we sort X to get the empirical quantile
        self.init_threshold['up'] = S[int(0.98*n_init)] # t is fixed for the whole algorithm
        self.init_threshold['down'] = S[int(0.02*n_init)] # t is fixed for the whole algorithm

        # initial peaks
        self.peaks['up'] = init_data[init_data>self.init_threshold['up']]-self.init_threshold['up']
        self.peaks['down'] = -(init_data[init_data<self.init_threshold['down']]-self.init_threshold['down'])
        self.Nt['up'] = self.peaks['up'].size
        self.Nt['down'] = self.peaks['down'].size
        self.n = n_init
        
        if verbose:
            print('Initial threshold : %s' % self.init_threshold)
            print('Number of peaks : %s' % self.Nt)
            #print('Grimshaw maximum log-likelihood estimation ... ', end = '')
            
        l = {'up':None,'down':None}
        for side in ['up','down']:
            g,s,l[side] = self._MOM(side)
            self.extreme_quantile[side] = self._quantile(side,g,s)
            self.gamma[side] = g
            self.sigma[side] = s

    
    def predict(self, data, with_alarm = True):
        """
        Run biSPOT on the stream
        
        Parameters
        ----------
        data : numpy.array
            data for the run (list, np.array or pd.series)

        with_alarm : bool
            (default = True) If False, SPOT will adapt the threshold assuming \
            there is no abnormal values
        Returns
        ----------
        dict
            keys : 'upper_thresholds', 'lower_thresholds' and 'alarms'
            
            '***-thresholds' contains the extreme quantiles and 'alarms' contains \
            the indexes of the values which have triggered alarms
            
        """
        if isinstance(data,list):
            stream_data = np.array(data)
        elif isinstance(data,np.ndarray):
            stream_data = data
        elif isinstance(data,pd.Series):
            stream_data = data.values
        else:
            raise TypeError('This data format (%s) is not supported.' % type(data))
        
        # list of the thresholds
        thup = []
        thdown = []
        alarm = []
        # Loop over the stream
        for i in tqdm.tqdm(range(stream_data.size)):
    
            # If the observed value exceeds the current threshold (alarm case)
            if stream_data[i]>self.extreme_quantile['up'] :
                # if we want to alarm, we put it in the alarm list
                if with_alarm:
                    alarm.append(i)
                # otherwise we add it in the peaks
                else:
                    self.peaks['up'] = np.append(self.peaks['up'],stream_data[i]-self.init_threshold['up'])
                    self.Nt['up'] += 1
                    self.n += 1
                    # and we update the thresholds

                    g,s,l = self._MOM('up')
                    self.extreme_quantile['up'] = self._quantile('up',g,s)

            # case where the value exceeds the initial threshold but not the alarm ones
            elif stream_data[i]>self.init_threshold['up']:
                    # we add it in the peaks
                    self.peaks['up'] = np.append(self.peaks['up'],stream_data[i]-self.init_threshold['up'])
                    self.Nt['up'] += 1
                    self.n += 1
                    # and we update the thresholds

                    g,s,l = self._MOM('up')
                    self.extreme_quantile['up'] = self._quantile('up',g,s)
                    
            elif stream_data[i]<self.extreme_quantile['down'] :
                # if we want to alarm, we put it in the alarm list
                if with_alarm:
                    alarm.append(i)
                # otherwise we add it in the peaks
                else:
                    self.peaks['down'] = np.append(self.peaks['down'],-(stream_data[i]-self.init_threshold['down']))
                    self.Nt['down'] += 1
                    self.n += 1
                    # and we update the thresholds

                    g,s,l = self._MOM('down')
                    self.extreme_quantile['down'] = self._quantile('down',g,s)

            # case where the value exceeds the initial threshold but not the alarm ones
            elif stream_data[i]<self.init_threshold['down']:
                    # we add it in the peaks
                    self.peaks['down'] = np.append(self.peaks['down'],-(stream_data[i]-self.init_threshold['down']))
                    self.Nt['down'] += 1
                    self.n += 1
                    # and we update the thresholds

                    g,s,l = self._MOM('down')
                    self.extreme_quantile['down'] = self._quantile('down',g,s)
            else:
                self.n += 1

                
            thup.append(self.extreme_quantile['up']) # thresholds record
            thdown.append(self.extreme_quantile['down']) # thresholds record
        
        return {'upper_thresholds' : thup,'lower_thresholds' : thdown, 'alarms': alarm}


    def _MOM(self,side,epsilon = 1e-8, n_points = 10):
        Yi = self.peaks[side]
        avg = np.mean(Yi)
        var = np.var(Yi)
        sigma = 0.5*avg*(avg**2/var + 1)
        gamma = 0.5*(avg**2/var - 1)
        return gamma,sigma,100

    
    def _quantile(self,side,gamma,sigma):
        """
        Compute the quantile at level 1-q for a given side
        
        Parameters
        ----------
        side : str
            'up' or 'down'
        gamma : float
            GPD parameter
        sigma : float
            GPD parameter
        Returns
        ----------
        float
            quantile at level 1-q for the GPD(γ,σ,μ=0)
        """
        if side == 'up':
            r = self.n * self.proba / self.Nt[side]
            if gamma != 0:
                return self.init_threshold['up'] + (sigma/gamma)*(pow(r,-gamma)-1)
            else:
                return self.init_threshold['up'] - sigma*log(r)
        elif side == 'down':
            r = self.n * self.proba / self.Nt[side]
            if gamma != 0:
                return self.init_threshold['down'] - (sigma/gamma)*(pow(r,-gamma)-1)
            else:
                return self.init_threshold['down'] + sigma*log(r)
        else:
            print('error : the side is not right')
        
    
    def plot(self, data, run_results, with_alarm = True):
        """
        Plot the results of given by the run
        
        Parameters
        ----------
        data : numpy.array
            data for the run (list, np.array or pd.series)
        run_results : dict
            results given by the 'run' method
        with_alarm : bool
            (default = True) If True, alarms are plotted.
        Returns
        ----------
        list
            list of the plots
            
        """

        if isinstance(data,list):
            stream_data = np.array(data)
        elif isinstance(data,np.ndarray):
            stream_data = data
        elif isinstance(data,pd.Series):
            stream_data = data.values
        else:
            raise TypeError('This data format (%s) is not supported.' % type(data))

        x = range(stream_data.size)
        K = run_results.keys()
        
        ts_fig, = plt.plot(x,stream_data,color=air_force_blue)
        fig = [ts_fig]
        
        if 'upper_thresholds' in K:
            thup = run_results['upper_thresholds']
            uth_fig, = plt.plot(x,thup,color=deep_saffron,lw=2,ls='dashed')
            fig.append(uth_fig)
            
        if 'lower_thresholds' in K:
            thdown = run_results['lower_thresholds']
            lth_fig, = plt.plot(x,thdown,color=deep_saffron,lw=2,ls='dashed')
            fig.append(lth_fig)
        
        if with_alarm and ('alarms' in K):
            alarm = run_results['alarms']
            al_fig = plt.scatter(alarm,stream_data[alarm],color='red')
            fig.append(al_fig)
            
        plt.xlim((0,stream_data.size))
        plt.show()
        
        return fig
