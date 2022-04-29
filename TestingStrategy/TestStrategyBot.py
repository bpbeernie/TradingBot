from ibapi.contract import Contract
from Helpers import Bars as bars
from Globals import Globals as gb
import logging
import os
import datetime
import threading
import csv
from TestingStrategy import Constants as const

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
    analysisLock = threading.Lock()
    
    
    def __init__(self, ib, symbol):
        self.ib = ib
        self.symbol = symbol
        self.reqIdList = []
        self.processedReqIdList = []
        
        self.barsize = 1
        self.openBar = None
        self.entryLimitforShort = 0.0
        self.profitTargetForShort = 0.0
        self.stopLossForShort = 0.0
        self.entryLimitforLong = 0.0
        self.profitTargetForLong = 0.0
        self.stopLossForLong = 0.0
        self.data = {}
        
        self.dateCount = 0
        
        self.longEntryRunning = False
        self.longEntryDone = False
        self.shortEntryRunning = False
        self.shortEntryDone = False
        
        self.finalResults = {}

    def setup(self):
        self.contract = Contract()
        self.contract.symbol = self.symbol.upper()
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"
        self.contract.primaryExchange = "ARCA"
        
        for dateRange in const.DATE_RANGE:
            TestBot.lock.acquire()
            self.reqIdList = []
            self.processedReqIdList = []
            self.data = {}
            self.finalResults = {}
            
            self.folderName = dateRange[0]
            
            start_date = dateRange[1] + datetime.timedelta(days=1)
            end_date = dateRange[2]
        
            date_range = self.workdays(start_date, end_date)
            self.dateCount = len(date_range)
            
            print("Starting " + self.symbol)
            for single_date in date_range:
                queryTime = single_date.strftime("%Y%m%d %H:%M:%S")
                reqId = gb.Globals.getInstance().getOrderId()
                self.ib.reqHistoricalData(reqId, self.contract,queryTime,"1 D",str(self.barsize)+ " min","TRADES",1,1,False,[])
                self.reqIdList.append(reqId)


    def workdays(self, d, end, excluded=(6, 7)):
        days = []
        while d.date() <= end.date():
            if d.isoweekday() not in excluded and d not in const.HOLIDAYS:
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
        
    def proccessDate(self, dateToProcess):
        result = 0
        longEntryDone = False
        shortEntryDone = False
        longEntryRunning = False
        shortEntryRunning = False
        openBar = None
        data = self.data[dateToProcess]
        
        for newBar in data:                        
            if not openBar:
                openBar = newBar

                diff = openBar.high - openBar.low
                adjustedHigh = openBar.high + diff * 0.2
                adjustedLow = openBar.low - diff * 0.2
                adjustedDiff = adjustedHigh - adjustedLow
                
                entryLimitforLong = adjustedHigh
                profitTargetForLong = adjustedHigh + adjustedDiff * 3
                stopLossForLong = adjustedLow
                
                entryLimitforShort = adjustedLow
                profitTargetForShort = adjustedLow - adjustedDiff * 3
                stopLossForShort = adjustedHigh

            else:
                if longEntryDone and shortEntryDone:
                    return result
                
                if longEntryRunning and not longEntryDone:
                    if newBar.high > profitTargetForLong:
                        result += 3
                        return result
                    if newBar.low < stopLossForLong:
                        shortEntryRunning = True
                        longEntryDone = True
                        result -= 1
                        
                if shortEntryRunning and not shortEntryDone:
                    if newBar.low < profitTargetForShort:
                        result += 3
                        return result
                    
                    if newBar.high > stopLossForShort:
                        longEntryRunning = True
                        shortEntryDone = True
                        result -= 1
                
                if not longEntryRunning and not shortEntryRunning:
                    if newBar.high > entryLimitforLong:
                        longEntryRunning = True
                    
                    if newBar.low < entryLimitforShort:
                        shortEntryRunning = True
                        
        if shortEntryRunning and not shortEntryDone:
            remaining =  (entryLimitforShort - data[-1].close) / (entryLimitforShort - profitTargetForShort)
            result += remaining * 3
            
        if longEntryRunning and not longEntryDone:
            remaining = (data[-1].close - entryLimitforLong) /  (profitTargetForLong - entryLimitforLong)
            result += remaining * 3
            
        return result
        
        
    def historicalDataEnd(self,reqId):
        if reqId not in self.reqIdList:
            return
        
        self.processedReqIdList.append(reqId)
        
        if len(self.reqIdList) == len(self.processedReqIdList):
            for date in self.data.keys():
                result = self.proccessDate(date)
                self.finalResults.setdefault(datetime.datetime.strptime(date, '%Y-%m-%d'), result) 

            self.printFinalResults()
            print("Ending " + self.symbol)
            TestBot.lock.release()
        
    def printFinalResults(self):
        folder = const.OUTPUT_PATH + f'{self.folderName}/'
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        with open(folder + self.symbol + ".csv", 'w', encoding='UTF8', newline='') as f:
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
        

    def updateStatus(self, orderID, status):
        pass

    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        pass
