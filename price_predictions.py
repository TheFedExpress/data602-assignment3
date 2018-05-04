# -*- coding: utf-8 -*-
"""
Created on Sun Apr 22 17:57:00 2018
@author: pgood
"""
import time

def prepare_returns(ticker):
    import numpy as np
    from get_currency_info import get_history
    
    df = get_history(ticker, 2000)
    df.loc[:, 'log_ret'] = np.log(df.close) - np.log(df.close.shift(1))
    df = df.loc['01-01-2016':]
    df.dropna(inplace = True)
    #returns['log_ret'] = returns['log_ret'].diff()

    return df

def garch_predict(ticker):

    from arch import arch_model
    from get_currency_info import get_current
    
    returns = prepare_returns(ticker)['log_ret']
        
    am = arch_model(returns, p=1, o=0, q=1, dist='StudentsT')
    res = am.fit(update_freq=5, disp='off')
    
    change = res.forecast(horizon=1).mean.iloc[-1,0]
    
    forecast = get_current(ticker, 'check')*(1 + change)
    return '${:,.2f}'.format(forecast)

def forest_predict(prim_ticker):
    from get_currency_info import get_current
    import numpy as np
    from sklearn.ensemble import RandomForestRegressor
    
    if prim_ticker == 'BTC':
        sec_ticker = 'ETH'
    else:
        sec_ticker = 'BTC'
    prim = prepare_returns(prim_ticker)[['close']]
    sec = prepare_returns(sec_ticker)[['close']]
    
#    prim = sm.add_constant(eth)
#   result = sm.OLS(sec,prim).fit()
    
#    b = result.params[1]
#    adf_stats = adfuller(btc['close'] - b*eth['close'])
#    print("The p-value for the ADF test is ", adf_stats[1])
    
    df = prepare_returns(prim_ticker)
    
    df.loc[:, 'diff'] = prim - sec
    
    
    
    df.loc[:, 'log_ret'] = np.log(df.close) - np.log(df.close.shift(1))
    df.loc[:, 'log_ret2'] = np.log(df.close) - np.log(df.close.shift(2))
    df.loc[:, 'log_ret3'] = np.log(df.close) - np.log(df.close.shift(3))
    df.loc[:, 'log_ret4'] = np.log(df.close) - np.log(df.close.shift(4))
    df.loc[:, 'log_ret5'] = np.log(df.close) - np.log(df.close.shift(5))
    df[['prev2', 'prev3', 'prev4', 'prev5']] = df.shift(1).loc[:, ['log_ret2', 'log_ret3', 'log_ret4', 'log_ret5']]
    
    df.dropna(inplace = True)
    
    for i in range(1,5):
        df[['prev_ret{}'.format(i)]] = df.shift(i).loc[:,['log_ret']]
    
    df = df.dropna()
    
    #keeping function definintion here because it's not a "real" funciton
    #its only use is in the apply method
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
    
    y = df['log_ret']
    rf = RandomForestRegressor(min_samples_leaf = 5, min_samples_split = 10, n_estimators = 100)
    rf.fit(X, y.values.ravel())
        
    pred = rf.predict(X.iloc[-1:, :].values.reshape(1,-1))
    forecast = get_current(prim_ticker, 'check')*(1 + pred[0])
    return '${:,.2f}'.format(forecast)
then = time.time()
garch_predict('btc')
print (time.time() - then)