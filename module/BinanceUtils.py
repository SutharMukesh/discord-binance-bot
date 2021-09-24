from binance import Client


class BinanceUtils(object):
    """
    This class will contain all of the important functions that will be used that works with both Python 2 and Python 3 interpreters.
    """

    def __init__(self, config):
        self.api_key = config.binance['api_key']
        self.api_secret = config.binance['api_secret']

        self.client = Client(self.api_key, self.api_secret)

    def placeBuyOrder(self, sym, buy_range):
        info = self.client.get_ticker(symbol=sym)
        lastPrice = info['lastPrice']

        print(buy_range, lastPrice)
        if lastPrice in range(buy_range[0], buy_range[1]):
            print('placing buy order')

    def placeSellTargetOrders(self, sym, sell_range):
        print(sym)
