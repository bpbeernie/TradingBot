#Imports
from ibapi.contract import Contract
from Globals import Globals as gb
import logging
import os
import datetime
import pytz
from AMDStrategy import AMDExecutionTracker as tracker
import threading
from Mail import Email as email
from Globals import SpecialDates as specialdates

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
    processedEndOfDayBackup = False
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
        email.sendEmail(f"Started trading {self.symbol}", f"Trade has started!")
        
        self.executionTracker = tracker.AMDExecutionTracker()

        #Create our IB Contract Object
        self.contract = Contract()
        self.contract.symbol = self.symbol.upper()
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"
        
        if self.contract.symbol == "META":
            self.contract.primaryExchange = "NASDAQ"
        elif self.contract.symbol == "GM":
            self.contract.primaryExchange = "NYSE"
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
        if datetime.datetime.today().date() in specialdates.EARLY_DATES:
            self.check_end_of_day_early()
        else:
            self.check_end_of_day_normal()
        
    def check_end_of_day_normal(self):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today1259pm = now.replace(hour=12, minute=59, second=30, microsecond=0)
        
        OpenBotBase.lock.acquire()
        if not OpenBotBase.processedEndOfDay and now > today1259pm:
            logger.info("Processing EOD")
            OpenBotBase.processedEndOfDay = True
            self.ib.reqGlobalCancel()
            self.ib.reqAccountUpdates(True, "1")
            logger.info("Processed EOD")
        OpenBotBase.lock.release()
        
        today125945pm = now.replace(hour=12, minute=59, second=45, microsecond=0)
        OpenBotBase.lock.acquire()
        if OpenBotBase.processedEndOfDay and not OpenBotBase.processedEndOfDayBackup and now > today125945pm:
            logger.info("Processing EOD Backup")
            OpenBotBase.processedEndOfDayBackup = True
            self.ib.reqPositions()
            logger.info("Finished EOD Backup")
        OpenBotBase.lock.release()
        
    def check_end_of_day_early(self):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today0959pm = now.replace(hour=9, minute=59, second=30, microsecond=0)
        
        OpenBotBase.lock.acquire()
        if not OpenBotBase.processedEndOfDay and now > today0959pm:
            logger.info("Processing Early EOD")
            OpenBotBase.processedEndOfDay = True
            self.ib.reqGlobalCancel()
            self.ib.reqAccountUpdates(True, "1")
            logger.info("Processed Early EOD")
        OpenBotBase.lock.release()
        
        today095945pm = now.replace(hour=9, minute=59, second=45, microsecond=0)
        OpenBotBase.lock.acquire()
        if OpenBotBase.processedEndOfDay and not OpenBotBase.processedEndOfDayBackup and now > today095945pm:
            logger.info("Processing Early EOD Backup")
            OpenBotBase.processedEndOfDayBackup = True
            self.ib.reqPositions()
            logger.info("Finished Early EOD Backup")
        OpenBotBase.lock.release()