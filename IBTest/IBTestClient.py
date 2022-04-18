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
        
        try:
            print("Order Placed for " + contract.symbol + " at " + str(now))
        except AttributeError:
            pass
        
        try:
            print("Order ID: " + str(orderId))
        except AttributeError:
            pass
        
        try:
            print("Action: " + str(order.action))
        except AttributeError:
            pass
        
        try:
            print("Quantity: " + str(order.totalQuantity))
        except AttributeError:
            pass
        
        try:
            print("Limit Price: " + str(order.lmtPrice))
        except AttributeError:
            pass
        
        try:
            print("Parent ID: " + str(order.parentOrderId))
        except AttributeError:
            pass
        
        try:
            print("Aux Price: " + str(order.auxPrice))
        except AttributeError:
            pass
            
        try:
            print("Transmit: " + str(order.transmit))
        except AttributeError:
            pass
        print(" ======================= ")

        