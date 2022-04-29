import datetime

#STOCKS_TO_TEST = ["AMD", "AAPL", "FB", "PFE", "UAL", "CSCO", "BAC"]
STOCKS_TO_TEST = ["TWTR", "MSFT", "GM", "AAL", "AMD", "AAPL", "FB", "PFE", "UAL", "CSCO", 
                  "BAC", "DIS", "CRM", "BABA", "CMCSA", "PYPL", "ORCL", "MRK", "NVDA", "GILD", "C", 
                  "INTC", "MRVL", "MDLZ", "BA", "V", "JPM"]

HOLIDAYS = [datetime.datetime(2022, 1, 17), datetime.datetime(2022, 2, 21), datetime.datetime(2022, 4, 15),
            datetime.datetime(2022, 6, 20),datetime.datetime(2022, 7, 4),datetime.datetime(2022, 9, 5),
            datetime.datetime(2022,11, 24),datetime.datetime(2022,12, 26)]

DATE_RANGE = [
    #("202201", datetime.datetime(2022, 1, 1), datetime.datetime(2022, 2, 1)),
              #("202202", datetime.datetime(2022, 2, 1), datetime.datetime(2022, 3, 1)),
             # ("202203", datetime.datetime(2022, 3, 1), datetime.datetime(2022, 4, 1)),
              ("202204", datetime.datetime(2022, 4, 1), datetime.datetime(2022, 4, 29))
              ]

OUTPUT_PATH = "C:/Users/bpbee/Desktop/trading/BackTesting/"