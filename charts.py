# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 19:33:24 2018

@author: pgood
"""

def tpl(df):
    df['upl'] = df.market*df.position - df.vwap*df.position
    df['tpl'] + df.upl + df.rpl

def vwap(df, tick):
    import numpy as np
    import pandas as pd
    from plotly.graph_objs import Scatter, Data, Line
    
    
    df = df[df['crypto'] == tick]['wap']
    dates = pd.to_datetime(df.index, format = '%Y%m%d%H%M%S')
    
    price = Scatter(x= dates, y = df, line = Line(width = 2, color = 'blue'), name = tick)
    data = Data([price])
    return data
