import unittest
from unittest.mock import patch, Mock

import sys
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBotV3 import AggressiveAMDBotV3
from random import seed
from random import uniform
from random import randint
from Test.Data.AMDTestData import happyPath
from Globals import Globals as gb
from freezegun import freeze_time
import datetime
import pytz

@freeze_time("2022-04-08 6:31:34", tz_offset=-8)
class TestAMDHappyBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = AggressiveAMDBotV3(ib, "AAPL")

        cls.bot.setup()
        
        testBars = []
        
        for bar in happyPath:
            testBars.extend(cls.generateBars(*bar))
        
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
            
    def test_on_openBar(self):
        self.assertEqual(self.bot.openBar.low, 171.32, "Low setup properly")
        self.assertEqual(self.bot.openBar.high, 171.79, "High setup properly")
        
    def test_entry_triggers_quantity(self):
        self.assertEqual(self.bot.quantity, 64, "Test Quantity")
        
    def test_entry_triggers_entries(self):
        self.assertEqual(round(self.bot.entryLimitForLong, 2), 171.88, "Entry for Long")
        self.assertEqual(round(self.bot.entryLimitForShort, 2), 171.23, "Entry for Short")
        
    def test_entry_triggers_profitTargets(self):
        self.assertEqual(round(self.bot.profitTargetForShort, 2), 169.25, "Entry for Short")
        
    def test_check_global_orders(self):
        self.assertTrue("AAPL" in gb.Globals.getInstance().activeOrders.keys(), "Added to globals")
        


    def test_check_short_executed(self):
        self.assertTrue(self.bot.executionTracker.isShortOrderSent(), "Short has been executed")
        
        
    def test_count(self):
        self.assertEqual(1, self.bot.executionTracker._count, "Only 1 orders")

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