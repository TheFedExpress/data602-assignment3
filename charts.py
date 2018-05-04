# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 19:33:24 2018

@author: pgood
"""

def tpl(df):
    df['upl'] = df.market*df.position - df.vwap*df.position
    df['tpl'] + df.upl + df.rpl

def graph_cols(df, tick, column):
    import pandas as pd
    from plotly.graph_objs import Scatter, Data, Line
    
    
    df = df[df['ticker'] == tick][column]
    dates = pd.to_datetime(df.index, format = '%Y%m%d%H%M%S%f')
    
    price = Scatter(x= dates, y = df, line = Line(width = 2, color = 'blue'), name = tick)
    data = Data([price])
    return data

def graph_tots(df, column, title):
    import pandas as pd
    from plotly.graph_objs import Scatter, Data, Line
    
    df = df[column]
    dates = pd.to_datetime(df.index, format = '%Y%m%d%H%M%S%f')
    
    price = Scatter(x= dates, y = df, line = Line(width = 2, color = 'blue'), name = title)
    data = Data([price])
    return data