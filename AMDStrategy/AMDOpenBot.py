#Imports
from ibapi.contract import Contract
from Helpers import Bars as bars, Orders as orders
from Globals import Globals as gb

#Bot Logic
class AMDBot:
    ib = None
    contract = None
    barsize = 1
    bars = []
    reqId = 1
    symbol = ""
    startingBars = []
    openBar = None
    
    def __init__(self, ib):
        self.ib = ib

    def setup(self):
        print("Setting up AMD")
        self.ib.reqIds(-1)
        
        self.symbol = "AMD"
        self.barsize = 1
        
        #Create our IB Contract Object
        self.contract = Contract()
        self.contract.symbol = self.symbol.upper()
        self.contract.secType = "STK"
        self.contract.exchange = "SMART"
        self.contract.currency = "USD"
        self.ib.reqIds(-1)
        
        # Request Market Data
        self.ib.reqRealTimeBars(0, self.contract, 5, "TRADES", 1, [])

    def on_bar_update(self, reqId, bar,realtime):
        return

    #Pass realtime bar data back to our bot object
    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        print("current order ID ",  gb.Globals.getInstance().orderId)
        if not self.startingBars or len(self.startingBars) < 12:
            bar = bars.Bar()
            bar.close = close
            bar.date = time
            bar.high = high
            bar.low = low
            bar.open = open_
            bar.volume = volume
            self.startingBars.append(bar)
        else:
            if self.openBar is None:
                self.openBar = bars.Bar()
                self.openBar.low = min(o.low for o in self.startingBars)
                self.openBar.high = max(o.high for o in self.startingBars)

            if self.symbol not in gb.Globals.getInstance().currentOrders:
                expectedHigh = self.openBar.high + self.openBar.high * 0.001
                expectedLow = self.openBar.low - self.openBar.low * 0.001
                print("current high: ", high)
                print("expected high: ", expectedHigh)
                print("current low:", low)
                print("expected low:", expectedLow)
                
                risk = expectedHigh - expectedLow
                quantity = 50
                
                entryLimitForLong = expectedHigh
                entryLimitforShort = expectedLow
                profitTargetForLong = expectedHigh + risk * 3
                profitTargetForShort = expectedLow - risk * 3
                stopLossForLong = expectedLow
                stopLossForShort = expectedHigh

            
                if high > expectedHigh:                    
                    bracket = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "BUY", quantity, entryLimitForLong, profitTargetForLong, stopLossForLong)
                    
                    #Place Bracket Order
                    for o in bracket:
                        if (o.orderType == "STP"):
                            print("The stoploss order is: ", o.orderId)
                            
                            gb.Globals.getInstance().orderResponses[o.orderId] = {}
                            gb.Globals.getInstance().orderResponses[o.orderId]["orders"] = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId+3, "SELL", quantity, entryLimitforShort, profitTargetForShort, stopLossForShort)
                            gb.Globals.getInstance().orderResponses[o.orderId]["contract"] = self.contract
                            
                        self.ib.placeOrder(o.orderId, self.contract,o)
                    
                    self.update_globals_for_orders()
                    
                    print("Buy AMD")
                elif low < expectedLow:
                    
                    bracket = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId, "SELL", quantity, entryLimitforShort, profitTargetForShort, stopLossForShort)
                    
                    #Place Bracket Order
                    for o in bracket:
                        if (o.orderType == "STP"):
                            print("The stoploss order is: ", o.orderId)
                            gb.Globals.getInstance().orderResponses[o.orderId] = {}
                            gb.Globals.getInstance().orderResponses[o.orderId]["orders"] = orders.limitBracketOrder(self.symbol, gb.Globals.getInstance().orderId+3, "BUY", quantity, entryLimitForLong, profitTargetForLong, stopLossForLong)
                            gb.Globals.getInstance().orderResponses[o.orderId]["contract"] = self.contract
                            
                        self.ib.placeOrder(o.orderId, self.contract, o)
                        
                    self.update_globals_for_orders()
                    print("Short AMD")

    def update_globals_for_orders(self):
        gb.Globals.getInstance().currentOrders["AMD"] = gb.Globals.getInstance().orderId
        gb.Globals.getInstance().orderId += 6          