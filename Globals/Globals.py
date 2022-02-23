class Globals:
    orderId = 1
    activeOrders = {}
    orderResponses = {}
    
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