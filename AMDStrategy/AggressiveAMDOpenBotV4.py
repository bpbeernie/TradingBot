from Helpers import Bars as bars, OrdersV2 as orders
from Globals import Globals as gb
import logging
import os
from AMDStrategy import Constants as const
import math
from AMDStrategy import OpenBotBase, TrackerWrapper
import datetime
import pytz

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/amd4.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class AggressiveAMDBotV4(OpenBotBase.OpenBotBase):
    
    def setup(self):
        super().setup()
        
        self.updated_tracker = TrackerWrapper.TrackerWrapper(self.executionTracker)
        self.numStartingBars = const.STARTING_BAR_COUNT
    
    def updateStatus(self, orderID, status):
        if self.done:
            return
        
        if status != "Filled":
            return
        
        if self.executionTracker.isLongOrderFilled() and self.executionTracker.isShortOrderFilled():
            if orderID == self.updated_tracker.getLongProfitID() and not self.updated_tracker.isLongProfitHit():
                logger.info(self.symbol + " long reverse profit hit")
                self.executionTracker._longProfitHit = True
                self.done = True
                
            if orderID == self.updated_tracker.getLongStopID() and not self.updated_tracker.isLongStopHit():
                logger.info(self.symbol + " reverse long stop hit")
                self.done = True
                self.executionTracker._longStopHit = True
                
            if orderID == self.updated_tracker.getShortProfitID():
                logger.info(self.symbol + " short reverse profit hit")
                self.executionTracker._shortProfitHit = True
                self.done = True
                
            if orderID == self.updated_tracker.getShortStopID() and not self.updated_tracker.isShortStopHit():
                logger.info(self.symbol + " reverse short stop hit")
                self.done = True
                self.executionTracker._shortStopHit = True
        else:
            if self.executionTracker.isLongOrderSent():
                if orderID == self.executionTracker._longOrder._openOrder.orderId and not self.executionTracker.isLongOrderFilled():
                    logger.info(self.symbol + " Long entry filled.")
                    self.executionTracker._longOrderFilled = True
                
                if orderID == self.executionTracker._longOrder._stopOrder.orderId and not self.executionTracker.isShortOrderSent():
                    logger.info(self.symbol + " Stop order hit, creating response order.")
                    openOrder, profitOrder, stopOrder = orders.marketBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "SELL", self.quantity, self.profitTargetForShort, self.stopLossForShort)
                    
                    self.executionTracker.setShort(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                    
                    self.update_globals_for_orders()
                    
                    self.executionTracker._longStopHit = True
                    
                if orderID == self.executionTracker._longOrder._profitOrder.orderId:
                    logger.info(self.symbol + " long profit hit")
                    self.executionTracker._longProfitHit = True
                    self.done = True
                    
            if self.executionTracker.isShortOrderSent():
                if orderID == self.executionTracker._shortOrder._openOrder.orderId and not self.executionTracker.isShortOrderFilled():
                    logger.info(self.symbol + " Short entry filled.")
                    self.executionTracker._shortOrderFilled = True
                
                if orderID == self.executionTracker._shortOrder._stopOrder.orderId and not self.executionTracker.isLongOrderSent():
                    logger.info(self.symbol + " Stop order hit, creating response order.")
                    openOrder, profitOrder, stopOrder = orders.marketBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "BUY", self.quantity, self.profitTargetForLong, self.stopLossForLong)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                
                    self.update_globals_for_orders()
                    
                    self.executionTracker._shortStopHit = True
                
                if orderID == self.executionTracker._shortOrder._profitOrder.orderId:
                    logger.info(self.symbol + " short profit hit")
                    self.executionTracker._shortProfitHit = True
                    self.done = True

    def cancel_entry_order(self, orderID):
        logger.info(self.symbol + " canceling")
        self.ib.cancelOrder(orderID)
        self.done = True
       
    def processBar(self, time, open_, high, low, close, volume):
        bar = bars.Bar()
        bar.close = close
        bar.date = time
        bar.high = high
        bar.low = low
        bar.open = open_
        bar.volume = volume
        
        return bar
                    
    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        self.check_end_of_day()
        
        if self.done:
            return
        
        if self.symbol == "META":
            now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
            today630am = now.replace(hour=6, minute=30, second=0, microsecond=0)
            today1pm = now.replace(hour=13, minute=0, second=0, microsecond=0)
            if now < today630am or now > today1pm:
                logger.info(self.symbol + f" don't process META data outside trading hours")
                return
        
        if (reqId != self.reqId):
            return
        
        if not self.startingBars or len(self.startingBars) < self.numStartingBars:
            bar = self.processBar(time, open_, high, low, close, volume)
            self.startingBars.append(bar)
            logger.info(self.symbol + ": Creating open bar")
        else:
            
            if self.openBar is None:
                self.openBar = bars.Bar()
                self.openBar.low = min(o.low for o in self.startingBars)
                self.openBar.high = max(o.high for o in self.startingBars)
                
            if self.executionTracker.isLongOrderSent() and self.executionTracker.isLongOrderFilled() and not self.done:
                if high >= self.executionTracker._longOrder._profitOrder.lmtPrice:
                    logger.info(self.symbol + ": Long profit hit, making sure position is cancelled")
                    self.cancel_entry_order(self.updated_tracker.getLongOpenOrderID())
                    self.cancel_entry_order(self.updated_tracker.getLongProfitID())
                    self.cancel_entry_order(self.updated_tracker.getLongStopID())
                    self.ib.addStocksToClose(self.symbol)
                    self.ib.reqAccountUpdates(True, "1")
                    self.executionTracker._longProfitHit = True
                    return
                
            if self.executionTracker.isShortOrderSent() and self.executionTracker.isShortOrderFilled() and not self.done:
                if low <= self.executionTracker._shortOrder._profitOrder.lmtPrice:
                    logger.info(self.symbol + ": Short profit hit, making sure order is cancelled")
                    self.cancel_entry_order(self.updated_tracker.getShortOpenOrderID())
                    self.cancel_entry_order(self.updated_tracker.getShortProfitID())
                    self.cancel_entry_order(self.updated_tracker.getShortStopID())
                    self.ib.addStocksToClose(self.symbol)
                    self.ib.reqAccountUpdates(True, "1")
                    self.executionTracker._shortProfitHit = True
                    return

                
            if self.executionTracker.isLongOrderFilled() and self.executionTracker.isShortOrderFilled():
                if self.timingCounter % 120 == 0:
                    logger.info(self.symbol + ": Both long and Short are done")
                self.timingCounter += 1
                return
            

            if self.symbol not in gb.Globals.getInstance().activeOrders:
                openBarDiff = self.openBar.high - self.openBar.low
                expectedHigh = self.openBar.high + openBarDiff * const.OPENBARMARGIN
                expectedLow = self.openBar.low - openBarDiff * const.OPENBARMARGIN
                logger.info(self.symbol + ": current high: {}".format( high))
                logger.info(self.symbol + ": expected high: {}".format(expectedHigh))
                logger.info(self.symbol + ": current low: {}".format(low))
                logger.info(self.symbol + ": expected low: {}".format(expectedLow))
                
                risk = expectedHigh - expectedLow
                
                if risk == 0:
                    bar = self.processBar(time, open_, high, low, close, volume)
                    self.startingBars.append(bar)
                    self.numStartingBars = self.numStartingBars + const.STARTING_BAR_COUNT
                    self.openBar = None
                    
                    logger.info("Risk is 0, Need to increase starting bar")
                    return
                
                
                self.quantity = math.ceil(const.CASHRISK / risk)
                
                self.entryLimitForLong = expectedHigh
                self.entryLimitForShort = expectedLow
                self.profitTargetForLong = expectedHigh + risk * 3
                self.profitTargetForShort = expectedLow - risk * 3
                self.stopLossForLong = expectedLow
                self.stopLossForShort = expectedHigh

                entryAmount = self.entryLimitForLong * self.quantity
                
                if entryAmount > const.MAX_AMOUNT:
                    bar = self.processBar(time, open_, high, low, close, volume)
                    self.startingBars.append(bar)
                    self.numStartingBars = self.numStartingBars + const.STARTING_BAR_COUNT
                    self.openBar = None
                    
                    logger.info("Need to increase starting bar")
                    logger.info(f'{self.symbol} - q:{self.quantity} entry:{self.entryLimitForLong} risk:{risk} amount:{entryAmount}')
                    return
            
                if high >= expectedHigh and not self.executionTracker.isLongOrderSent():                    
                    openOrder, profitOrder, stopOrder = orders.marketBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "BUY", self.quantity, self.profitTargetForLong, self.stopLossForLong)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)

                    self.update_globals_for_orders()
                    
                    logger.info("Buy " + self.symbol)
                elif low <= expectedLow and not self.executionTracker.isShortOrderSent():
                    openOrder, profitOrder, stopOrder = orders.marketBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "SELL", self.quantity, self.profitTargetForShort, self.stopLossForShort)
                    
                    self.executionTracker.setShort(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                    
                    self.update_globals_for_orders()
                    
                    logger.info("Short " + self.symbol)
