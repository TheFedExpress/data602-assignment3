# -*- coding: utf-8 -*-
"""
Created on Sun Apr 22 17:57:00 2018

@author: pgood
"""

from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.stattools import adfuller
from get_currency_info import get_history, get_sd
from sklearn.kernel_ridge import KernelRidge
from sklearn import datasets, linear_model
import numpy as np
import matplotlib.pyplot as plt

df = get_sd('btc', 1000)
df.loc[:, 'log_ret'] = np.log(df.close) - np.log(df.close.shift(1))
returns = df.loc[:338, ['time', 'log_ret']]
returns.set_index('time', inplace = True)
returns.dropna(inplace = True)
returns['log_ret'] = returns['log_ret'].diff()

returns.dropna(inplace = True)

print(adfuller(returns.log_ret.values, maxlag = 10))
returns.plot()

"""
plot_acf(returns, lags = 60, alpha = .02)
plot_pacf(returns, lags = 60, alpha = .02)
"""

returns = df[['time', 'log_ret']]
returns.set_index('time', inplace = True)
returns.dropna(inplace = True)


mod = ARIMA(returns, order = (5,2,1))
res = mod.fit()
print(res.summary())


fut_returns = res.forecast(50)[0]

pred = np.zeros(50)
last = df.iloc[len(df) - 51, 1]

for i in range(len(fut_returns)):
    if i == 0:
        pred[i] = last * (1 + fut_returns[i])
    else:
        pred[i] = pred[i-1]* (1 + fut_returns[i])

all_points = np.concatenate((df.close.values.reshape(-1,1)[:-50], pred.reshape(-1,1)), axis = 0)

plt.subplot(2,1,1)
plt.plot(np.arange(len(all_points)), all_points)
plt.subplot(2,1,2)
df['close'].plot()
plt.show()