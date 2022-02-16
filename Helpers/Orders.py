from ibapi.contract import Contract
from ibapi.order import *

#Bracet Order Setup
def bracketOrder(symbol, parentOrderId, action, quantity, profitTarget, stopLoss):
    #Initial Entry
    #Create our IB Contract Object
    contract = Contract()
    contract.symbol = symbol.upper()
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    # Create Parent Order / Initial Entry
    parent = Order()
    parent.orderId = parentOrderId
    parent.orderType = "MKT"
    parent.action = action
    parent.totalQuantity = quantity
    parent.transmit = False
    # Profit Target
    profitTargetOrder = Order()
    profitTargetOrder.orderId = parent.orderId+1
    profitTargetOrder.orderType = "LMT"
    profitTargetOrder.action = "SELL"
    profitTargetOrder.totalQuantity = quantity
    profitTargetOrder.lmtPrice = round(profitTarget,2)
    profitTargetOrder.parentId = parentOrderId
    profitTargetOrder.transmit = False
    # Stop Loss
    stopLossOrder = Order()
    stopLossOrder.orderId = parent.orderId+2
    stopLossOrder.orderType = "STP"
    stopLossOrder.action = "SELL"
    stopLossOrder.totalQuantity = quantity
    stopLossOrder.parentId = parentOrderId
    stopLossOrder.auxPrice = round(stopLoss,2)
    stopLossOrder.transmit = True

    bracketOrders = [parent, profitTargetOrder, stopLossOrder]
    return bracketOrders

def limitBracketOrder(symbol, parentOrderId, action, quantity, limit, profitTarget, stopLoss):
    ocaGroup = "OCA_"+str(parentOrderId)
    
    contract = Contract()
    contract.symbol = symbol.upper()
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    
    if (action == "BUY"):
        reverseAction = "SELL"
    else:
        reverseAction = "BUY"
    
    print("Reverse action is: " + reverseAction)
    
    # Create Parent Order / Initial Entry
    parent = Order()
    parent.orderId = parentOrderId
    parent.orderType = "LMT"
    parent.action = action
    parent.lmtPrice = round(limit,2)
    parent.totalQuantity = quantity
    parent.ocaGroup = ocaGroup
    parent.transmit = False
    # Profit Target
    profitTargetOrder = Order()
    profitTargetOrder.orderId = parent.orderId+1
    profitTargetOrder.orderType = "LMT"
    profitTargetOrder.action = reverseAction
    profitTargetOrder.totalQuantity = quantity
    profitTargetOrder.lmtPrice = round(profitTarget,2)
    profitTargetOrder.parentId = parentOrderId
    profitTargetOrder.ocaGroup = ocaGroup
    profitTargetOrder.transmit = False
    # Stop Loss
    stopLossOrder = Order()
    stopLossOrder.orderId = parent.orderId+2
    stopLossOrder.orderType = "STP"
    stopLossOrder.action = reverseAction
    stopLossOrder.totalQuantity = quantity
    stopLossOrder.parentId = parentOrderId
    stopLossOrder.auxPrice = round(stopLoss,2)
    stopLossOrder.ocaGroup = ocaGroup
    stopLossOrder.transmit = True

    bracketOrders = [parent, profitTargetOrder, stopLossOrder]
    return bracketOrders