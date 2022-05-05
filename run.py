from UpwardBreakTriangleStrategy import InteractiveBrokersPythonBot
from AMDStrategy import AggressiveAMDOpenBot, ReverseAMDOpenBot
from LODStrategy import LODBounceBotBuilder
from IB import IBClient as ibClient
import threading
import time
import logging
import Constants as const
import os
from IBTest import IBTestClient
from IBTest.IBTestClient import IBTestApi

try:
    if os.environ['ENV'] == const.PROD:
        from Config.production import *
    elif os.environ['ENV'] == const.DEV:
        from Config.development import *
except KeyError:
    from Config.development import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_filename = "logs/main.log"
os.makedirs(os.path.dirname(log_filename), exist_ok=True)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log_filename, mode="a", encoding=None, delay=False)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def run():
    #Connect to IB on init
    ib = ibClient.IBApi()
    ib.connect(const.LOCALIP, PORT, 1)
    logger.info("Connected at port {}".format(PORT))
    
    ib_thread = threading.Thread(target=run_loop, args=(ib,), daemon=True)
    ib_thread.start()
    
    time.sleep(1)
    ib.reqIds(-1)
    
    botList = []

    #botList.append(InteractiveBrokersPythonBot.Bot(ib)) 
    #botList.append(AMDOpenBot.AMDBot(ib)) 
    
    botList.append(AggressiveAMDOpenBot.AggressiveAMDBot(ib, "FB")) 
    #botList.append(AggressiveAMDOpenBot.AggressiveAMDBot(ib, "ORCL")) 
    botList.append(AggressiveAMDOpenBot.AggressiveAMDBot(ib, "TWTR")) 
    botList.append(AggressiveAMDOpenBot.AggressiveAMDBot(ib, "AAPL")) 
    
    testIB = IBTestApi(ib)
    botList.extend(LODBounceBotBuilder.create_bots(testIB))
    
    ib.addBots(botList)

    for bot in botList:
        bot.setup()


def run_loop(ib):
    print(ib)
    ib.run()

if __name__ == '__main__':
    run()