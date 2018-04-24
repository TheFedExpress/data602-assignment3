# -*- coding: utf-8 -*-
"""
Created on Mon Apr 23 16:55:44 2018

@author: peter_goodridge
"""

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
import statsmodels.api as sm

df = get_history('ltc', 2000)
rows = len(df) - 50
df = df.loc[df['volumefrom'] > 0]




ridge = linear_model.LinearRegression()

df.loc[:, 'log_ret'] = np.log(df.close) - np.log(df.close.shift(1))



for i in range(1,2):
    df[['prev_ret{}'.format(i), 'prev_from', 'prev_to']] = df.shift(i).loc[:,['log_ret', 'volumefrom', 'volumeto']]

    df['trade_ratio{}'.format(i)] = df.apply(lambda x: x.prev_to/x.prev_from, axis = 1)
    df.drop(columns = ['prev_from', 'prev_to'])



df = df.dropna()
X = df.iloc[:, 8:]
X = X[['prev_ret1', 'trade_ratio1']]
X = sm.add_constant(X)
y = df['log_ret']
#ridge.fit(X.loc[:rows - 50],df.loc[:rows - 50, 'log_ret'].values.reshape(-1,1))
result = sm.OLS(y,X).fit()
print(result.summary())
"""
for idx, col_name in enumerate(X.columns):
    print("The coefficient for {} is {}".format(col_name, ridge.coef_[0][idx]))
score = ridge.score(X.loc[:rows - 50],df.loc[:rows - 50, 'close'].values.reshape(-1,1))
print(score)
pred = ridge.predict(X)

all_pred = pred
"""