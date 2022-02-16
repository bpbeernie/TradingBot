from UpwardBreakTriangleStrategy import InteractiveBrokersPythonBot
from AMDStrategy import AMDOpenBot
from IB import IBClient as ibClient
import threading
import time
import pytz

def run():
    #Connect to IB on init
    ib = ibClient.IBApi()
    ib.connect("127.0.0.1", 7466, 1)
    

    print("Connected!")
    ib_thread = threading.Thread(target=run_loop, args=(ib,), daemon=True)
    ib_thread.start()
    
    time.sleep(1)
    
    botList = []
    
    #botList.append(InteractiveBrokersPythonBot.Bot(ib)) 
    botList.append(AMDOpenBot.AMDBot(ib)) 
    ib.addBots(botList)
    
    for bot in botList:
        bot.setup()


def run_loop(ib):
    print(ib)
    ib.run()

if __name__ == '__main__':
    run()