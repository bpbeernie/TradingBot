from LODStrategy import Constants as const
from LODStrategy.LODBounceBot import LODBounceBot

def create_bots(ib):
    bots = []
    
    for stock in const.STOCKS_TO_TRADE:
        bots.append(LODBounceBot(ib, stock))
        
    return bots