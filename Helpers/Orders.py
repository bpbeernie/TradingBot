from ibapi.contract import Contract
from ibapi.order import *
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/orders.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

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
    
    logger.info("Reverse action is: " + reverseAction)
    
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
    
    logger.info(parent)
    logger.info(profitTargetOrder)
    logger.info(stopLossOrder)
    logger.info("Quantity: " + str(stopLossOrder.totalQuantity))
    logger.info("Stop loss Price: " + str(stopLossOrder.auxPrice))

    return parent, profitTargetOrder, stopLossOrder


def closingOrder(symbol, orderId, quantity):    
    contract = Contract()
    contract.symbol = symbol.upper()
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    
    if (quantity > 0):
        action = "SELL"
    else:
        action = "BUY"
    
    # Create Parent Order / Initial Entry
    closingOrder = Order()
    closingOrder.orderId = orderId
    closingOrder.orderType = "MKT"
    closingOrder.action = action
    closingOrder.totalQuantity = abs(quantity)
    closingOrder.transmit = True
 
    logger.info(closingOrder)
 
    return contract, closingOrder