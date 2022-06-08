from Helpers import Bars as bars, OrdersV2 as orders
from Globals import Globals as gb
import logging
import os
from AMDStrategy import Constants as const
import math
from AMDStrategy import OpenBotBase, TrackerWrapper

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/amd3.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class AggressiveAMDBotV3(OpenBotBase.OpenBotBase):
    
    def setup(self):
        super().setup()
        
        self.updated_tracker = TrackerWrapper.TrackerWrapper(self.executionTracker)
        self.numStartingBars = const.STARTING_BAR_COUNT
    
    def updateStatus(self, orderID, status):
        if self.executionTracker.isLongOrderFilled() and self.executionTracker.isShortOrderFilled():
            return
        
        if self.executionTracker.isLongOrderSent():
            if status == "Filled":
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
                
                if orderID == self.executionTracker._longOrder._profitOrder.orderId:
                    logger.info(self.symbol + " long profit hit")
                    self.done = True
                
        if self.executionTracker.isShortOrderSent():
            if status == "Filled": 
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
                
                if orderID == self.executionTracker._shortOrder._profitOrder.orderId:
                    logger.info(self.symbol + " short profit hit")
                    self.done = True

    def cancel_entry_order(self, orderID):
        logger.info(self.symbol + " hit profit target without filling entry, canceling")
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
        if self.done:
            return
        
        self.check_end_of_day()
        
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
                
            if self.executionTracker.isLongOrderFilled() and self.executionTracker.isShortOrderFilled():
                if self.timingCounter % 120 == 0:
                    logger.info("Both long and Short are done")
                self.timingCounter += 1
                return
            
            if self.executionTracker.isLongOrderSent() and not self.executionTracker.isLongOrderFilled():
                if high >= self.executionTracker._longOrder._profitOrder.lmtPrice:
                    logger.info("Long profit hit without fill")
                    self.cancel_entry_order(self.executionTracker._longOrder._openOrder.orderId)
                    return
                
            if self.executionTracker.isShortOrderSent() and not self.executionTracker.isShortOrderFilled():
                if low <= self.executionTracker._shortOrder._profitOrder.lmtPrice:
                    logger.info("Short profit hit without fill")
                    self.cancel_entry_order(self.executionTracker._shortOrder._openOrder.orderId)
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
                
                if entryAmount > 20000:
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
