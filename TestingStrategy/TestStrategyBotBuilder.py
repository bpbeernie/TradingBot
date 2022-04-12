from TestingStrategy import Constants as const, TestStrategyBot

def create_bots(ib):
    bots = []
    
    for stock in const.STOCKS_TO_TEST:
        bots.append(TestStrategyBot.TestBot(ib, stock))
        
    return bots