#Bar Object
class ATRBar:
    low = 0
    high = 0
    close = 0
    open = 0
        
    def __str__(self):
        return "Open: " + str(self.open) + "\n" + "Low: " + str(self.low)  + "\n" + "High: " + str(self.high)  + "\n" + "Close: " + str(self.close)