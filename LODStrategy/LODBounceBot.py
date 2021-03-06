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
from AMDStrategy import AMDExecutionTracker as tracker

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

    def __init__(self, ib, symbol):
        self.ib = ib
        self.symbol = symbol
        self.barsize = 1
        self.reqId = gb.Globals.getInstance().getOrderId()
        self.startingBars = []
        self.openBar = None
        self.processedEndOfDay = False
        self.data = []
    
        self.tenMinLOD = None
    
        self.twentyFiveMinHOD = 0
        self.twentyMinLOD = 0
        self.active = False
        self.done = False
        self.atrData = []
        self.executionTracker = tracker.AMDExecutionTracker()

    def setup(self):
        self.log("Setting up LOD")
        
        #Create our IB Contract Object
        self.contract = Contract()
        self.contract.symbol = self.symbol.upper()
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"
        self.contract.primaryExchange = "ARCA"
        
        self.ib.reqRealTimeBars(self.reqId, self.contract, 5, "TRADES", 1, [])
        
    def log(self, message, value=None):
        if value:
            logger.info(self.symbol + ": " + str(message) + " - " + str(value))
        else:
            logger.info(self.symbol + ": " + str(message))


    def updateStatus(self, orderID, status):
        pass
    
    def on_bar_update(self, reqId, bar, realtime):
        pass
    
    def convertMinsToBarInterval(self, specifiedMin):
        return specifiedMin*const.BARS_PER_MIN
    
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
            i += 1
            
        self.log("For minute " + str(i) + " we calculate atr value: ", prevATRValue)
        return round(prevATRValue, 2)


    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        if (self.done):
            return
        
        self.check_time()
        
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
        
        if (intervalsPassed % const.BARS_PER_MIN == 0):
            startingInterval = intervalsPassed - const.BARS_PER_MIN
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
            
            atr = self.generateATR()
            atrFactor = 2
            trigger = max(round(1/3.25*atr*atrFactor,2), 0.02) + self.tenMinLOD
            openBid = round((trigger-self.tenMinLOD) + trigger, 2)
            stopLoss = round(self.tenMinLOD-(trigger-self.tenMinLOD)*1.25, 2)
            quantity = math.ceil(const.CASHRISK / (openBid-stopLoss))
            
            target = round((((openBid-stopLoss)*quantity*1+quantity*0.01*4)/quantity) + openBid, 2)
            
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
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "BUY", 
                                                                                 quantity, openBid, target, stopLoss)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)

                    self.update_globals_for_orders()
                    
                    self.done = True
                    
                    self.log("Buy " + self.symbol)


    def update_globals_for_orders(self):
        gb.Globals.getInstance().activeOrders[self.symbol] = gb.Globals.getInstance().getOrderId()

    def check_time(self):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now > today9am:
            self.log("Processed 9 am")
            self.done = True