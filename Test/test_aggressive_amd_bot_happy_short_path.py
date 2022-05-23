import unittest
from unittest.mock import patch, Mock
import sys
from pickle import FALSE
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
        
        cls.bot = AMDBot(ib, "TWTR")

        cls.bot.setup()
        
        file_name = "Data/TWTR_2022-05-16.pkl"
        
        testBars = []
        
        with (open(file_name, "rb")) as openfile:
            while True:
                try:
                    testBars.extend(pickle.load(openfile))
                except EOFError:
                    break
                

        shortOrderDone = False

        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar["Open"], bar["High"], bar["Low"], bar["Close"], None, None, None)
        
            if cls.bot.executionTracker.isShortOrderSent() and not cls.bot.executionTracker.isShortOrderFilled():
                cls.bot.updateStatus(cls.bot.executionTracker._shortOrder._openOrder.orderId, "Filled")

            if cls.bot.executionTracker.isShortOrderFilled() and not shortOrderDone:
                if bar["Low"] <= cls.bot.executionTracker._shortOrder._profitOrder.lmtPrice:
                    cls.bot.updateStatus(cls.bot.executionTracker._shortOrder._profitOrder.orderId, "Filled")
                    shortOrderDone = True
            
            


    def test_long_order_sent(self):
        self.assertFalse(self.bot.executionTracker.isLongOrderSent(), "No Long Order Sent")
        
    def test_long_order_filled(self):
        self.assertFalse(self.bot.executionTracker.isLongOrderFilled(), "No Long Order Filled")
        
    def test_short_order_sent(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short Order Sent")
        
    def test_Short_order_filled(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderFilled(), "Short Order Filled")
        
    def test_done(self):
        self.assertTrue(self.bot.done, "done")


if __name__ == '__main__':
    unittest.main()