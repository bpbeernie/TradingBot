from UpwardBreakTriangleStrategy import InteractiveBrokersPythonBot
from AMDStrategy import AMDOpenBot
from IB import IBClient as ibClient
import threading
import time
import pytz
import logging
import Constants as const
import os
from LODStrategy import LODBounceBotBuilder

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
    ib.connect(const.LOCALIP, const.PORT, 1)
    logger.info("Connected at port {}".format(const.PORT))
    
    ib_thread = threading.Thread(target=run_loop, args=(ib,), daemon=True)
    ib_thread.start()
    
    time.sleep(1)
    
    botList = []
    
    #botList.append(InteractiveBrokersPythonBot.Bot(ib)) 
    botList.extend(LODBounceBotBuilder.create_bots(ib))
    #botList.append(AMDOpenBot.AMDBot(ib)) 
    ib.addBots(botList)
    
    for bot in botList:
        bot.setup()


def run_loop(ib):
    print(ib)
    ib.run()

if __name__ == '__main__':
    run()