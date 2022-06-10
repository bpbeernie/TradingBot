#Imports
from ibapi.contract import Contract
from Globals import Globals as gb
import logging
import os
import datetime
import pytz
from AMDStrategy import AMDExecutionTracker as tracker
import threading

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/open.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#Bot Logic
class OpenBotBase:
    processedEndOfDay = False
    lock = threading.Lock()
    
    def __init__(self, ib, symbol):
        self.ib = ib
        self.symbol = symbol
        self.reqId = gb.Globals.getInstance().getOrderId()
        self.startingBars = []
        self.barsize = 1
        self.openBar = None
        self.executionTracker = None
        self.quantity = 0
        self.entryLimitForShort = 0.0
        self.profitTargetForShort = 0.0
        self.stopLossForShort = 0.0
        self.entryLimitforLong = 0.0
        self.profitTargetForLong = 0.0
        self.stopLossForLong = 0.0
        self.timingCounter = 0
        self.done = False

    def setup(self):
        logger.info("Setting up open strategy for " + self.symbol)
        
        self.executionTracker = tracker.AMDExecutionTracker()

        #Create our IB Contract Object
        self.contract = Contract()
        self.contract.symbol = self.symbol.upper()
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"
        
        if self.contract.symbol == "META":
            self.contract.primaryExchange = "NASDAQ"
        else:
            self.contract.primaryExchange = "ARCA"

        # Request Market Data
        print("Start: " + self.symbol + str(self.reqId))
        self.ib.reqRealTimeBars(self.reqId, self.contract, 5, "TRADES", 1, [])

    def on_bar_update(self, reqId, bar, realtime):
        pass

    def updateStatus(self, orderID, status):
        pass
                    
    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        pass

    def update_globals_for_orders(self):
        gb.Globals.getInstance().activeOrders[self.symbol] = gb.Globals.getInstance().getOrderId(3)
    
    def check_end_of_day(self):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today1259pm = now.replace(hour=12, minute=59, second=30, microsecond=0)
        
        OpenBotBase.lock.acquire()
        if not OpenBotBase.processedEndOfDay and now > today1259pm:
            logger.info("Processed EOD")
            OpenBotBase.processedEndOfDay = True
            self.ib.reqGlobalCancel()
            self.ib.reqAccountUpdates(True, "1")
        OpenBotBase.lock.release()