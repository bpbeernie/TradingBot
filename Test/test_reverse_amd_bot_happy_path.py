import unittest
from unittest.mock import patch, Mock

import sys
sys.modules['gb'] = Mock()
from AMDStrategy.ReverseAMDOpenBot import ReverseAMDBot
from random import seed
from random import uniform
from random import randint
from Test.Data.AMDReverseTestData import happyPath
from Globals import Globals as gb
from freezegun import freeze_time
import datetime
import pytz

@freeze_time("2022-04-08 6:31:34", tz_offset=-8)
class TestAMDReverseHappyBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = ReverseAMDBot(ib, "AAPL")

        cls.bot.setup()
        
        testBars = []
        
        for bar in happyPath:
            testBars.extend(cls.generateBars(*bar))
        
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
            
            if cls.bot.executionTracker.isShortOrderSent() and bar[2] < cls.bot.profitTargetForShort:
                cls.bot.updateStatus(cls.bot.executionTracker._shortOrder._profitOrder.orderId, "Filled")
        
        cls.bot.updateStatus(cls.bot.executionTracker._longOrder._profitOrder.orderId, "Filled")
        
    def test_on_openBar(self):
        self.assertEqual(self.bot.openBar.low, 167.44, "Low setup properly")
        self.assertEqual(self.bot.openBar.high, 168.08, "High setup properly")
        
    def test_entry_triggers_quantity(self):
        self.assertEqual(self.bot.quantity, 28, "Test Quantity")
        
    def test_entry_triggers_entries(self):
        self.assertEqual(round(self.bot.entryLimitForLong, 2), 167.31, "Entry for Long")
        self.assertEqual(round(self.bot.entryLimitForShort, 2), 168.21, "Entry for Short")
        
    def test_entry_triggers_profitTargets(self):
        self.assertEqual(round(self.bot.profitTargetForLong, 2), 168.21, "Profit for Long")
        self.assertEqual(round(self.bot.profitTargetForShort, 2), 167.31, "Profit for Short")
        
    def test_stopLoss(self):
        self.assertEqual(round(self.bot.stopLossForLong, 2), 166.42, "Stop Loss for Long")
        self.assertEqual(round(self.bot.stopLossForShort, 2), 169.1, "Stop Loss for Short")
        
    def test_check_global_orders(self):
        self.assertTrue("AAPL" in gb.Globals.getInstance().activeOrders.keys(), "Added to globals")
        
    def test_check_short_executed(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short has been executed")
        
    def test_check_long_executed(self):
        self.assertTrue(self.bot.executionTracker.isLongOrderSent(), "Long has been executed")

    def test_check_done(self):
        self.assertTrue(self.bot.done, "Bot is done")

    def test_count(self):
        self.assertEqual(2, self.bot.executionTracker._count, "Only 2 orders")

    @classmethod
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