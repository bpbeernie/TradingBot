import unittest
from unittest.mock import patch, Mock

import sys
sys.modules['gb'] = Mock()
from LODStrategy import LODBounceBot
from random import seed
from random import uniform
from random import randint
from Test.Data.MRKTestData import happyPath
from freezegun import freeze_time
from IBTest import IBTestClient
from IB import IBClient

@freeze_time("2022-03-31 6:31:34")
class TestLODHappyBot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = IBTestClient.IBTestApi(IBClient.IBApi())
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = LODBounceBot.LODBounceBot(ib, "MRK")

        cls.bot.setup()
        
        testBars = []
        
        for bar in happyPath:
            testBars.extend(cls.generateBars(*bar))
        
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
            
    def test_open_order(self):
        self.assertEqual(self.bot.executionTracker._longOrder._openOrder.lmtPrice, 82.58, "Open Value")
        self.assertEqual(self.bot.executionTracker._longOrder._openOrder.totalQuantity, 154, "Open Quantity")
            
    def test_profit_order(self):
        self.assertEqual(self.bot.executionTracker._longOrder._profitOrder.lmtPrice, 82.75, "Open Value")
            
    def test_stop_order(self):
        self.assertEqual(self.bot.executionTracker._longOrder._stopOrder.auxPrice, 82.45, "Open Value")
            
    def test_done(self):
        self.assertTrue(self.bot.done, "Bot is done")
        


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