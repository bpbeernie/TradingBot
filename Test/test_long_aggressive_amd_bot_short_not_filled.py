import unittest
from unittest.mock import patch, Mock
import sys
from AMDStrategy.TrackerWrapper import TrackerWrapper
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBot import AggressiveAMDBot as AMDBot
from random import seed
from random import uniform
from random import randint
from Globals import Globals as gb
from freezegun import freeze_time
import datetime
import pytz
import pickle

@freeze_time("2022-05-22 6:31:34", tz_offset=-8)
class TestAggressiveAMDCancelBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = AMDBot(ib, "TWTR")

        cls.bot.setup()
        cls.tracker = TrackerWrapper(cls.bot.executionTracker)
        
        file_name = "Data/TWTR_2022-05-20.pkl"
        
        testBars = []
        
        with (open(file_name, "rb")) as openfile:
            while True:
                try:
                    testBars.extend(pickle.load(openfile))
                except EOFError:
                    break

        longOrderDone = False
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar["Open"], bar["High"], bar["Low"], bar["Close"], None, None, None)
            
            if cls.tracker.isLongOrderSent() and not cls.tracker.isLongOrderFilled():
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")
                
            if cls.tracker.isLongOrderFilled() and not longOrderDone:
                if bar["High"] >= cls.tracker.getLongStopPrice():
                    cls.bot.updateStatus(cls.tracker.getLongStopID(), "Filled")
                    longOrderDone = True
            
            

    def test_long_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderSent(), "Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderFilled(), "Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertFalse(self.bot.executionTracker.isShortOrderFilled(), "Short Order Filled")
        
    def test_done(self):
        self.assertTrue(self.bot.done, "Order is done")

    def test_count(self):
        self.assertEqual(2, self.bot.executionTracker._count, "Only 2 orders")

if __name__ == '__main__':
    unittest.main()