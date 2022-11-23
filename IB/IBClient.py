from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from Globals import Globals as gb
from Helpers import OrdersV2 as ord
import datetime
import pytz
from Globals import SpecialDates as specialdates

#Class for Interactive Brokers Connection
class IBApi(EWrapper,EClient):
    
    
    def __init__(self):
        EClient.__init__(self, self)
        self.closedPositions = []
        self._stocksToClose = []
        
    def addBots(self, bots):
        self._botList = bots
        
    def addStocksToClose(self, stock):
        self._stocksToClose.append(stock)
        
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
        
        if datetime.datetime.today().date() in specialdates.EARLY_DATES:
            self.updatePortfolioEarly(contract, position,
                    marketPrice, marketValue,averageCost, unrealizedPNL, realizedPNL, accountName)
        else:
            self.updatePortfolioNormal(contract, position,
                    marketPrice, marketValue,averageCost, unrealizedPNL, realizedPNL, accountName)
        
    def updatePortfolioNormal(self, contract, position,
                    marketPrice, marketValue,averageCost, unrealizedPNL, realizedPNL, accountName):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today1259pm = now.replace(hour=12, minute=59, second=30, microsecond=0)
        
        print("Received Portfolio Update: " + contract.symbol + " : " + str(position))
        
        if now > today1259pm:
            if position != 0 and contract.symbol not in self.closedPositions:
                print("Closing position for: " + contract.symbol)
                self.closedPositions.append(contract.symbol)
                gb.Globals.getInstance().orderResponses = {}
                closingContract, closingOrder = ord.closingOrder(contract.symbol, gb.Globals.getInstance().getOrderId(), position)
                self.placeOrder(closingOrder.orderId, closingContract, closingOrder)
        else:
            if contract.symbol in self._stocksToClose and position != 0:
                self._stocksToClose.remove(contract.symbol)
                print("Closing individual stock position for: " + contract.symbol)
                gb.Globals.getInstance().orderResponses = {}
                closingContract, closingOrder = ord.closingOrder(contract.symbol, gb.Globals.getInstance().getOrderId(), position)
                self.placeOrder(closingOrder.orderId, closingContract, closingOrder)
         
    def updatePortfolioEarly(self, contract, position,
                    marketPrice, marketValue,averageCost, unrealizedPNL, realizedPNL, accountName):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        today959pm = now.replace(hour=9, minute=59, second=30, microsecond=0)
        
        print("Received Portfolio Update: " + contract.symbol + " : " + str(position))
        
        if now > today959pm:
            if position != 0 and contract.symbol not in self.closedPositions:
                print("Closing early position for: " + contract.symbol)
                self.closedPositions.append(contract.symbol)
                gb.Globals.getInstance().orderResponses = {}
                closingContract, closingOrder = ord.closingOrder(contract.symbol, gb.Globals.getInstance().getOrderId(), position)
                self.placeOrder(closingOrder.orderId, closingContract, closingOrder)
        else:
            if contract.symbol in self._stocksToClose and position != 0:
                self._stocksToClose.remove(contract.symbol)
                print("Closing early individual stock position for: " + contract.symbol)
                gb.Globals.getInstance().orderResponses = {}
                closingContract, closingOrder = ord.closingOrder(contract.symbol, gb.Globals.getInstance().getOrderId(), position)
                self.placeOrder(closingOrder.orderId, closingContract, closingOrder)

    def position(self, account, contract, position, float):
        print("Received Position Update: " + contract.symbol + " : " + str(position))
        if position != 0 and contract.symbol not in self.closedPositions:
            print("Closing position for: " + contract.symbol)
            self.closedPositions.append(contract.symbol)
            gb.Globals.getInstance().orderResponses = {}
            closingContract, closingOrder = ord.closingOrder(contract.symbol, gb.Globals.getInstance().getOrderId(), position)
            self.placeOrder(closingOrder.orderId, closingContract, closingOrder)
