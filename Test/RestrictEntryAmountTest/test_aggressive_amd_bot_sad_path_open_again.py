import unittest
from unittest.mock import patch, Mock
import sys
from pickle import FALSE
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBotV3 import AggressiveAMDBotV3 as AMDBot
from random import seed
from random import uniform
from random import randint
from Globals import Globals as gb
from freezegun import freeze_time
import datetime
import pytz
import pickle

@freeze_time("2021-10-15 6:31:34", tz_offset=-8)
class TestAggressiveAMDCancelBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = AMDBot(ib, "TWTR")

        cls.bot.setup()
        
        file_name = "../Data/TWTR_2021-10-15.pkl"
        
        testBars = []
        
        with (open(file_name, "rb")) as openfile:
            while True:
                try:
                    testBars.extend(pickle.load(openfile))
                except EOFError:
                    break
                

        longOrderDone = False
        shortOrderDone = False

        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)
        
            if cls.bot.executionTracker.isShortOrderSent() and not cls.bot.executionTracker.isShortOrderFilled():
                cls.bot.updateStatus(cls.bot.executionTracker._shortOrder._openOrder.orderId, "Filled")

            if cls.bot.executionTracker.isShortOrderFilled() and not shortOrderDone:
                if bar.high >= cls.bot.executionTracker._shortOrder._stopOrder.auxPrice:
                    cls.bot.updateStatus(cls.bot.executionTracker._shortOrder._stopOrder.orderId, "Filled")
                    shortOrderDone = True
            
            if not longOrderDone and cls.bot.executionTracker.isLongOrderSent() and not cls.bot.executionTracker.isLongOrderFilled():
                cls.bot.updateStatus(cls.bot.executionTracker._longOrder._openOrder.orderId, "Filled")
            
            if cls.bot.executionTracker.isLongOrderFilled() and not longOrderDone:
                if cls.bot.executionTracker._longOrder._stopOrder.auxPrice >= bar.low:
                    cls.bot.updateStatus(cls.bot.executionTracker._longOrder._stopOrder.orderId, "Filled")
                    longOrderDone = True
            


    def test_long_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderSent(), "Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderFilled(), "Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderFilled(), "Short Order Filled")

    def test_count(self):
        self.assertEqual(2, self.bot.executionTracker._count, "Only 2 orders")

if __name__ == '__main__':
    unittest.main()