import unittest
from unittest.mock import patch, Mock
import sys
from pickle import FALSE
from AMDStrategy.TrackerWrapper import TrackerWrapper
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBotV4 import AggressiveAMDBotV4 as AMDBot
from random import seed
from random import uniform
from random import randint
from Globals import Globals as gb
from freezegun import freeze_time
import datetime
import pytz
import pickle

@freeze_time("2022-05-22 6:31:34", tz_offset=-8)
class TestAggressiveAMDCriticalFixBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = AMDBot(ib, "TWTR")

        cls.bot.setup()
        
        cls.tracker = TrackerWrapper(cls.bot.executionTracker)
        
        file_name = "../Data/TWTR_2022-05-23.pkl"
        
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
            cls.bot.on_realtime_update(requestID, None, bar["Open"], bar["High"], bar["Low"], bar["Close"], None, None, None)
        
            if cls.tracker.isShortOrderSent() and not cls.tracker.isShortOrderFilled():
                cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                cls.shortOrderID = cls.tracker.getShortOpenOrderID()
                cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                
            if cls.tracker.isShortOrderFilled() and not shortDone:
                if bar["High"] >= cls.tracker.getShortStopPrice():
                    cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                    cls.longOrderID = cls.tracker.getLongOpenOrderID()
                    cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getShortStopID(), "Filled")
                    shortDone = True
                    
            if cls.tracker.isLongOrderSent() and not cls.tracker.isLongOrderFilled():
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")
                cls.bot.updateStatus(cls.tracker.getLongOpenOrderID(), "Filled")

            if cls.tracker.isLongOrderFilled() and not longDone:
                if bar["Low"] <= cls.tracker.getLongStopPrice():
                    cls.bot.updateStatus(cls.tracker.getLongStopID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getLongStopID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getLongStopID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getLongStopID(), "Filled")
                    longDone = True


    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderFilled(), "Short Order Filled")

    def test_long_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderSent(), "Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderFilled(), "Long Order Filled")

    def test_Only_One_reverse_long(self):
        self.assertEqual(self.longOrderID, self.tracker.getLongOpenOrderID(), "Only 1 reverse order sent")

    def test_Only_One_reverse_stop(self):
        self.assertEqual(self.shortOrderID, self.tracker.getShortOpenOrderID(), "Only 1 short order made")

    def test_count(self):
        self.assertEqual(2, self.tracker.getCount(), "Only 2 orders")

if __name__ == '__main__':
    unittest.main()