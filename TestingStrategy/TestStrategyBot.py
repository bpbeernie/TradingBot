#Imports
from ibapi.contract import Contract
from Helpers import Bars as bars, Orders as orders
from Globals import Globals as gb
import logging
import os
import datetime
import pytz
import math
from AMDStrategy import AMDExecutionTracker as tracker
import threading
import sys
import csv

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/test.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#Bot Logic
class TestBot:
    lock = threading.Lock()
    
    def __init__(self, ib, symbol):
        self.ib = ib
        self.symbol = symbol
        self.reqIdList = []
        self.startingBars = []
        self.barsize = 1
        self.openBar = None
        self.targetPrice = 0
        self.executionTracker = None
        self.quantity = 0
        self.entryLimitforShort = 0.0
        self.profitTargetForShort = 0.0
        self.stopLossForShort = 0.0
        self.entryLimitforLong = 0.0
        self.profitTargetForLong = 0.0
        self.stopLossForLong = 0.0
        self.timingCounter = 0
        self.done = False
        self.data = {}
        
        self.dateCount = 0
        
        self.longEntryRunning = False
        self.longEntryDone = False
        self.shortEntryRunning = False
        self.shortEntryDone = False
        
        self.finalResults = {}

    def setup(self):
        self.executionTracker = tracker.AMDExecutionTracker()
        
        #Create our IB Contract Object
        self.contract = Contract()
        self.contract.symbol = self.symbol.upper()
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"
        self.contract.primaryExchange = "ARCA"

        # Request Historical Data
        start_date = datetime.datetime(2022, 3, 11)
        end_date = datetime.datetime.now() + datetime.timedelta(days=1)
        
        date_range = self.workdays(start_date, end_date)
        self.dateCount = len(date_range)
        
        TestBot.lock.acquire()
        print("Starting " + self.symbol)
        for single_date in date_range:
            queryTime = single_date.strftime("%Y%m%d %H:%M:%S")
            reqId = gb.Globals.getInstance().getOrderId()
            self.ib.reqHistoricalData(reqId, self.contract,queryTime,"1 D",str(self.barsize)+ " min","TRADES",1,1,False,[])
            self.reqIdList.append(reqId)


    def workdays(self, d, end, excluded=(6, 7)):
        days = []
        while d.date() <= end.date():
            if d.isoweekday() not in excluded:
                days.append(d)
            d += datetime.timedelta(days=1)
        return days

    def on_bar_update(self, reqId, bar, realtime):
        if reqId not in self.reqIdList:
            return
        
        date = datetime.datetime.strptime(bar.date, '%Y%m%d  %H:%M:%S')
        dateString = f'{date.year}-{date.month}-{date.day}'
        
        newBar = bars.Bar()
        newBar.open = bar.open
        newBar.close = bar.close
        newBar.high = bar.high
        newBar.low = bar.low
        
        self.data.setdefault(dateString, []).append(newBar) 
        
    def historicalDataEnd(self,reqId):
        if reqId not in self.reqIdList:
            return
        
        for date in self.data.keys():
            result = 0
            done = False
            
            for newBar in self.data[date]:
                    
                if not self.openBar:
                    self.initialize(newBar)
                else:
                    if self.longEntryDone and self.shortEntryDone:
                        done = True
                        break
                    
                    if self.longEntryRunning and not self.longEntryDone:
                        if newBar.high > self.profitTargetForLong:
                            #print("Long profit target hit")
                            result += 3
                            done = True
                            break
                        if newBar.low < self.stopLossForLong:
                            #print("Long stop loss hit")
                            self.shortEntryRunning = True
                            self.longEntryDone = True
                            #print("Starting Short entry")
                            result -= 1
                            
                    if self.shortEntryRunning and not self.shortEntryDone:
                        if newBar.low < self.profitTargetForShort:
                            #print("Short profit target hit")
                            result += 3
                            done = True
                            break
                        if newBar.high > self.stopLossForShort:
                            #print("Short stop loss hit")
                            self.longEntryRunning = True
                            self.shortEntryDone = True
                            #print("Starting long Entry")
                            result -= 1
                    
                    if not self.longEntryRunning and not self.shortEntryRunning:
                        if newBar.high > self.entryLimitforLong:
                            #print("Entered Long at: " + str(self.entryLimitforLong))
                            self.longEntryRunning = True
                        
                        if newBar.low < self.entryLimitforShort:
                            #print("Entered Short at: " + str(self.entryLimitforShort))
                            self.shortEntryRunning = True
            if not done:
                if self.shortEntryRunning and not self.shortEntryDone:
                    remaining =  (self.entryLimitforShort - self.data[date][-1].close) / (self.entryLimitforShort - self.profitTargetForShort)
                    result += remaining * 3
                    
                if self.longEntryRunning and not self.longEntryDone:
                    remaining = (self.data[date][-1].close - self.entryLimitforLong) /  (self.profitTargetForLong - self.entryLimitforLong)
                    result += remaining * 3
            
            self.finalResults.setdefault(datetime.datetime.strptime(date, '%Y-%m-%d'), result) 
            self.reset()
        if len(self.finalResults) == self.dateCount:
            self.printFinalResults()
            print("Ending " + self.symbol)
            TestBot.lock.release()
        
    def printFinalResults(self):
        with open('C:/Users/bpbee/Desktop/trading/BackTesting/' + self.symbol + ".csv", 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([None, "Win", "Lose"])
        
            keys = sorted(self.finalResults.keys())
            for key in keys:
                value = self.finalResults[key]
                date = key.strftime("%Y-%m-%d")
                if value < 0:
                    writer.writerow([date, None, abs(value)])
                else:
                    writer.writerow([date, abs(value), None])
        
        
    def reset(self):
        self.longEntryRunning = False
        self.longEntryDone = False
        self.shortEntryRunning = False
        self.shortEntryDone = False
        self.openBar = None
        
    def initialize(self, bar):
        self.openBar = bar

        diff = self.openBar.high - self.openBar.low
        adjustedHigh = self.openBar.high + diff * 0.2
        adjustedLow = self.openBar.low - diff * 0.2
        adjustedDiff = adjustedHigh - adjustedLow
        
        self.entryLimitforLong = adjustedHigh
        self.profitTargetForLong = adjustedHigh + adjustedDiff * 3
        self.stopLossForLong = adjustedLow
        
        self.entryLimitforShort = adjustedLow
        self.profitTargetForShort = adjustedLow - adjustedDiff * 3
        self.stopLossForShort = adjustedHigh

    def updateStatus(self, orderID, status):
        pass

    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        pass
