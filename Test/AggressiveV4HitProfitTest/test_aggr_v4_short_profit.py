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

class TestLongProfit(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        with freeze_time("2022-08-09 13:30:00") as frozen_datetime:
                
            requestID = 1
            cls.ib = IBWrapper()
            
            cls.bot = AMDBot(cls.ib, "AMD")
    
            cls.bot.setup()
            cls.tracker = TrackerWrapper(cls.bot.executionTracker)
            
            file_name = "../Data/AMD_2022-08-09.pkl"
            
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
                        print("Long profit hit but not filled")
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
                        print("Short profit hit not filled")
                        shortDone = True
                    elif bar.high >= cls.tracker.getShortStopPrice():
                        cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                        
                cls.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)

                    
    def test_long_order_sent(self):
        self.assertFalse(self.bot.executionTracker.isLongOrderSent(), "Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertFalse(self.bot.executionTracker.isLongOrderFilled(), "Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderFilled(), "Short Order Filled")    
        
    def test_done(self):
        self.assertTrue(self.bot.done, "Is Done")

    def test_stock_closed(self):
        self.assertIn("AMD", self.ib.stocksClosed, "AMD is set as a stock to close")

    def test_stock_to_close(self):
        self.assertNotIn("AMD", self.ib._stocksToClose, "AMD is set as a stock to close")

    def test_long_stop_hit(self):
        self.assertFalse(self.tracker.isLongStopHit())
        
    def test_short_stop_hit(self):
        self.assertFalse(self.tracker.isShortStopHit())
        
    def test_long_profit_hit(self):
        self.assertFalse(self.tracker.isLongProfitHit())
        
    def test_short_profit_hit(self):
        self.assertTrue(self.tracker.isShortProfitHit())

@freeze_time("2022-08-09 9:16:00", tz_offset=-8)
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
        contract = Contract()
        contract.symbol = "AMD"
        
        self.updatePortfolio(contract, 323, 32, 32, 32, 32, "", "")
        self.updatePortfolio(contract, 323, 32, 32, 32, 32, "", "")
        self.updatePortfolio(contract, 323, 32, 32, 32, 32, "", "")
        self.updatePortfolio(contract, 323, 32, 32, 32, 32, "", "")
    
    def reqPositions(self):
        pass

    def cancelOrder(self, orderId):
        print(f"Cancelling order: {orderId}")
        pass

if __name__ == '__main__':
    unittest.main()