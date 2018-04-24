# -*- coding: utf-8 -*-
"""
Created on Sun Apr 22 17:57:00 2018

@author: pgood
"""

from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import statsmodels.api as sm
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.stattools import adfuller
from get_currency_info import get_history
from sklearn.kernel_ridge import KernelRidge
from sklearn import datasets, linear_model
import numpy as np
import matplotlib.pyplot as plt
import time

returns = get_history('btc', 2000)

returns = returns[['close', 'time']]



#df.loc[:, 'log_ret'] = np.log(df.close) - np.log(df.close.shift(1))
#returns = df.loc[:338, ['time', 'log_ret']]
returns.set_index('time', inplace = True)
returns.dropna(inplace = True)
#returns['close'] = returns['close'].diff()

returns.dropna(inplace = True)

print(adfuller(returns.close)[1])


#plot_acf(returns, lags = 60, alpha = .02)
#plot_pacf(returns, lags = 60, alpha = .02)


mod = ARIMA(returns, order = (1,1,1))
res = mod.fit()


print(res.summary())


fut_returns = res.forecast(50)[0]



all_points = np.concatenate((returns.close.values.reshape(-1,1)[:], fut_returns.reshape(-1,1)), axis = 0)

plt.subplot(2,1,1)
plt.plot(np.arange(len(all_points)), all_points)
plt.subplot(2,1,2)
returns['close'].plot()
plt.show()
