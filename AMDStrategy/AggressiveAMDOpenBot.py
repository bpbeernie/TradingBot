#Imports
from ibapi.contract import Contract
from Helpers import Bars as bars, Orders as orders
from Globals import Globals as gb
import logging
import os
import datetime
import pytz
from AMDStrategy import Constants as const
import math
from AMDStrategy import AMDExecutionTracker as tracker

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/amd.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#Bot Logic
class AggressiveAMDBot:
    ib = None
    contract = None
    barsize = 1
    bars = []
    reqId = 1
    symbol = ""
    startingBars = []
    openBar = None
    processedEndOfDay = False
    targetPrice = 0
    executionTracker = None
    quantity = 0
    entryLimitforShort = 0.0
    profitTargetForShort = 0.0
    stopLossForShort = 0.0
    entryLimitforLong = 0.0
    profitTargetForLong = 0.0
    stopLossForLong = 0.0
    timingCounter = 0
    done = False
    
    def __init__(self, ib):
        self.ib = ib

    def setup(self):
        logger.info("Setting up Aggressive AMD")
        
        self.executionTracker = tracker.AMDExecutionTracker()
        self.ib.reqIds(-1)
        
        self.symbol = "AMD"
        self.barsize = 1
        
        #Create our IB Contract Object
        self.contract = Contract()
        self.contract.symbol = self.symbol.upper()
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"

        self.reqId = gb.Globals.orderId;
        
        # Request Market Data
        self.ib.reqRealTimeBars(self.reqId, self.contract, 5, "TRADES", 1, [])
        gb.Globals.getInstance().orderId += 1    

    def on_bar_update(self, reqId, bar, realtime):
        return



    def updateStatus(self, orderID, status):
        if self.executionTracker.isLongOrderExecuted() and self.executionTracker.isShortOrderExecuted():
            return
        
        if self.executionTracker.isLongOrderExecuted():
            if status == "Filled":
                if orderID == self.executionTracker._longOrder._stopOrder.orderId:
                    logger.info("AMD Stop order hit, creating response order.")
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId+3, "SELL", self.quantity, self.entryLimitforShort, self.profitTargetForShort, self.stopLossForShort)
                    
                    self.executionTracker.setShort(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                    
                    self.update_globals_for_orders()
                
                if orderID == self.executionTracker._longOrder._profitOrder.orderId:
                    logger.info("AMD long profit hit")
                    self.done = True
                    #gb.Globals.getInstance().activeOrders.pop(self.symbol)
                
        if self.executionTracker.isShortOrderExecuted():
            if status == "Filled": 
                if orderID == self.executionTracker._shortOrder._stopOrder.orderId:
                    logger.info("AMD Stop order hit, creating response order.")
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId+3, "BUY", self.quantity, self.entryLimitForLong, self.profitTargetForLong, self.stopLossForLong)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                
                    self.update_globals_for_orders()
                
                if orderID == self.executionTracker._shortOrder._profitOrder.orderId:
                    logger.info("AMD short profit hit")
                    self.done = True
                    #gb.Globals.getInstance().activeOrders.pop(self.symbol)
                    
    #Pass realtime bar data back to our bot object
    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        if self.done:
            return
        
        self.check_end_of_day()
        
        if (reqId != self.reqId):
            return
        
        if not self.startingBars or len(self.startingBars) < 12:
            bar = bars.Bar()
            bar.close = close
            bar.date = time
            bar.high = high
            bar.low = low
            bar.open = open_
            bar.volume = volume
            self.startingBars.append(bar)
            logger.info("Creating open bar")
        else:
            if self.openBar is None:
                self.openBar = bars.Bar()
                self.openBar.low = min(o.low for o in self.startingBars)
                self.openBar.high = max(o.high for o in self.startingBars)
                
                #If opening candle too small, artifically increment it.
                if (self.openBar.high - self.openBar.low < self.openBar.low * const.RISKMULTIPLIER * 3 ):
                    self.openBar.high = self.openBar.low + self.openBar.low * const.RISKMULTIPLIER * 3

            if self.executionTracker.isLongOrderExecuted() and self.executionTracker.isShortOrderExecuted():
                if self.timingCounter % 120 == 0:
                    logger.info("Both long and Short are done")
                self.timingCounter += 1
                return

            if self.symbol not in gb.Globals.getInstance().activeOrders:
                expectedHigh = self.openBar.high + self.openBar.high * const.RISKMULTIPLIER
                expectedLow = self.openBar.low - self.openBar.low * const.RISKMULTIPLIER
                logger.info("current high: {}".format( high))
                logger.info("expected high: {}".format(expectedHigh))
                logger.info("current low: {}".format(low))
                logger.info("expected low: {}".format(expectedLow))
                
                risk = expectedHigh - expectedLow
                self.quantity = math.ceil(const.CASHRISK / risk)
                
                self.entryLimitForLong = expectedHigh
                self.entryLimitforShort = expectedLow
                self.profitTargetForLong = expectedHigh + risk * 3
                self.profitTargetForShort = expectedLow - risk * 3
                self.stopLossForLong = expectedLow
                self.stopLossForShort = expectedHigh

            
                if high > expectedHigh and not self.executionTracker.isLongOrderExecuted():                    
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "BUY", self.quantity, self.entryLimitForLong, self.profitTargetForLong, self.stopLossForLong)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)

                    self.update_globals_for_orders()
                    
                    logger.info("Buy AMD")
                elif low < expectedLow and not self.executionTracker.isShortOrderExecuted():
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "SELL", self.quantity, self.entryLimitforShort, self.profitTargetForShort, self.stopLossForShort)
                    
                    self.executionTracker.setShort(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                    
                    self.update_globals_for_orders()
                    
                    logger.info("Short AMD")

    def update_globals_for_orders(self):
        gb.Globals.getInstance().activeOrders[self.symbol] = gb.Globals.getInstance().orderId
        gb.Globals.getInstance().orderId += 3       
    
    def check_end_of_day(self):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today1259pm = now.replace(hour=12, minute=59, second=30, microsecond=0)
        if not self.processedEndOfDay and now > today1259pm:
            logger.info("Processed EOD")
            self.processedEndOfDay = True
            self.ib.reqGlobalCancel()
            self.ib.reqAccountUpdates(True, "1")