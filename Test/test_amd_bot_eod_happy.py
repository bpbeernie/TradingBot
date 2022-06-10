import unittest
from unittest.mock import patch, Mock
from IB import IBClient
import sys
sys.modules['gb'] = Mock()
from AMDStrategy.AggressiveAMDOpenBotV3 import AggressiveAMDBotV3
from random import seed
from random import uniform
from random import randint
from Globals import Globals as gb
from freezegun import freeze_time
import datetime
import pytz
import pickle
from AMDStrategy.TrackerWrapper import TrackerWrapper
from ibapi.contract import Contract

class TestAMDBotEOD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with freeze_time("2022-04-05 12:59:00") as frozen_datetime:
            requestID = 1
            cls.ib = IBWrapper()
            
            cls.bot = AggressiveAMDBotV3(cls.ib, "META")
    
            cls.bot.setup()
            cls.tracker = TrackerWrapper(cls.bot.executionTracker)
            
            file_name = "Data/META_2022-06-10.pkl"
            
            testBars = []
            
            with (open(file_name, "rb")) as openfile:
                while True:
                    try:
                        testBars.extend(pickle.load(openfile))
                    except EOFError:
                        break
            
            longDone = False
            shortDone = False
            for bar in testBars[:-6]:
                cls.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)
            
                if cls.tracker.isShortOrderSent() and not cls.tracker.isShortOrderFilled():
                    cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                    cls.shortOpenID = cls.tracker.getShortOpenOrderID()
                    cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                    cls.bot.updateStatus(cls.tracker.getShortOpenOrderID(), "Filled")
                    
                    
                if cls.tracker.isShortOrderFilled() and not shortDone:
                    if bar.low <= cls.tracker.getShortProfitTarget():
                        cls.bot.updateStatus(cls.tracker.getShortProfitTarget(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getShortProfitTarget(), "Filled")
                        cls.bot.updateStatus(cls.tracker.getShortProfitTarget(), "Filled")
                        shortDone = True
            
                        
            frozen_datetime.tick(delta=datetime.timedelta(seconds=31))
            for bar in testBars[-6:]:
                cls.bot.on_realtime_update(requestID, None, bar.open, bar.high, bar.low, bar.close, None, None, None)
                
    def test_processed_end_of_day_pass(self):
        self.assertTrue(self.bot.processedEndOfDay, "Is EOD")

    def test_meta_processed(self):
        TestAMDBotEOD.ib.updatePortfolio(self.bot.contract, -8, 157, None,None, None, None, None)
        
        self.assertTrue("META" in self.ib.closedPositions, "processed meta")
        
        self.assertEqual(len(TestAMDBotEOD.ib.orderList), 4, "check closing orders")
        self.assertEqual(TestAMDBotEOD.ib.orderList[-1][1].primaryExchange, "NASDAQ", "processed meta")
        self.assertEqual(TestAMDBotEOD.ib.orderList[-1][2].totalQuantity, 8, "close stock")
        self.assertEqual(TestAMDBotEOD.ib.orderList[-1][2].action, "BUY", "close stock by buying")
        

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