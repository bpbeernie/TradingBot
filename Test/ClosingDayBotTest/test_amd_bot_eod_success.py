import unittest
from unittest.mock import Mock

import sys
sys.modules['gb'] = Mock()
from AMDStrategy.ClosingDayBot import ClosingDayBot
from random import seed
from random import uniform
from random import randint
from Test.Data.AMDTestData import sadAndHappyPath
from freezegun import freeze_time

@freeze_time("2022-06-01 12:59:35")
class TestAMDBotEOD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = ClosingDayBot(ib)

        cls.bot.setup()
        
        testBars = []
        
        for bar in sadAndHappyPath:
            testBars.extend(cls.generateBars(*bar))
        
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
            
    def test_processed_end_of_day_success(self):        
        self.assertTrue(self.bot.processedEndOfDay, "Processed EOD")

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