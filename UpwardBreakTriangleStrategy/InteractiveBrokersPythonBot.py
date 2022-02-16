#Imports
import ibapi
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from Helpers import Bars as bars, Orders as orders
from IB import IBClient as ibClient
import ta
import numpy as np
import pandas as pd
import pytz
import math
from datetime import datetime, timedelta
import threading
from Globals import Globals as gb

#Bot Logic
class Bot:
    ib = None
    barsize = 1
    currentBar = bars.Bar()
    bars = []
    reqId = 1
    smaPeriod = 50
    symbol = ""
    initialbartime = datetime.now().astimezone(pytz.timezone("America/New_York"))
    
    def __init__(self, ib):
        self.ib = ib

    def setup(self):
        self.currentBar = bars.Bar()
        self.ib.reqIds(-1)
        
        self.symbol = "AAPL"
        self.barsize = 1
        
        mintext = " min"
        if (int(self.barsize) > 1):
            mintext = " mins"
        queryTime = (datetime.now().astimezone(pytz.timezone("America/New_York"))-timedelta(days=1)).replace(hour=16,minute=0,second=0,microsecond=0).strftime("%Y%m%d %H:%M:%S")
        #Create our IB Contract Object
        contract = Contract()
        contract.symbol = self.symbol.upper()
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        self.ib.reqIds(-1)
        
        # Request Market Data
        self.ib.reqHistoricalData(self.reqId,contract,"","2 D",str(self.barsize)+mintext,"TRADES",1,1,True,[])

    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        return

    #Pass realtime bar data back to our bot object
    def on_bar_update(self, reqId, bar,realtime):
        #Historical Data to catch up
        if (realtime == False):
            self.bars.append(bar)
        else:
            bartime = datetime.strptime(bar.date,"%Y%m%d %H:%M:%S").astimezone(pytz.timezone("America/New_York"))
            minutes_diff = (bartime-self.initialbartime).total_seconds() / 60.0
            self.currentBar.date = bartime
            lastBar = self.bars[len(self.bars)-1]
            #On Bar Close
            if (minutes_diff > 0 and math.floor(minutes_diff) % self.barsize == 0):
                self.initialbartime = bartime
                #Entry - If we have a higher high, a higher low and we cross the 50 SMA Buy
                #1.) SMA
                closes = []
                for bar in self.bars:
                    closes.append(bar.close)
                self.close_array = pd.Series(np.asarray(closes))
                self.sma = ta.trend.sma_indicator(self.close_array,self.smaPeriod,True)
                print("SMA : " + str(self.sma[len(self.sma)-1]))
                #2.) Calculate Higher Highs and Lows
                lastLow = self.bars[len(self.bars)-1].low
                lastHigh = self.bars[len(self.bars)-1].high
                lastClose = self.bars[len(self.bars)-1].close

                # Check Criteria
                if (bar.close > lastHigh
                    and self.currentBar.low > lastLow
                    and bar.close > str(self.sma[len(self.sma)-1])
                    and lastClose < str(self.sma[len(self.sma)-2])):
                    #Bracket Order 2% Profit Target 1% Stop Loss
                    profitTarget = bar.close*1.02
                    stopLoss = bar.close*0.99
                    quantity = 1
                    bracket = orders.bracketOrder(self.symbol, gb.Globals.getInstance().orderId,"BUY",quantity, profitTarget, stopLoss)
                    contract = Contract()
                    contract.symbol = self.symbol.upper()
                    contract.secType = "STK"
                    contract.exchange = "SMART"
                    contract.currency = "USD"
                    #Place Bracket Order
                    for o in bracket:
                        o.ocaGroup = "OCA_"+str(gb.Globals.getInstance().orderId)
                        self.ib.placeOrder(o.orderId,contract,o)
                    gb.Globals.getInstance().orderId += 3
                #Bar closed append
                self.currentBar.close = bar.close
                print("New bar!")
                self.bars.append(self.currentBar)
                self.currentBar = bars.Bar()
                self.currentBar.open = bar.open
        #Build  realtime bar
        if (self.currentBar.open == 0):
            self.currentBar.open = bar.open
        if (self.currentBar.high == 0 or bar.high > self.currentBar.high):
            self.currentBar.high = bar.high
        if (self.currentBar.low == 0 or bar.low < self.currentBar.low):
            self.currentBar.low = bar.low