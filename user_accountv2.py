# -*- coding: utf-8 -*-
"""
Created on Sat Feb 17 16:53:12 2018

@author: pgood
"""

class User:
    
    def __init__(self, db, starting = 100000000.0):
        if db.new_account == 0:
            self.currency = db.db.cur.find_one({'currency' : {'$exists' : True}})['currency']
        else:
            self.currency = 'USDT'
        self.starting_cash = starting
        
    
    #For fungible shares, it doesn't make sense to allow for simultaneous short and long positions
    #This would also require two lines on the P/L, causing confusion
    def evalTransaction(self, tran_type, shares, price, ticker, db, pl, blotter):
       from datetime import datetime
       
       cash = pl.pl.loc['cash', 'market']
       total = shares * price
       
       try:
            prev_shares = pl.pl.loc[ticker, "position"]
            new = 0
       except KeyError:
            new = 1
            prev_shares = 0

       if tran_type in ["buy", "cover"]:
            #User abuse/misuse prevention
            margin = pl.check_margin()

            if tran_type == "cover" and prev_shares >= 0:
                self.message = "You do not have any short sales with this security"
            elif tran_type == "cover" and shares + prev_shares > 0:
                self.message = "You have attempted to cover {} shares.  Please cover {} shares or less"
                self.message = self.message.format(shares, -prev_shares)
                
            elif tran_type == "buy" and cash <= margin * 2 + shares * price:
                self.message = "This transaction requires ${:,.2f} in your account.  You have ${:,.2f}."
                self.message = self.message.format(margin * 2 + shares * price, cash)
                
            elif tran_type == "buy" and prev_shares < 0:
                self.message = "You currently have {} shares of {} shorted.  Please cover those before buying."
                self.message = self.message.format(shares, ticker)
            else:#Process transaction
                date = datetime.now ()
                trans = (cash - total,  ticker, -total, price, shares, tran_type)
                pl.eval_pl(tran_type, shares, price, ticker, total, db, new, prev_shares)
                blotter.eval_blotter(db, date, trans)
                self.message = "Success"
                
       else:
            if tran_type == "short":
                margin = pl.check_margin()
                                 
            if tran_type == "sell" and prev_shares < 0:
                self.message = "You have a short position in {0} of {1} shares".format(ticker, prev_shares*-1)
                
            elif tran_type == "sell" and prev_shares < shares:
                self.message= "You have {0} shares of {1} in you account.  Please choose a different quantity to sell"
                self.message = self.message.format(prev_shares, ticker)
                
            elif tran_type == "short" and prev_shares > 0:
                self.message = "You have a long position in {} of {} shares.  Please sell before shorting"
                self.message = self.message.format(ticker, prev_shares)
            elif tran_type == "short" and cash <= (margin * 2 + shares * price):
                self.message = "This transaction requires ${:,.2f} in your account.  You have ${:,.2f}."
                self.message = self.message.format(margin * 2 + shares * price, cash)
                
            else:#Process transaction
               date = datetime.now ()
               trans = (cash + total,  ticker, total, price, shares, tran_type)
               pl.eval_pl(tran_type, shares, price, ticker, total, db, new, prev_shares)
               blotter.eval_blotter(db, date, trans)
               self.message = "Success"
    
    def wipe_account(self, db, blotter, pl):
        import pandas as pd
        #reset db
        db.db.pl.delete_many({})
        db.db.blotter.delete_many({})
        db.db.cur.delete_many({})
        db.currency_update('usdt')
        
        #reset blotter
        blotter.blotter_rows = 0
        blotter.blotter = pd.DataFrame(columns = [ "cash_balance", "currency", "net", "price",
         "shares", "tran_type"])
    
        #reset pl
        start = {"cash": {"position": 0, "market": self.starting_cash, "wap" : 0.0, "rpl": 0.0, "upl": 0.0, "tpl": 0.0,
        "allocation_by_shares": 0.0, "allocation_by_dollars": 100.0}}
        pl.pl = pd.DataFrame.from_dict(start, orient = 'index')
        db.pl_insert(pl.pl, 'cash')
        
        #reset user
        self.currency = 'USDT'
        db.db.cur.insert_one({'currency' : 'USDT'})
        
    def change_currency(self, ticker, db):
        self.currency = ticker
        db.currency_update(ticker)

class Blotter:
    
    def __init__(self, user, db):
        import pandas as pd
        from datetime import datetime
        
        if db.new_account == 1:
            self.blotter_rows = 0
            self.blotter = pd.DataFrame(columns = [ "cash_balance", "currency", "net", "price",
                                 "shares", "tran_type"])
    
        else:
            self.blotter_rows = db.db.blotter.count()
            if self.blotter_rows > 0:
                #recreate blotter from last session
                blotter_list = []
                blotter_recs = db.db.blotter.find({})
                for rec in blotter_recs:
                    record_dict = {}
                    for key in rec.keys():
                        if key != '_id':
                            if key == 'date':
                                record_dict[key] = datetime.fromtimestamp(rec[key])
                            else:
                                record_dict[key] = rec[key]
                    blotter_list.append(record_dict)
                self.blotter = pd.DataFrame(blotter_list)
                self.blotter.set_index('date', inplace=True)

            else:#new blotter with no rows
                self.blotter = pd.DataFrame(columns = [ "cash_balance", "currency", "net", "price",
                                 "shares", "tran_type"])
                
    def showBlotter(self, user):
        from get_currency_info import get_current
             
        if self.blotter_rows > 0:
            if user.currency != 'USDT':
                cur = get_current(user.currency, 'check')
                mult = 1/cur
                #Going from dollars to the currency, intead of directly to from currency
                #to prevents the problem of certain currencies pairs not trading.
                #It also makes the program neater for such a minor difference, since this is
                #only for display purposes.
            else:
                mult = 1
            #prepare for display
            df = self.blotter.copy()
            df.loc[:, ['price', 'net', 'cash_balance']] *= mult
            df["price"] = df["price"].map('${:,.2f}'.format)
            df["net"] = df["net"].map('${:,.2f}'.format)
            df["cash_balance"] = df["cash_balance"].map('${:,.2f}'.format)
            dates = df.index
            df['Transaction Date'] = dates
            
            df = df[['Transaction Date', "currency", "price", "shares", "tran_type", "net", "cash_balance"]]
            to_string = lambda x: '{:,.8f}'.format(x).rstrip('0').rstrip('.')
            df['shares'] = df['shares'].map(to_string)
            labels = ["Transaction Date", "Currency", "Price", "Shares Traded", "Transaction Type",
                      "Net Cash Flow", "Cash Balance"]
            df.columns = labels
            self.blotter_view = df
            
    def eval_blotter(self, db, date, trans):
           self.blotter.loc[date] = trans
           db.blotter_insert(date, trans)
           self.blotter_rows += 1

            
class PL:
    
    def __init__(self, user, db):
        import pandas as pd
        
        if db.new_account == 1:
            start = {"cash": {"position": 0.0, "market": user.starting_cash, "wap" : 0.0, "rpl": 0.0, "upl": 0.0, 
                              "tpl": 0.0, "allocation_by_shares": 0.0, "allocation_by_dollars": 0.0}}
            self.pl = pd.DataFrame.from_dict(start, orient = 'index')
            db.pl_insert(self.pl, 'cash')
            
        else: #recreate pl from last session
            pl_recs = db.db.pl.find({})
            pl_dict = {}
            for rec in pl_recs:
                for key in rec.keys():
                    if key != '_id':
                        pl_dict[key] = rec[key]
            self.pl = pd.DataFrame.from_dict(pl_dict, orient = 'index')        
    
    def check_margin(self):
        from get_currency_info import get_current
        
        margin = 0
        for currency in self.pl.index:
            if self.pl.loc[currency, "position"] < 0:
                margin += self.pl.loc[currency, "position"] * get_current(currency, "buy") * -1
        return margin
    
    def eval_pl(self, tran_type, shares, price, ticker, total, db, new, prev_shares):
        #only certain columns that form the "base" data are calculated here.  
        #Columns like upl are only calculated when the user views the pl because 
        #those rely on market value.  This approach should be more efficient
        #in terms of performance and coding
        if tran_type in ('buy', 'cover'):
            self.pl.loc['cash', 'market'] -= total
            
            if new == 0:
                new_shares = prev_shares + shares
                
                if tran_type == "buy":
                    
                    if self.pl.loc[ticker, "position"] == 0:
                        self.pl.loc[ticker, "wap"] = price
            
                    else:
                        prev_value = prev_shares * self.pl.loc[ticker, "wap"]
                        self.pl.loc[ticker, "wap"] = (prev_value + shares * price)/new_shares
                        
                else:#Cover
                    gain = self.pl.loc[ticker, "wap"] * shares - total
                    self.pl.loc[ticker, "rpl"]  = self.pl.loc[ticker, "rpl"] + gain
                    
                #both    
                self.pl.loc[ticker, "position"] = new_shares
                if new_shares == 0:#for aesthetics in the P&L
                    self.pl.loc[ticker, "wap"] = 0
                db.pl_update(self.pl, ticker)
                db.pl_update(self.pl, 'cash')
                
            else:#new currencies
                self.pl.loc[ticker, ['position', 'market', 'wap', 'rpl', 'upl', 'tpl', 
                     'allocation_by_dollars', 'allocation_by_shares']] = (shares, 0, price, 0, 0, 0, 0, 0)
                db.pl_insert(self.pl, ticker)
                db.pl_update(self.pl, 'cash')
                
        else:#sell/short
           self.pl.loc['cash', 'market'] += total
           
           if new == 0:
               new_shares = self.pl.loc[ticker,'position'] - shares
               
               if tran_type == "sell":
                   gain = total -  self.pl.loc[ticker, 'wap'] * shares
                   self.pl.loc[ticker, 'rpl']  = self.pl.loc[ticker, "rpl"] + gain
                   
               else:#short

                   if self.pl.loc[ticker, 'position'] == 0:
                       self.pl.loc[ticker, "wap"] = price
                       
                   else:
                       prev_value = prev_shares * self.pl.loc[ticker, "wap"]*-1
                       self.pl.loc[ticker, "wap"] = (prev_value + shares * price)/new_shares*-1
               #both
               self.pl.loc[ticker, "position"] = new_shares
               if new_shares == 0:
                   self.pl.loc[ticker, "wap"] = 0   
                   
               db.pl_update(self.pl, ticker)
               db.pl_update(self.pl, 'cash')
               
           else:#new currencies
               self.pl.loc[ticker, ['position', 'market', 'wap', 'rpl', 'upl', 'tpl', 
                 'allocation_by_dollars', 'allocation_by_shares']] = (-shares, 0, price, 0, 0, -shares*price, 0, 0)
               db.pl_insert(self.pl, ticker)
               db.pl_update(self.pl, 'cash')



           
    def showPL(self, user):
        import numpy as np
        from get_currency_info import get_current
        

        #for showing PL in different currencies
        if user.currency != 'USDT':
            cur = get_current(user.currency, 'check')
            mult = 1/cur
        else:
            mult = 1
            
        final_df = self.pl.copy()[self.pl.index != 'cash']
        #create a dataframe from positions for easy calculated columns
        markets = []
        for position in final_df.index.values:
            market = get_current(position, 'check')
            markets.append(market)
        final_df["market"] = markets
        
        cash = self.pl.loc['cash', 'market'] * mult
        
        #additional columns calculated from "base" data
        final_df.loc[:, "total_value"] = final_df.position * final_df.market
        final_df.loc[:, 'share_weight'] =  abs(final_df.position)/np.sum(abs(final_df.position))
        final_df.loc[:, 'value_weight'] = abs(final_df['total_value'])/np.sum(abs(final_df['total_value']))
        final_df.loc[:, "upl"] = final_df.position * final_df.market - final_df.position * final_df.wap
        final_df.loc[:, 'tpl'] = final_df.upl + final_df.rpl     
        
        final_df.fillna(0)
        final_df.replace(np.nan, 0, inplace=True)
        
        currencies = final_df.index
        final_df['currency'] = currencies
        final_df = final_df[['currency', "position", "market", "total_value", 'value_weight', 'share_weight', 
                             "wap", "upl", 'rpl',  "tpl"]]
        
        final_df.loc[:, ['tpl', 'market', 'rpl', 'total_value', 'wap', 'upl']] *= mult
        #total row
        val = cash + np.sum(final_df["total_value"])
        totals = ['Total', '', '',  val,'', '', '', np.sum(final_df["upl"]), np.sum(final_df["rpl"]),
                  np.sum(final_df["tpl"])]
        #format total row
        for item in range(len(totals)):
            if type(totals[item]) is not str:
                totals[item] = "${:,.2f}".format(totals[item]) 
                
        totals = tuple(totals)
        cash_row = ("Cash", '', '', "${:,.2f}".format(cash),'', '',  '', '','', '')
        space_row = tuple(['' for i in range(len(final_df.columns))])
        
        #format currency rows
        for item in ["market", "total_value", "wap", "upl", "rpl", 'tpl']:
            final_df[item] = final_df[item].map('${:,.2f}'.format)
        for item in ['value_weight', 'share_weight']:
            final_df[item] = (final_df[item]*100).map('{:,.1f}%'.format)
        to_string = lambda x: '{:,.8f}'.format(x).rstrip('0').rstrip('.')
        final_df['position'] = final_df['position'].map(to_string)
            
        rows = len(final_df)
        
        final_df.loc[rows] = cash_row
        final_df.loc[rows + 1] = space_row
        final_df.loc[rows + 2] = totals
            
        cols = ['Currency', "Position", "Market Price", "Total Value", 'Value Weight', 'Share Weight',
                "WAP", "UPL", "RPL", 'Total PL']
        
        
        final_df.columns = cols
        self.pl_view = final_df

class UserDB:
    def __init__(self):
        from pymongo import MongoClient
        
        client = MongoClient('mongodb://cuny:data@ds153958.mlab.com:53958/currency-app', connectTimeoutMS = 50000)
        self.db = client.get_database('currency-app')
        
        if self.db.pl.count() > 0:
            self.new_account = 0
        else:
            self.new_account = 1
            self.db.cur.insert_one({'currency' : 'USDT'})
        
        
    def pl_insert(self, df, ticker):
        item = df.loc[ticker].to_dict()
        self.db.pl.insert_one({ticker: item})
        
    def pl_update(self, df, ticker):
        item = df.loc[ticker].to_dict()
        self.db.pl.update_one({ticker : {'$exists' : True}}, {'$set': {ticker : item}})
    
    def currency_update(self, currency):
        self.db.cur.update_one({'currency' : {'$exists' : True}}, {'$set': {'currency' : currency}})
        
    def blotter_insert(self, date, row):
         from datetime import datetime
         
         keys = [ "cash_balance", "currency", "net", "price",
                                 "shares", "tran_type", 'date']
         vals = list(row)
         since_date = datetime(1970, 1, 1, 0, 0, 0)
         seconds = (date - since_date).total_seconds()
         vals.append(seconds)
         doc = dict(zip(keys, vals))
         self.db.blotter.insert_one(doc)
        