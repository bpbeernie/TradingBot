import unittest
from unittest.mock import patch, Mock

import sys
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBot import AggressiveAMDBot
from random import seed
from random import uniform
from random import randint
from Test.Data.AMDTestData import *
from Globals import Globals as gb
from freezegun import freeze_time
import datetime
import pytz
from Globals import Globals as gb


class TestAMDBotUpdateStatus(unittest.TestCase):
    def setUp(self):
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        self.bot = AggressiveAMDBot(ib, "AMD")

        self.bot.setup()
        self.requestID = self.bot.reqId
        
        self.testBars = []

        for bar in sadAndHappyPath:
            self.testBars.extend(self.generateBars(*bar))
                    
    def test_long_stop_hit(self):
        for bar in self.testBars[:60]:
            self.bot.on_realtime_update(self.requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
        
        self.assertTrue(self.bot.executionTracker.isLongOrderSent(), "Long order has been executed")
        self.assertFalse(self.bot.executionTracker.isShortOrderSent(), "Short order has not been executed yet")
        
        longOrderID = self.bot.executionTracker._longOrder._stopOrder.orderId
        self.bot.updateStatus(longOrderID, "Filled")
        
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short order has been executed")
        
    def test_short_profit_hit(self):     
        for bar in self.testBars[36:]:
            self.bot.on_realtime_update(self.requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)

        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short order has been executed")
        
        shortOrderID = self.bot.executionTracker._shortOrder._profitOrder.orderId
        print("short order ID: " + str(shortOrderID))
        self.bot.updateStatus(shortOrderID, "Filled")
        self.assertTrue(self.bot.done, "All trades done")
       
    def tearDown(self):
        gb.Globals.getInstance().activeOrders = {}

    def generateBars(self, _open, high, low, _close):
        seed(1)
        newStart = _open
        returnList = []
        
        highIndex = randint(1, 12)
        highLow = randint(1, 12)
        
        for i in range(12):
            newHigh = uniform(newStart, high)
            newClose = uniform(newStart, newHigh)
            newLow = uniform(low, newClose)
            
            if i == highIndex:
                newHigh = high
                
            if i == highLow:
                newLow = low
            
            if i == 11:
                returnList.append((newStart, newHigh, newLow, _close))
            else:
                returnList.append((newStart, newHigh, newLow, newClose))
            newStart = newClose
            
        return returnList
if __name__ == '__main__':
    unittest.main()