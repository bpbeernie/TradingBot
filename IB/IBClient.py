from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from Globals import Globals as gb
from Helpers import Orders as ord

#Class for Interactive Brokers Connection
class IBApi(EWrapper,EClient):
    
    
    def __init__(self):
        EClient.__init__(self, self)
        self.closedPositions = []
        
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
        try:
            for bot in self._botList:
                bot.historicalDataEnd(reqId)
        except Exception as e:
            print(e)
    # Get next order id we can use
    def nextValidId(self, nextorderId):
        gb.Globals.getInstance().orderId = nextorderId
        
    def orderStatus(self, orderId , status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print("OrderStatus. Id: ", orderId, ", Status: ", status, ", Filled: ", filled, ", Remaining: ", remaining, ", LastFillPrice: ", lastFillPrice)
        
        try:
            for bot in self._botList:
                bot.updateStatus(orderId, status)
        except Exception as e:
            print(e)
        
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
        
        print("Received Portfolio Update: " + contract.symbol + " : " + str(position))
        
        if position != 0 and contract.symbol not in self.closedPositions:
            print("Closing position for: " + contract.symbol)
            self.closedPositions.append(contract.symbol)
            gb.Globals.getInstance().orderResponses = {}
            closingContract, closingOrder = ord.closingOrder(contract.symbol, gb.Globals.getInstance().getOrderId(), position)
            self.placeOrder(closingOrder.orderId, closingContract, closingOrder)

