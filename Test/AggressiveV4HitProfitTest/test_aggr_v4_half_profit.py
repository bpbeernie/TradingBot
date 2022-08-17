import unittest
from unittest.mock import Mock
from IB import IBClient
import sys
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBotV4 import AggressiveAMDBotV4 as AMDBot
from freezegun import freeze_time
import datetime
import pickle
from AMDStrategy.TrackerWrapper import TrackerWrapper
from ibapi.contract import Contract

class TestHalfProfit(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        with freeze_time("2022-08-11 13:30:00") as frozen_datetime:
                
            requestID = 1
            cls.ib = IBWrapper()
            
            cls.bot = AMDBot(cls.ib, "NVDA")
    
            cls.bot.setup()
            cls.tracker = TrackerWrapper(cls.bot.executionTracker)
            
            file_name = "../Data/NVDA_2022-08-11.pkl"
            
            testBars = []
            
            with (open(file_name, "rb")) as openfile:
                while True:
                    try:
                        testBars.extend(pickle.load(openfile))
                    except EOFError:
                        break
            
            shortDone = False
            longDone = False
            
            for bar in testBars:
                frozen_datetime.tick(delta=datetime.timedelta(seconds=5))
                
                if cls.tracker.isLongOrderSent() and not cls.tracker.isLongOrderFilled():
                    cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")
                    cls.longOpenID = cls.tracker.getLongOpenOrderID()
                    
                if cls.tracker.isLongOrderFilled() and not longDone:
                    if bar.high >= cls.tracker.getLongProfitTarget():
                        cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                        longDone = True
                        cls.longOrderEndPrice = cls.tracker.getLongProfitTarget()
                    elif bar.low <= cls.tracker.getLongStopPrice():
                        cls.bot.updateStatus(cls.tracker.getLongStopID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getLongStopID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getLongStopID(), "Filled")
                    
    
                if cls.tracker.isShortOrderSent() and not cls.tracker.isShortOrderFilled():
                    cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                    cls.shortOpenID = cls.tracker.getShortOpenOrderID()
                    cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                    
                    
                if cls.tracker.isShortOrderFilled() and not shortDone:
                    if bar.low <= cls.tracker.getShortProfitTarget():
                        cls.bot.updateStatus(cls.tracker.getShortProfitID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getShortProfitID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getShortProfitID(), "Filled")
                        shortDone = True
                    elif bar.high >= cls.tracker.getShortStopPrice():
                        cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                        
                cls.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)

                    
    def test_long_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderSent(), "Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderFilled(), "Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderFilled(), "Short Order Filled")    
        
    def test_done(self):
        self.assertTrue(self.bot.done, "Is Done")

    def test_stock_closed(self):
        self.assertTrue(len(self.ib.stocksClosed)==0, "No stocks were closed")

    def test_stock_to_close(self):
        self.assertTrue(len(self.ib._stocksToClose)==0, "No stocks were closed")

    def test_long_stop_hit(self):
        self.assertFalse(self.tracker.isLongStopHit())
        
    def test_short_stop_hit(self):
        self.assertTrue(self.tracker.isShortStopHit())
        
    def test_long_profit_hit(self):
        self.assertTrue(self.tracker.isLongProfitHit())
        
    def test_short_profit_hit(self):
        self.assertFalse(self.tracker.isShortProfitHit())

@freeze_time("2022-08-11 12:59:35")
class IBWrapper(IBClient.IBApi):
    def __init__(self):
        IBClient.IBApi.closedPositions = []
        self._stocksToClose = []
        self.orderList = []
        self.stocksClosed = []

    def reqRealTimeBars(self, reqId, contract, barSize,
                        whatToShow, useRTH,
                        realTimeBarsOptions):
        pass

    def placeOrder(self, orderId, contract, order):
        self.orderList.append((orderId, contract, order))
    
    def reqGlobalCancel(self):
        pass
    
    def reqAccountUpdates(self, first, second):
        print("Request account updates hit")
        self.stocksClosed = self._stocksToClose.copy()
    
    def reqPositions(self):
        pass

    def cancelOrder(self, orderId):
        print(f"Cancelling order: {orderId}")
        pass

if __name__ == '__main__':
    unittest.main()