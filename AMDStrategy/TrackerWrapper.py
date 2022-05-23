class TrackerWrapper():
    def __init__(self, amdTracker):
        self._amdTracker = amdTracker
        
    def isShortOrderSent(self):
        return self._amdTracker.isShortOrderSent()
        
    def isLongOrderSent(self):
        return self._amdTracker.isLongOrderSent()
        
    def isShortOrderFilled(self):
        return self._amdTracker.isShortOrderFilled()
    
    def isLongOrderFilled(self):
        return self._amdTracker.isLongOrderFilled()
    
    
    def getShortOpenOrderID(self):
        return self._amdTracker._shortOrder._openOrder.orderId
    
    def getLongOpenOrderID(self):
        return self._amdTracker._longOrder._openOrder.orderId
    
    def getShortProfitTarget(self):
        return self._amdTracker._shortOrder._profitOrder.lmtPrice
    
    def getLongProfitTarget(self):
        return self._amdTracker._longOrder._profitOrder.lmtPrice
    
    def getShortProfitID(self):
        return self._amdTracker._shortOrder._profitOrder.orderId
    
    def getLongProfitID(self):
        return self._amdTracker._longOrder._profitOrder.orderId
    
    def getShortStopPrice(self):
        return self._amdTracker._shortOrder._stopOrder.auxPrice
    
    def getLongStopPrice(self):
        return self._amdTracker._longOrder._stopOrder.auxPrice
    
    def getShortStopID(self):
        return self._amdTracker._shortOrder._stopOrder.orderId
    
    def getLongStopID(self):
        return self._amdTracker._longOrder._stopOrder.orderId