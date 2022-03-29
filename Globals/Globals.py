import threading

class Globals:
    lock = threading.Lock()

    __instance = None
    @staticmethod 
    def getInstance():
        """ Static access method. """
        if Globals.__instance == None:
            Globals()
        return Globals.__instance
    def __init__(self):
        """ Virtually private constructor. """
        if Globals.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Globals.__instance = self
            self.orderId = 1
            self.activeOrders = {}
            self.orderResponses = {}
            
    def getOrderId(self, value=1):
        Globals.lock.acquire()
        
        tempValue = self.orderId
        self.orderId += value
        
        Globals.lock.release()
        
        return tempValue