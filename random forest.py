# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 16:55:44 2018

@author: peter_goodridge
"""


from get_currency_info import get_history
from sklearn.kernel_ridge import KernelRidge
from sklearn import datasets, linear_model
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from sklearn.ensemble import RandomForestRegressor

def prepare_returns(ticker):
    df = get_history(ticker, 2000)
    df.set_index('time', inplace = True)
    df = df.loc['04-01-2016':]
    return df


eth = prepare_returns('btc')[['close']]
btc = prepare_returns('eth')[['close']]

eth = sm.add_constant(eth)
result = sm.OLS(btc,eth).fit()

b = result.params[1]
adf_stats = adfuller(btc['close'] - b*eth['close'])
print("The p-value for the ADF test is ", adf_stats[1])

df = prepare_returns('eth')

df.loc[:, 'diff'] = eth - btc



df.loc[:, 'log_ret'] = np.log(df.close) - np.log(df.close.shift(1))
df.loc[:, 'log_ret2'] = np.log(df.close) - np.log(df.close.shift(2))
df.loc[:, 'log_ret3'] = np.log(df.close) - np.log(df.close.shift(3))
df.loc[:, 'log_ret4'] = np.log(df.close) - np.log(df.close.shift(4))
df.loc[:, 'log_ret5'] = np.log(df.close) - np.log(df.close.shift(4))
df.loc[:, 'minmax'] = df.high/df.low
df[['prev2', 'prev3', 'prev4', 'prev5']] = df.shift(1).loc[:, ['log_ret2', 'log_ret3', 'log_ret4', 'log_ret5']]

df.dropna(inplace = True)

for i in range(1,5):
    df[['prev_ret{}'.format(i), 'prev_from', 'prev_to']] = df.shift(i).loc[:,['log_ret', 'volumefrom', 'volumeto']]

    df['trade_ratio{}'.format(i)] = df.apply(lambda x: x.prev_to/x.prev_from, axis = 1)
    df.drop(columns = ['prev_from', 'prev_to'])

df = df.dropna()

def calc_streak(df):
    streak = 1
    cols = [df.prev_ret1, df.prev_ret2, df.prev_ret3, df.prev_ret4]
    for i in range(1,4):
        test = cols[i-1] * cols[i] > 0
        if test == False:
            break
        else:
            streak += test
    return streak
df['streak'] = df.apply(calc_streak, axis = 1)        
X = df[['prev_ret1', 'prev2', 'prev3', 'prev4', 'prev5', 'diff', 'streak']]


X = sm.add_constant(X)
y = df['log_ret']
length = len(X)
fut_returns = []
for i in range(75,0,-1):
    rf = RandomForestRegressor(min_samples_leaf = 5, min_samples_split = 10, n_estimators = 200)
    x_train = X.iloc[:-i, :]
    y_train = y.iloc[:-i]
    x_test = X.iloc[length - i,:]
    rf.fit(x_train, y_train.values.ravel())
    
    fut_returns.append(rf.predict(x_test.values.reshape(1,-1)))

actual_returns = y.iloc[-75:]
mse = ((actual_returns -np.array(fut_returns).ravel())**2).sum()/100
ss = (actual_returns**2).sum()/100
print(mse/ss)
