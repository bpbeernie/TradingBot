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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/amd.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#Bot Logic
class AMDBot:
    ib = None
    contract = None
    barsize = 1
    bars = []
    reqId = 1
    symbol = ""
    startingBars = []
    openBar = None
    processedEndOfDay = False
    
    def __init__(self, ib):
        self.ib = ib

    def setup(self):
        logger.info("Setting up AMD")
        self.ib.reqIds(-1)
        
        self.symbol = "AMD"
        self.barsize = 1
        
        #Create our IB Contract Object
        self.contract = Contract()
        self.contract.symbol = self.symbol.upper()
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"
        self.ib.reqIds(-1)
        
        # Request Market Data
        self.ib.reqRealTimeBars(0, self.contract, 5, "TRADES", 1, [])

    def on_bar_update(self, reqId, bar, realtime):
        return

    #Pass realtime bar data back to our bot object
    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        self.check_end_of_day()
        
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
                if (self.openBar.high - self.openBar.low < self.openBar.low * const.RISKMULTIPLIER * 4 ):
                    self.openBar.high = self.openBar.low + self.openBar.low * const.RISKMULTIPLIER * 4

            if self.symbol not in gb.Globals.getInstance().currentOrders:
                expectedHigh = self.openBar.high + self.openBar.high * const.RISKMULTIPLIER
                expectedLow = self.openBar.low - self.openBar.low * const.RISKMULTIPLIER
                logger.info("current high: {}".format( high))
                logger.info("expected high: {}".format(expectedHigh))
                logger.info("current low: {}".format(low))
                logger.info("expected low: {}".format(expectedLow))
                
                risk = expectedHigh - expectedLow
                quantity = math.ceil(const.CASHRISK / risk)
                
                entryLimitForLong = expectedHigh
                entryLimitforShort = expectedLow
                profitTargetForLong = expectedHigh + risk * 3
                profitTargetForShort = expectedLow - risk * 3
                stopLossForLong = expectedLow
                stopLossForShort = expectedHigh

            
                if high > expectedHigh:                    
                    bracket = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "BUY", quantity, entryLimitForLong, profitTargetForLong, stopLossForLong)
                    
                    #Place Bracket Order
                    for o in bracket:
                        if (o.orderType == "STP"):
                            logger.info("The stoploss order is: {}".format(o.orderId))
                            
                            gb.Globals.getInstance().orderResponses[o.orderId] = {}
                            gb.Globals.getInstance().orderResponses[o.orderId]["orders"] = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId+3, "SELL", quantity, entryLimitforShort, profitTargetForShort, stopLossForShort)
                            gb.Globals.getInstance().orderResponses[o.orderId]["contract"] = self.contract
                            
                        self.ib.placeOrder(o.orderId, self.contract,o)
                    
                    self.update_globals_for_orders()
                    
                    logger.info("Buy AMD")
                elif low < expectedLow:
                    
                    bracket = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "SELL", quantity, entryLimitforShort, profitTargetForShort, stopLossForShort)
                    
                    #Place Bracket Order
                    for o in bracket:
                        if (o.orderType == "STP"):
                            logger.info("The stoploss order is: {}".format(o.orderId))
                            gb.Globals.getInstance().orderResponses[o.orderId] = {}
                            gb.Globals.getInstance().orderResponses[o.orderId]["orders"] = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId+3, "BUY", quantity, entryLimitForLong, profitTargetForLong, stopLossForLong)
                            gb.Globals.getInstance().orderResponses[o.orderId]["contract"] = self.contract
                            
                        self.ib.placeOrder(o.orderId, self.contract, o)
                        
                    self.update_globals_for_orders()
                    logger.info("Short AMD")

    def update_globals_for_orders(self):
        gb.Globals.getInstance().currentOrders["AMD"] = gb.Globals.getInstance().orderId
        gb.Globals.getInstance().orderId += 6       
    
    def check_end_of_day(self):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today1259pm = now.replace(hour=12, minute=59, second=30, microsecond=0)
        if not self.processedEndOfDay and now > today1259pm:
            logger.info("Processed EOD")
            self.ib.reqGlobalCancel()
            self.ib.reqAccountUpdates()
            self.processedEndOfDay = True