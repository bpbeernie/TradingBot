import unittest
from unittest.mock import patch, Mock

import sys
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBot import AggressiveAMDBot
from pprint import pprint
from random import seed
from random import uniform

class TestAMDBot(unittest.TestCase):
    
    def test_on_realtime_update(self):
        requestID = 1
        ib = Mock()
        ib.reqRealTimeBars = Mock(return_value = 1)
        
        bot = AggressiveAMDBot(ib, "AAPL")
        self.assertEqual(bot.reqId, requestID, "Request ID Set Properly")
        
        bot.setup()
        
        
        testBars = self.generateBars(177.88, 178.02, 177.63, 177.64)
        testBars2 = self.generateBars(177.63, 177.75, 177.45, 177.74)
        
        for bar in testBars:
            bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
        
        for bar in testBars2:
            bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
        
        bot.on_realtime_update(requestID, None, bar[0], bar[1], bar[2], bar[3], None, None, None)
        
        pprint(bot.openBar)
        
        
    def generateBars(self, _open, high, low, _close):
        seed(1)
        newStart = _open
        returnList = []
        
        for i in range(12):
            newHigh = uniform(newStart, high)
            newClose = uniform(newStart, newHigh)
            newLow = uniform(low, newClose)
            
            if i == 11:
                returnList.append((newStart, newHigh, newLow, _close))
            else:
                returnList.append((newStart, newHigh, newLow, newClose))
            newStart = newClose
            
        return returnList
if __name__ == '__main__':
    unittest.main()