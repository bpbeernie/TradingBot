import unittest
from unittest.mock import patch, Mock
import sys
from pickle import FALSE
from AMDStrategy.TrackerWrapper import TrackerWrapper
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBotV2 import AggressiveAMDBotV2 as AMDBot
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
        
        cls.bot = AMDBot(ib, "GM")

        cls.bot.setup()
        cls.tracker = TrackerWrapper(cls.bot.executionTracker)
        file_name = "../Data/GM_2022-05-31.pkl"
        
        testBars = []
        
        with (open(file_name, "rb")) as openfile:
            while True:
                try:
                    testBars.extend(pickle.load(openfile))
                except EOFError:
                    break
                
        longDone = False
        shortDone = False
        
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)
        
            if cls.tracker.isLongOrderSent() and not cls.tracker.isLongOrderFilled():
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")

            if cls.tracker.isLongOrderFilled() and not longDone:
                if bar.high >= cls.tracker.getLongProfitTarget():
                    cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
                    longDone = True

            if cls.tracker.isShortOrderSent() and not cls.tracker.isShortOrderFilled():
                cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")

            if cls.tracker.isShortOrderFilled() and not shortDone:
                if bar.low <= cls.tracker.getShortProfitTarget():
                    cls.bot.updateStatus(cls.tracker.getShortProfitID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getShortProfitID(), "Filled")
                    longDone = True
                    
        print(f'Open Price: {cls.tracker.getShortOpenOrderPrice()}')
        print(f'Quantity: {cls.bot.quantity}')

    def test_long_order_sent(self):
        self.assertFalse(self.bot.executionTracker.isLongOrderSent(), "Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertFalse(self.bot.executionTracker.isLongOrderFilled(), "Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderFilled(), "Short Order Filled")
        
    def test_done(self):
        self.assertTrue(self.bot.done, "done")

    def test_count(self):
        self.assertEqual(1, self.tracker.getCount(), "Only 2 orders")

if __name__ == '__main__':
    unittest.main()