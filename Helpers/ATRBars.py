#Bar Object
class ATRBar:
    
    def __init__(self):
        self.low = 0
        self.high = 0
        self.close = 0
        self.open = 0
        
    def __str__(self):
        return "Open: " + str(self.open) + "\n" + "Low: " + str(self.low)  + "\n" + "High: " + str(self.high)  + "\n" + "Close: " + str(self.close)