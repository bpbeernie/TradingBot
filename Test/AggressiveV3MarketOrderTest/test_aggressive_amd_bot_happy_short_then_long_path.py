import unittest
from unittest.mock import patch, Mock
import sys
from pickle import FALSE
from AMDStrategy.TrackerWrapper import TrackerWrapper
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

@freeze_time("2022-05-22 6:31:34", tz_offset=-8)
class TestAggressiveAMDHappyLongBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = AMDBot(ib, "TWTR")

        cls.bot.setup()
        
        cls.tracker = TrackerWrapper(cls.bot.executionTracker)
        
        file_name = "../Data/TWTR_2022-05-17.pkl"
        
        testBars = []
        
        with (open(file_name, "rb")) as openfile:
            while True:
                try:
                    testBars.extend(pickle.load(openfile))
                except EOFError:
                    break
                

        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar["Open"], bar["High"], bar["Low"], bar["Close"], None, None, None)
        
            if cls.tracker.isShortOrderSent() and not cls.tracker.isShortOrderFilled():
                cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                
            if cls.tracker.isShortOrderFilled():
                if bar["High"] >= cls.tracker.getShortStopPrice():
                    cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
        
            if cls.tracker.isLongOrderSent() and not cls.tracker.isLongOrderFilled():
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")
            
            if cls.tracker.isLongOrderFilled():
                if bar["High"] >= cls.tracker.getLongProfitTarget():
                    cls.bot.updateStatus(cls.tracker.getLongProfitID(), "Filled")
            


    def test_long_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderSent(), "No Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderFilled(), "No Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderFilled(), "Short Order Filled")

    def test_count(self):
        self.assertEqual(2, self.bot.executionTracker._count, "Only 2 orders")

if __name__ == '__main__':
    unittest.main()