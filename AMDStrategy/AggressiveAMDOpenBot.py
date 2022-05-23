from Helpers import Bars as bars, Orders as orders
from Globals import Globals as gb
import logging
import os
from AMDStrategy import Constants as const
import math
from AMDStrategy import OpenBotBase
from pickle import TRUE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/amd.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class AggressiveAMDBot(OpenBotBase.OpenBotBase):
    
    def updateStatus(self, orderID, status):
        if self.executionTracker.isLongOrderFilled() and self.executionTracker.isShortOrderFilled():
            return
        
        if self.executionTracker.isLongOrderSent():
            if status == "Filled":
                if orderID == self.executionTracker._longOrder._openOrder.orderId:
                    logger.info(self.symbol + " Long entry filled.")
                    self.executionTracker._longOrderFilled = True
                
                if orderID == self.executionTracker._longOrder._stopOrder.orderId:
                    logger.info(self.symbol + " Stop order hit, creating response order.")
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "SELL", self.quantity, self.entryLimitForShort, self.profitTargetForShort, self.stopLossForShort)
                    
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
                if orderID == self.executionTracker._shortOrder._openOrder.orderId:
                    logger.info(self.symbol + " Short entry filled.")
                    self.executionTracker._shortOrderFilled = True
                
                if orderID == self.executionTracker._shortOrder._stopOrder.orderId:
                    logger.info(self.symbol + " Stop order hit, creating response order.")
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "BUY", self.quantity, self.entryLimitForLong, self.profitTargetForLong, self.stopLossForLong)
                    
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
                    
    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        if self.done:
            return
        
        self.check_end_of_day()
        
        if (reqId != self.reqId):
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
                self.quantity = math.ceil(const.CASHRISK / risk)
                
                self.entryLimitForLong = expectedHigh
                self.entryLimitForShort = expectedLow
                self.profitTargetForLong = expectedHigh + risk * 3
                self.profitTargetForShort = expectedLow - risk * 3
                self.stopLossForLong = expectedLow
                self.stopLossForShort = expectedHigh

            
                if high >= expectedHigh and not self.executionTracker.isLongOrderSent():                    
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "BUY", self.quantity, self.entryLimitForLong, self.profitTargetForLong, self.stopLossForLong)
                    
                    self.executionTracker.setLong(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)

                    self.update_globals_for_orders()
                    
                    logger.info("Buy " + self.symbol)
                elif low <= expectedLow and not self.executionTracker.isShortOrderSent():
                    openOrder, profitOrder, stopOrder = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().getOrderId(3), "SELL", self.quantity, self.entryLimitForShort, self.profitTargetForShort, self.stopLossForShort)
                    
                    self.executionTracker.setShort(openOrder, profitOrder, stopOrder)
                    
                    self.ib.placeOrder(openOrder.orderId, self.contract, openOrder)
                    self.ib.placeOrder(profitOrder.orderId, self.contract, profitOrder)
                    self.ib.placeOrder(stopOrder.orderId, self.contract, stopOrder)
                    
                    self.update_globals_for_orders()
                    
                    logger.info("Short " + self.symbol)
