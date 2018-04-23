# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 23:39:00 2018

@author: pgood
"""

from get_currency_info import get_history
from sklearn.kernel_ridge import KernelRidge
from sklearn import datasets, linear_model
import numpy as np
import matplotlib.pyplot as plt

df = get_history('btc', 389)
"""
ridge = KernelRidge(kernel = 'polynomial', gamma = 10, alpha = .1, degree = 3)
ridge.fit(np.arange(350).reshape(-1,1),df.loc[:349, 'close'].values.reshape(-1,1))

score = ridge.score(np.arange(350).reshape(-1,1),df.loc[:349, 'close'].values.reshape(-1,1))
print(score)
pred = ridge.predict(np.arange(390).reshape(-1,1))

all_pred = pred

plt.plot(df['time'], df['close'])

plt.plot(df['time'], all_pred, color = 'green')

plt.show()
"""

ridge = linear_model.LinearRegression()

for i in range(1,21):
    df[['prev_close{}'.format(i), 'prev_from', 'prev_to']] = df.shift(i).loc[:,['close', 'volumefrom', 'volumeto']]

    df['trade_ratio{}'.format(i)] = df.apply(lambda x: x.prev_to/x.prev_from, axis = 1)
    df.drop(columns = ['prev_from', 'prev_to'])
df.drop(columns = ['prev_from', 'prev_to'])
df = df.dropna()
X = df.iloc[:, 7:]
y = df['close']
ridge.fit(X.loc[:349],df.loc[:349, 'close'].values.reshape(-1,1))
for idx, col_name in enumerate(X.columns):
    print("The coefficient for {} is {}".format(col_name, ridge.coef_[0][idx]))
score = ridge.score(X.loc[:349],df.loc[:349, 'close'].values.reshape(-1,1))
print(score)
pred = ridge.predict(X)

all_pred = pred

plt.plot(df['time'], df['close'])

plt.plot(df['time'], all_pred, color = 'green')

plt.show()
