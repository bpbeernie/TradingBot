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

@freeze_time("2022-06-30 12:59:00")
class TestAMDBotEOD(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        requestID = 1
        cls.ib = IBWrapper()
        
        cls.bot = AMDBot(cls.ib, "GM")

        cls.bot.setup()
        cls.tracker = TrackerWrapper(cls.bot.executionTracker)
        
        file_name = "../Data/GM_2022-06-30.pkl"
        
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

            if cls.tracker.isLongOrderSent() and not self.tracker.isLongOrderFilled():
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")
                cls.longOpenID = cls.tracker.getLongOpenOrderID()
                
            if cls.tracker.isLongOrderFilled() and not longDone:
                if bar.high >= cls.tracker.getLongProfitTarget():
                    cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                    longDone = True
                    cls.longOrderEndPrice = cls.tracker.getLongProfitTarget()

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
                    
            cls.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)
            
                    
    def test_long_order_sent(self):
        self.assertFalse(self.bot.executionTracker.isLongOrderSent(), "Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertFalse(self.bot.executionTracker.isLongOrderFilled(), "Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "No Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderFilled(), "No Short Order Filled")    
        
    def test_short_quantity(self):
        self.assertEqual(self.bot.quantity, 201, "Quantity is correct")
        
    def test_short_profit_target(self):
        self.assertEqual(self.bot.profitTargetForShort, 31.93, "Profit target is correct")
         
    def test_short_entry(self):
        self.assertAlmostEqual(self.bot.entryLimitForShort, 32.56,  msg="Profit entry is correct", delta=0.1)
          
    def test_amount_bid(self):
        totalbid = self.bot.quantity*(self.bot.entryLimitForShort - self.bot.profitTargetForShort)
        self.assertAlmostEqual(totalbid, 126.53, msg="Amount purchased is corrects", delta=0.11)

class IBWrapper(IBClient.IBApi):
    def __init__(self):
        IBClient.IBApi.closedPositions = []
        self.orderList = []

    def reqRealTimeBars(self, reqId, contract, barSize,
                        whatToShow, useRTH,
                        realTimeBarsOptions):
        pass

    def placeOrder(self, orderId, contract, order):
        self.orderList.append((orderId, contract, order))
    
    def reqGlobalCancel(self):
        pass
    
    def reqAccountUpdates(self, first, second):
        pass

if __name__ == '__main__':
    unittest.main()