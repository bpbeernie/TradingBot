import unittest
from unittest.mock import patch, Mock
import sys
from pickle import FALSE
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
class TestAggressiveAMDHappyLongBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = AMDBot(ib, "AMD")

        cls.bot.setup()
        cls.tracker = TrackerWrapper(cls.bot.executionTracker)
        file_name = "Data/AMD_2022-05-13.pkl"
        
        testBars = []
        
        with (open(file_name, "rb")) as openfile:
            while True:
                try:
                    testBars.extend(pickle.load(openfile))
                except EOFError:
                    break
                
        longDone = False
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar["Open"], bar["High"], bar["Low"], bar["Close"], None, None, None)
        
            if cls.tracker.isLongOrderSent() and not cls.tracker.isLongOrderFilled():
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")

            if cls.tracker.isLongOrderFilled() and not longDone:
                if bar["High"] >= cls.tracker.getLongProfitTarget():
                    cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                    longDone = True

    def test_long_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderSent(), "Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderFilled(), "Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertFalse(self.bot.executionTracker.isShortOrderSent(), "No Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertFalse(self.bot.executionTracker.isShortOrderFilled(), "No Short Order Filled")
        
    def test_done(self):
        self.assertTrue(self.bot.done, "done")


if __name__ == '__main__':
    unittest.main()