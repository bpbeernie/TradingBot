import unittest
from unittest.mock import patch, Mock

import sys
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBot import AggressiveAMDBot
from random import seed
from random import uniform
from random import randint
from Test.TestData import *


class TestAMDBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = AggressiveAMDBot(ib, "AMD")

        cls.bot.setup()
        
        testBars = []
        
        for bar in sadAndHappyPath:
            testBars.extend(cls.generateBars(*bar))
        
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
            
    def test_on_openBar(self):
        self.assertEqual(self.bot.openBar.low, 110.43, "Low setup properly")
        self.assertEqual(self.bot.openBar.high, 110.96, "High setup properly")
        
    def test_entry_triggers_quantity(self):
        self.assertEqual(self.bot.quantity, 34, "Test Quantity")
        
    def test_entry_triggers_profitTargets(self):
        self.assertEqual(round(self.bot.profitTargetForLong, 2), 113.29, "Test Profit Target Long")
        self.assertEqual(round(self.bot.profitTargetForShort, 2), 108.1, "Test Profit Target Short")
        
    def test_entry_triggers_StopLosses(self):
        self.assertEqual(round(self.bot.stopLossForLong, 2), 110.32, "Test Stop Loss Long")
        self.assertEqual(round(self.bot.stopLossForShort, 2), 111.07, "Test Stop Loss Short")

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