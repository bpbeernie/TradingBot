#Bar Object
class Bar:
    def __init__(self):
        self.open = 0
        self.low = 0
        self.high = 0
        self.close = 0
        self.volume = 0
        self.date = ''
        
    def __str__(self):
        return "Open: " + str(self.open) + "\n" + "Low: " + str(self.low)  + "\n" + "High: " + str(self.high)  + "\n" + "Close: " + str(self.close)  + "\n" + "Volume: " + str(self.volume or '')  + "\n" + "Date: " + str(self.date or '')  + "\n"
    
    def __repr__(self):
        return str(self) 