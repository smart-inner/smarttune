# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import log,floor
import tqdm, os, pickle
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
class ESPOT:
    """
    This class allows to run DSPOT algorithm on univariate dataset (upper and lower bounds)
    
    Attributes
    ----------
    proba : float
        Detection level (risk), chosen by the user
        
    depth : int
        Number of observations to compute the moving average
        
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
    def __init__(self, q = 1e-4, depth = 10):
        self.proba = q
        self.n = 0
        self.depth = depth
        self.W = None
        
        nonedict =  {'up':None,'down':None}
        
        self.extreme_quantile = dict.copy(nonedict)
        self.init_threshold = dict.copy(nonedict)
        self.history_peaks = dict.copy(nonedict)
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
            initial batch to calibrate the algorithm
            
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

        n_init = init_data.size - self.depth
        
        M = backMean(init_data, self.depth)
        T = init_data[self.depth:]-M[:-1] # new variable
        
        S = np.sort(T)     # we sort T to get the empirical quantile
        self.init_threshold['up'] = S[int(0.98*n_init)] # t is fixed for the whole algorithm
        self.init_threshold['down'] = S[int(0.02*n_init)] # t is fixed for the whole algorithm
        # initial peaks
        self.history_peaks['up'] = T[T>self.init_threshold['up']]
        self.history_peaks['down'] = T[T<self.init_threshold['down']]
        self.peaks['up'] = self.history_peaks['up']-self.init_threshold['up']
        self.peaks['down'] = -(self.history_peaks['down'] - self.init_threshold['down'] )
        self.Nt['up'] = self.peaks['up'].size
        self.Nt['down'] = self.peaks['down'].size
        self.n = n_init
        self.W = init_data[-self.depth:]
        
        if verbose:
            print('Initial threshold : %s' % self.init_threshold)
            print('Number of peaks : %s' % self.Nt)
            print('Grimshaw maximum log-likelihood estimation ... ')
            
        l = {'up':None,'down':None}
        for side in ['up','down']:
            g,s,l[side] = self._grimshaw(side)
            self.extreme_quantile[side] = self._quantile(side,g,s)
            self.gamma[side] = g
            self.sigma[side] = s


    def _update_one_side(self, side, value):
        if side == 'up':
            min_index = np.argmin(self.history_peaks[side], axis=0)
            if value > self.history_peaks[side][min_index]:
                weight = 0.99 if self.history_peaks[side][min_index] > 0 else 1.01
                self.init_threshold[side] = weight * self.history_peaks[side][min_index]
                self.history_peaks[side][min_index] = value
                init_data = self.history_peaks[side]
                self.history_peaks[side] = init_data[init_data>self.init_threshold[side]]
                self.peaks[side] = self.history_peaks[side] - self.init_threshold[side]
        elif side == 'down':
            max_index = np.argmax(self.history_peaks[side], axis=0)
            if value < self.history_peaks[side][max_index]:
                weight = 1.01 if self.history_peaks[side][max_index] > 0 else 0.99
                self.init_threshold[side] = weight * self.history_peaks[side][max_index]
                self.history_peaks[side][max_index] = value
                init_data = self.history_peaks[side]
                self.history_peaks[side] = init_data[init_data<self.init_threshold[side]]
                self.peaks[side] = -(self.history_peaks[side]-self.init_threshold[side])
        self.Nt[side] = self.peaks[side].size
        g,s,_ = self._grimshaw('up')
        self.extreme_quantile['up'] = self._quantile('up',g,s)
        self.gamma[side] = g
        self.sigma[side] = s


    def predict(self, data, with_alarm = True):
        """
        Run biDSPOT on the stream
        
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
            Mi = self.ewma(self.W)# DAWNSON IN YOUR AREA HAHA HAHA
            Ni = stream_data[i]-Mi
            # If the observed value exceeds the current threshold (alarm case)
            if Ni>self.extreme_quantile['up'] :
                # if we want to alarm, we put it in the alarm list
                if with_alarm:
                    alarm.append(i)
                # otherwise we add it in the peaks
                else:
                    self._update_one_side('up', Ni)
                    #self.peaks['up'] = np.append(self.peaks['up'],Ni-self.init_threshold['up'])
                    #self.Nt['up'] += 1
                    #self.n += 1
                    # and we update the thresholds

                    #g,s,l = self._grimshaw('up')
                    #self.extreme_quantile['up'] = self._quantile('up',g,s)
                    #W = np.append(W[1:],stream_data[i])
                    
            # case where the value exceeds the initial threshold but not the alarm ones
            elif Ni>self.init_threshold['up']:
                    self._update_one_side('up', Ni)
                    # we add it in the peaks
                    #self.peaks['up'] = np.append(self.peaks['up'],Ni-self.init_threshold['up'])
                    #self.Nt['up'] += 1
                    #self.n += 1
                    # and we update the thresholds
                    #g,s,l = self._grimshaw('up')
                    #self.extreme_quantile['up'] = self._quantile('up',g,s)
                    #W = np.append(W[1:],stream_data[i])
                    
            elif Ni<self.extreme_quantile['down'] :
                # if we want to alarm, we put it in the alarm list
                if with_alarm:
                    alarm.append(i)
                # otherwise we add it in the peaks
                else:
                    self._update_one_side('down', Ni)
                    #self.peaks['down'] = np.append(self.peaks['down'],-(Ni-self.init_threshold['down']))
                    #self.Nt['down'] += 1
                    #self.n += 1
                    # and we update the thresholds

                    #g,s,l = self._grimshaw('down')
                    #self.extreme_quantile['down'] = self._quantile('down',g,s)
                    #self.W = np.append(self.W[1:],stream_data[i])
                    
            # case where the value exceeds the initial threshold but not the alarm ones
            elif Ni<self.init_threshold['down']:
                    self._update_one_side('down', Ni)
                    # we add it in the peaks
                    #self.peaks['down'] = np.append(self.peaks['down'],-(Ni-self.init_threshold['down']))
                    #self.Nt['down'] += 1
                    #self.n += 1
                    # and we update the thresholds

                    #g,s,l = self._grimshaw('down')
                    #self.extreme_quantile['down'] = self._quantile('down',g,s)
                    #W = np.append(W[1:],stream_data[i])
            self.n += 1
            self.W = np.append(self.W[1:],stream_data[i])

                
            thup.append(self.extreme_quantile['up']+Mi) # upper thresholds record
            thdown.append(self.extreme_quantile['down']+Mi) # lower thresholds record
        
        return {'upper_thresholds' : thup,'lower_thresholds' : thdown, 'alarms': alarm}


    def _rootsFinder(self, fun,jac,bounds,npoints,method):
        """
        Find possible roots of a scalar function
        
        Parameters
        ----------
        fun : function
            scalar function 
        jac : function
            first order derivative of the function  
        bounds : tuple
            (min,max) interval for the roots search    
        npoints : int
            maximum number of roots to output      
        method : str
            'regular' : regular sample of the search interval, 'random' : uniform (distribution) sample of the search interval
        
        Returns
        ----------
        numpy.array
            possible roots of the function
        """
        if method == 'regular':
            step = (bounds[1]-bounds[0])/(npoints+1)
            X0 = np.arange(bounds[0]+step,bounds[1],step)
        elif method == 'random':
            X0 = np.random.uniform(bounds[0],bounds[1],npoints)
        
        def objFun(X,f,jac):
            g = 0
            j = np.zeros(X.shape)
            i = 0
            for x in X:
                fx = f(x)
                g = g+fx**2
                j[i] = 2*fx*jac(x)
                i = i+1
            return g,j
        
        opt = minimize(lambda X:objFun(X,fun,jac), X0, 
                       method='L-BFGS-B', 
                       jac=True, bounds=[bounds]*len(X0))
        
        X = opt.x
        np.round(X,decimals = 5)
        return np.unique(X)
    
    
    def _log_likelihood(self, Y,gamma,sigma):
        """
        Compute the log-likelihood for the Generalized Pareto Distribution (μ=0)
        
        Parameters
        ----------
        Y : numpy.array
            observations
        gamma : float
            GPD index parameter
        sigma : float
            GPD scale parameter (>0)   
        Returns
        ----------
        float
            log-likelihood of the sample Y to be drawn from a GPD(γ,σ,μ=0)
        """
        n = Y.size
        if gamma != 0:
            tau = gamma/sigma
            L = -n * log(sigma) - ( 1 + (1/gamma) ) * ( np.log(1+tau*Y) ).sum()
        else:
            L = n * ( 1 + log(Y.mean()) )
        return L


    def _grimshaw(self,side,epsilon = 1e-8, n_points = 8):
        """
        Compute the GPD parameters estimation with the Grimshaw's trick
        
        Parameters
        ----------
        epsilon : float
            numerical parameter to perform (default : 1e-8)
        n_points : int
            maximum number of candidates for maximum likelihood (default : 10)
        Returns
        ----------
        gamma_best,sigma_best,ll_best
            gamma estimates, sigma estimates and corresponding log-likelihood
        """
        def u(s):
            return 1 + np.log(s).mean()
            
        def v(s):
            return np.mean(1/s)
        
        def w(Y,t):
            s = 1+t*Y
            us = u(s)
            vs = v(s)
            return us*vs-1
        
        def jac_w(Y,t):
            s = 1+t*Y
            us = u(s)
            vs = v(s)
            jac_us = (1/t)*(1-vs)
            jac_vs = (1/t)*(-vs+np.mean(1/s**2))
            return us*jac_vs+vs*jac_us
            
    
        Ym = self.peaks[side].min()
        YM = self.peaks[side].max()
        Ymean = self.peaks[side].mean()
        
        
        a = -1/YM
        if abs(a)<2*epsilon:
            epsilon = abs(a)/n_points
        
        a = a + epsilon
        b = 2*(Ymean-Ym)/(Ymean*Ym)
        c = 2*(Ymean-Ym)/(Ym**2)
    
        # We look for possible roots
        left_zeros = self._rootsFinder(lambda t: w(self.peaks[side],t),
                                 lambda t: jac_w(self.peaks[side],t),
                                 (a+epsilon,-epsilon),
                                 n_points,'regular')
        
        right_zeros = self._rootsFinder(lambda t: w(self.peaks[side],t),
                                  lambda t: jac_w(self.peaks[side],t),
                                  (b,c),
                                  n_points,'regular')
    
        # all the possible roots
        zeros = np.concatenate((left_zeros,right_zeros))
        
        # 0 is always a solution so we initialize with it
        gamma_best = 0
        sigma_best = Ymean
        ll_best = self._log_likelihood(self.peaks[side],gamma_best,sigma_best)
        
        # we look for better candidates
        for z in zeros:
            gamma = u(1+z*self.peaks[side])-1
            sigma = gamma/z
            ll = self._log_likelihood(self.peaks[side],gamma,sigma)
            if ll>ll_best:
                gamma_best = gamma
                sigma_best = sigma
                ll_best = ll
    
        return gamma_best,sigma_best,ll_best

    

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

    def ewma(self, X, alpha = 0.1):
        s = [X[0]]
        for i in range(1, len(X)):
            temp = alpha * X[i] + (1 - alpha) * s[-1]
            s.append(temp)  
        return s[-1]
    

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

    def save(self, filename):
        """
        Save the model in a file
        
        Parameters
        ----------
        filename : str
            name of the file
        """
        # if file exists, we delete it
        if os.path.isfile(filename):
            os.remove(filename)
            with open(filename, 'wb') as output:
                pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
        else:
            with open(filename, 'wb') as output:
                pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load(filename):
        """
        Load a model from a file
        
        Parameters
        ----------
        filename : str
            name of the file
        """
        with open(filename, 'rb') as input:
            return pickle.load(input)
