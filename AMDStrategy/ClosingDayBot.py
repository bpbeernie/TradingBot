from AMDStrategy import OpenBotBase

class ClosingDayBot(OpenBotBase.OpenBotBase):
    
    def __init__(self, ib, symbol=None):
        self.ib = ib
        self.symbol = symbol
    
    def setup(self):
        print(f'Start: Closing Day Bot')
    
                    
    def on_realtime_update(self, reqId, time, open_, high, low, close, volume, wap, count):
        self.check_end_of_day()
        
