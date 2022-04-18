from Helpers import Bars as bars, Orders as orders
from Globals import Globals as gb
import logging
import os
from AMDStrategy import Constants as const
import math
from AMDStrategy import OpenBotBase

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/amd.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class ReverseAMDBot(OpenBotBase.OpenBotBase):
    
    def updateStatus(self, orderID, status):
        if self.executionTracker.isLongOrderExecuted() and self.executionTracker.isShortOrderExecuted():
            self.done = True
            return
        
        if self.executionTracker.isLongOrderExecuted():
            if status == "Filled":
                if orderID == self.executionTracker._longOrder._stopOrder.orderId:
                    logger.info("AMD Stop order hit, creating possibility response order.")
                    gb.Globals.getInstance().activeOrders.pop(self.symbol)
                
                if orderID == self.executionTracker._longOrder._profitOrder.orderId:
                    logger.info("AMD profit hit, creating for reverse order.")
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "SELL", self.quantity, self.entryLimitForShort, self.profitTargetForShort, self.stopLossForShort)
                    
                    self.executionTracker.setShort(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                    
                    self.update_globals_for_orders()
                
        if self.executionTracker.isShortOrderExecuted():
            if status == "Filled": 
                if orderID == self.executionTracker._shortOrder._stopOrder.orderId:
                    logger.info("AMD Stop order hit, creating possibility response order.")
                    gb.Globals.getInstance().activeOrders.pop(self.symbol)
                    
                if orderID == self.executionTracker._shortOrder._profitOrder.orderId:
                    logger.info("AMD profit hit, creating for reverse order.")

                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "BUY", self.quantity, self.entryLimitForLong, self.profitTargetForLong, self.stopLossForLong)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                
                    self.update_globals_for_orders()

    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        self.check_end_of_day()
        
        if self.done:
            return
        
        if reqId != self.reqId:
            return
        
        if not self.startingBars or len(self.startingBars) < 12:
            bar = bars.Bar()
            bar.close = close
            bar.date = time
            bar.high = high
            bar.low = low
            bar.open = open_
            bar.volume = volume
            self.startingBars.append(bar)
            logger.info("Creating open bar")
        else:
            if self.openBar is None:
                self.openBar = bars.Bar()
                self.openBar.low = min(o.low for o in self.startingBars)
                self.openBar.high = max(o.high for o in self.startingBars)

            if self.executionTracker.isLongOrderExecuted() and self.executionTracker.isShortOrderExecuted():
                if self.timingCounter % 120 == 0:
                    logger.info("Both long and Short are done for: " + self.symbol)
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
                self.quantity = math.ceil(const.CASHRISK / risk)
                
                self.entryLimitForLong = expectedLow
                self.entryLimitForShort = expectedHigh
                self.profitTargetForLong = expectedHigh
                self.profitTargetForShort = expectedLow
                self.stopLossForLong = expectedLow - risk
                self.stopLossForShort = expectedHigh + risk

            
                if high > self.entryLimitForShort and not self.executionTracker.isShortOrderExecuted():                    
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "SELL", self.quantity, self.entryLimitForShort, self.profitTargetForShort, self.stopLossForShort)
                    
                    self.executionTracker.setShort(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                    
                    self.update_globals_for_orders()
                    
                    logger.info("Short AMD")
                elif low < self.entryLimitForLong and not self.executionTracker.isLongOrderExecuted():
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "BUY", self.quantity, self.entryLimitForLong, self.profitTargetForLong, self.stopLossForLong)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)

                    self.update_globals_for_orders()
                    
                    logger.info("Buy AMD")