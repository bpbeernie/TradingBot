class AMDExecutionTracker:
    def __init__(self):
        self._shortOrder = None
        self._longOrder = None
        self._shortOrderFilled = False
        self._longOrderFilled = False
        
    def setShort(self, openOrder, profitOrder, stopOrder):
        self._shortOrder = OrderSet()
        
        self._shortOrder._openOrder = openOrder
        self._shortOrder._profitOrder = profitOrder
        self._shortOrder._stopOrder = stopOrder

    def setLong(self, openOrder, profitOrder, stopOrder):
        self._longOrder = OrderSet()
        
        self._longOrder._openOrder = openOrder
        self._longOrder._profitOrder = profitOrder
        self._longOrder._stopOrder = stopOrder
        
    def isLongOrderSent(self):
        return self._longOrder is not None
    
    def isShortOrderSent(self):
        return self._shortOrder is not None
    
    def isLongOrderFilled(self):
        return self._longOrderFilled
    
    def isShortOrderFilled(self):
        return self._shortOrderFilled
    
class OrderSet:
    def __init__(self):
        self._openOrder = None;
        self._stopOrder = None;
        self._profitOrder = None;