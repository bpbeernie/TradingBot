import ibapi
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from Globals import Globals as gb
import threading
import logging
import os
from Helpers import Orders as ord

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/client.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


#Class for Interactive Brokers Connection
class IBApi(EWrapper,EClient):
    _botList = []
    lock = threading.Lock()
    
    def __init__(self):
        EClient.__init__(self, self)
        
    def addBots(self, bots):
        self._botList = bots
        
    # Historical Backtest Data
    def historicalData(self, reqId, bar):
        try:
            for bot in self._botList:
                bot.on_bar_update(reqId,bar,False)
        except Exception as e:
            print(e)
    # On Realtime Bar after historical data finishes
    def historicalDataUpdate(self, reqId, bar):
        try:
            for bot in self._botList:
                bot.on_bar_update(reqId,bar,True)
        except Exception as e:
            print(e)
    # On Historical Data End
    def historicalDataEnd(self, reqId, start, end):
        print("historicalDataEnd")
        print(reqId)
    # Get next order id we can use
    def nextValidId(self, nextorderId):
        gb.Globals.getInstance().orderId = nextorderId
        
    def orderStatus(self, orderId , status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print("OrderStatus. Id: ", orderId, ", Status: ", status, ", Filled: ", filled, ", Remaining: ", remaining, ", LastFillPrice: ", lastFillPrice)
        
        self.lock.acquire()
        if status == "Filled" and orderId in gb.Globals.getInstance().orderResponses:
            print("Response orders are being filled!")
            orders = gb.Globals.getInstance().orderResponses[orderId]["orders"]
            contract = gb.Globals.getInstance().orderResponses[orderId]["contract"]
            for o in orders:
                self.placeOrder(o.orderId, contract, o)
        
            gb.Globals.getInstance().orderId += 3
            del gb.Globals.getInstance().orderResponses[orderId]
        self.lock.release()
            
    # Listen for realtime bars
    def realtimeBar(self, reqId, time, open_, high, low, close,volume, wap, count):
        super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        try:
            for bot in self._botList:
                bot.on_realtime_update(reqId, time, open_, high, low, close, volume, wap, count)
        except Exception as e:
            print(e)
            
    def error(self, id, errorCode, errorMsg):
        print(errorCode)
        print(errorMsg)
        
    def updatePortfolio(self, contract, position,
                    marketPrice, marketValue,averageCost, unrealizedPNL, realizedPNL, accountName):
        
        super().updatePortfolio(contract, position, marketPrice,
                                marketValue,averageCost, unrealizedPNL,
                                realizedPNL, accountName)
        
        logger.info("Closing all Positions!")
        gb.Globals.getInstance().orderResponses = {}
        closingOrder = ord.closingOrder(contract.symbol, gb.Globals.getInstance().orderId, position)
        self.placeOrder(closingOrder.orderId, contract, closingOrder)
        gb.Globals.getInstance().orderId +=1

