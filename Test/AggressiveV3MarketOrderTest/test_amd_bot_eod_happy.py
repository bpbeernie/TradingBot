import unittest
from unittest.mock import Mock
from IB import IBClient
import sys
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBotV3 import AggressiveAMDBotV3
from freezegun import freeze_time
import datetime
import pickle
from AMDStrategy.TrackerWrapper import TrackerWrapper

class TestAMDBotEOD(unittest.TestCase):
    def test_eod_happy(self):
        with freeze_time("2022-04-05 12:59:00") as frozen_datetime:
            requestID = 1
            self.ib = IBWrapper()
            
            self.bot = AggressiveAMDBotV3(self.ib, "META")
    
            self.bot.setup()
            self.tracker = TrackerWrapper(self.bot.executionTracker)
            
            file_name = "../Data/META_2022-06-10.pkl"
            
            testBars = []
            
            with (open(file_name, "rb")) as openfile:
                while True:
                    try:
                        testBars.extend(pickle.load(openfile))
                    except EOFError:
                        break
            
            shortDone = False
            for bar in testBars[:-6]:
                self.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)
            
                if self.tracker.isShortOrderSent() and not self.tracker.isShortOrderFilled():
                    self.bot.updateStatus(self.tracker.getShortOpenOrderID(), "Filled")
                    self.shortOpenID = self.tracker.getShortOpenOrderID()
                    self.bot.updateStatus(self.tracker.getShortOpenOrderID(), "Filled")
                    self.bot.updateStatus(self.tracker.getShortOpenOrderID(), "Filled")
                    self.bot.updateStatus(self.tracker.getShortOpenOrderID(), "Filled")
                    
                    
                if self.tracker.isShortOrderFilled() and not shortDone:
                    if bar.low <= self.tracker.getShortProfitTarget():
                        self.bot.updateStatus(self.tracker.getShortProfitTarget(), "Filled")
                        self.bot.updateStatus(self.tracker.getShortProfitTarget(), "Filled")
                        self.bot.updateStatus(self.tracker.getShortProfitTarget(), "Filled")
                        shortDone = True
            
                        
            frozen_datetime.tick(delta=datetime.timedelta(seconds=31))
            for bar in testBars[-6:]:
                self.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)
                
            self.assertTrue(self.bot.processedEndOfDay, "Is EOD")
                
            self.ib.updatePortfolio(self.bot.contract, -8, 157, None,None, None, None, None)
            
            self.assertTrue("META" in self.ib.closedPositions, "processed meta")
            
            self.assertEqual(len(self.ib.orderList), 4, "check closing orders")
            self.assertEqual(self.ib.orderList[-1][1].primaryExchange, "NASDAQ", "processed meta")
            self.assertEqual(self.ib.orderList[-1][2].totalQuantity, 8, "close stock")
            self.assertEqual(self.ib.orderList[-1][2].action, "BUY", "close stock by buying")
                
        

class IBWrapper(IBClient.IBApi):
    def __init__(self):
        IBClient.IBApi.closedPositions = []
        self.orderList = []

    def reqRealTimeBars(self, reqId, contract, barSize,
                        whatToShow, useRTH,
                        realTimeBarsOptions):
        pass

    def placeOrder(self, orderId, contract, order):
        self.orderList.append((orderId, contract, order))
    
    def reqGlobalCancel(self):
        pass
    
    def reqAccountUpdates(self, first, second):
        pass

if __name__ == '__main__':
    unittest.main()