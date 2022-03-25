import yfinance as yf
from _datetime import datetime

msft = yf.Ticker("AMD")

# get stock info
#print(msft.info)

#start = datetime.datetime(2022, 3, 16)

# get historical market data
hist = msft.history(period="1d", interval="1m", prepost=True)

premarket = hist[129:149]

print(type(premarket))
print(type(premarket.loc["2022-03-16 06:29:00-04:00"]))