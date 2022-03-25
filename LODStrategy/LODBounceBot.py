#Imports
from ibapi.contract import Contract
from Helpers import Bars as bars, Orders as orders
from Globals import Globals as gb
from LODStrategy import Constants as const
import logging
import os
import datetime
import pytz
import math
from Helpers.ATRBars import ATRBar

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/lod.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#Bot Logic
class LODBounceBot:
    ib = None
    barsize = 1
    bars = []
    reqId = 1
    startingBars = []
    openBar = None
    processedEndOfDay = False
    data = []
    
    tenMinLOD = None
    
    twentyFiveMinHOD = 0
    twentyMinLOD = 0
    symbol = None
    active = False
    done = False
    atrData = []
    
    def __init__(self, ib, stock):
        self.ib = ib
        self.symbol = stock

    def setup(self):
        self.log("Setting up LOD")
        self.ib.reqIds(-1)
        
        self.barsize = 1
        
        #Create our IB Contract Object
        contract = Contract()
        contract.symbol = self.symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        
        self.reqId = gb.Globals.orderId
        
        self.ib.reqRealTimeBars(self.reqId, contract, 5, "TRADES", 1, [])
        gb.Globals.getInstance().orderId += 1  
        
    def log(self, message, value=None):
        if value:
            logger.info(self.symbol + ": " + str(message) + " - " + str(value))
        else:
            logger.info(self.symbol + ": " + str(message))


    def on_bar_update(self, reqId, bar, realtime):
        return
    
    def convertMinsToBarInterval(self, min):
        return min*60/4/2
    
    def generateATR(self):
        # for each 1 min interval
        prevATRValue = 0
        i = 0
        
        while i < len(self.atrData):
            atrBar = self.atrData[i]
            
            if i == 0:
                prevClose = atrBar.open
            else:
                prevClose = self.atrData[i-1].close
            
            highLow = abs(atrBar.high - atrBar.low)
            highClose = abs(atrBar.high - prevClose)
            lowClose = abs(atrBar.low - prevClose)
            
            currATRValue = max(highLow, highClose, lowClose)
            
            if prevATRValue == 0:
                prevATRValue = currATRValue / 4
                
            prevATRValue = (prevATRValue *13 + currATRValue) / 14
            self.log("For minute " + str(i) + " we calculate atr value: ", prevATRValue)
            i += 1
            
        self.log("For minute " + str(i) + " we calculate atr value: ", prevATRValue)
        return round(prevATRValue, 2)

            

    #Pass realtime bar data back to our bot object
    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        self.check_time()
        
        if (self.done):
            return
        
        if (reqId != self.reqId):
            return
        
        bar = bars.Bar()
        bar.close = close
        bar.date = time
        bar.high = high
        bar.low = low
        bar.open = open_
        bar.volume = volume
        
        self.data.append(bar)
        intervalsPassed = len(self.data)
        
        if (intervalsPassed % 15 == 0):
            startingInterval = intervalsPassed - 15
            minArray = self.data[startingInterval:]
            atrBar = ATRBar()
            atrBar.high = min(o.high for o in minArray)
            atrBar.low = min(o.low for o in minArray)
            atrBar.open = minArray[0].open
            atrBar.close = minArray[-1].close
            self.atrData.append(atrBar)
            self.log(atrBar)
        
        # If 10 mins has passed
        if not self.tenMinLOD and intervalsPassed >= self.convertMinsToBarInterval(10):
            self.tenMinLOD = min(o.low for o in self.data)
            self.log("10 Min LOD", self.tenMinLOD)
            return
        
        # If there is a new low, stop all actions
        if self.tenMinLOD:
            if bar.low < self.tenMinLOD:
                self.done = True
                self.log("Price went below 10 min LOD, strategy is done!")
                return
        
        
        if intervalsPassed >= self.convertMinsToBarInterval(25):
            self.log("25 min interval hit!")
            
            atr = self.generateATR()
            atrFactor = 2
            trigger = max(round(1/3.25*atr*atrFactor,2), 0.02) + self.tenMinLOD
            openBid = (trigger-self.tenMinLOD) + trigger
            stopLoss = round(self.tenMinLOD-(trigger-self.tenMinLOD)*1.25, 2)
            quantity = math.ceil(const.CASHRISK / (openBid-stopLoss))
            
            target = (((openBid-stopLoss)*quantity*1+quantity*0.01*4)/quantity) + openBid
            
            self.log("ATR: ", atr)
            self.log("trigger: ", trigger)
            self.log("openBid: ", openBid)
            self.log("stopLoss: ", stopLoss)
            self.log("quantity: ", quantity)
            self.log("target: ", target)
            
            if not self.twentyFiveMinHOD:
                self.twentyFiveMinHOD = max(o.high for o in self.data)
                self.log("25 min HOD: ", self.twentyFiveMinHOD)
            
            # If hits triggered, trade is active
            if not self.active and bar.low <= trigger:
                self.active = True
                self.log("Now active!")
                return
            
            # If this has been triggered
            if (self.active):
                if bar.high >= openBid and self.twentyFiveMinHOD > target:
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "BUY", 
                                                                                 quantity, openBid, target, stopLoss)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)

                    self.update_globals_for_orders()
                    
                    self.done = True
                    
                    self.log("Buy " + self.symbol)


    def update_globals_for_orders(self):
        gb.Globals.getInstance().currentOrders[self.stock] = gb.Globals.getInstance().orderId
        gb.Globals.getInstance().orderId += 3       

    def check_time(self):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now > today9am:
            self.log("Processed 9 am")
            self.done = True