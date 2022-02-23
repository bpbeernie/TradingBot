class AMDExecutionTracker:
    def __init__(self):
        self._shortOrder = None
        self._longOrder = None
        
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
        
    def isLongOrderExecuted(self):
        return self._longOrder is not None
    
    def isShortOrderExecuted(self):
        return self._shortOrder is not None
    
class OrderSet:
    _openOrder = None;
    _stopOrder = None;
    _profitOrder = None;