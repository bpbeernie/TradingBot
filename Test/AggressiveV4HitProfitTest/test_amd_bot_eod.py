import unittest
from unittest.mock import patch, Mock

import sys
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBotV4 import AggressiveAMDBotV4 as AMDBot
from random import seed
from random import uniform
from random import randint
from Test.Data.AMDTestData import *
from Globals import Globals as gb
from freezegun import freeze_time
import datetime
import pytz

@freeze_time("2022-04-05 9:21:34", tz_offset=-8)
class TestAMDBotEOD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        cls.bot = AMDBot(ib, "AMD")

        cls.bot.setup()
        
        testBars = []
        
        for bar in sadAndHappyPath:
            testBars.extend(cls.generateBars(*bar))
        
        for bar in testBars:
            cls.bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
            
    def test_processed_end_of_day_fail(self):
        print(datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific")))
        
        self.bot.check_end_of_day()
        
        self.assertFalse(self.bot.processedEndOfDay, "Not EOD yet")

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