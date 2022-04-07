from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from Globals import Globals as gb
from Helpers import Orders as ord
import datetime
import pytz
from IB.IBClient import IBApi

#Class for Interactive Brokers Connection
class IBTestApi(IBApi):
    
    def __init__(self, ib):
        self.__dict__ = ib.__dict__
        
    def placeOrder(self, orderId , contract, order):
        now = datetime.datetime.now().astimezone(pytz.timezone("Canada/Pacific"))
        print("Order Placed for " + contract.symbol + " at " + str(now))
        print("Order ID: " + str(orderId))
        print("Action: " + str(order.action))
        print("Quantity: " + str(order.totalQuantity))
        print("Limit Price: " + str(order.lmtPrice))
        print("Parent ID: " + str(order.parentOrderId))
        print("Aux Price: " + str(order.auxPrice))
        print("Transmit: " + str(order.transmit))
