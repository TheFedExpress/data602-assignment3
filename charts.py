# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 19:33:24 2018

@author: pgood
"""

def tpl(df):
    df['upl'] = df.market*df.position - df.vwap*df.position
    df['tpl'] + df.upl + df.rpl

def graph_cols(df, tick, column, title):
    import pandas as pd
    from plotly.graph_objs import Scatter, Data, Line, Figure
    
    
    df = df[df['ticker'] == tick][column]
    dates = pd.to_datetime(df.index, format = '%Y%m%d%H%M%S%f')
    
    price = Scatter(x= dates, y = df, line = Line(width = 2, color = 'blue'), name = tick)
    layout = dict(title = title)
    
    data = Data([price])
    fig = Figure(data= data, layout = layout)
    
    return fig

def graph_tots(df, column, column_name):
    import pandas as pd
    from plotly.graph_objs import Scatter, Data, Line, Figure
    
    df = df[column]
    dates = pd.to_datetime(df.index, format = '%Y%m%d%H%M%S%f')
    
    price = Scatter(x= dates, y = df, line = Line(width = 2, color = 'blue'), name = column_name)
    layout = dict(title = column_name + ' History')
    
    data = Data([price])
    fig = Figure(data= data, layout = layout)
    
    return fig