from binance import Client


class BinanceUtils(object):
    """
    This class will contain all of the important functions that will be used that works with both Python 2 and Python 3 interpreters.
    """

    def __init__(self, config):
        self.api_key = config.binance['api_key']
        self.api_secret = config.binance['api_secret']

        self.client = Client(self.api_key, self.api_secret)

    def placeBuyOrder(self, params):
        symbol = params["symbol"]
        buyRange = params["buy_range"]
        sellTargets = params["sell_targets"]
        stopLoss = params["stop_loss"]

        info = self.client.get_ticker(symbol=symbol)
        lastPrice = info['lastPrice']

        print(symbol, buyRange, sellTargets, stopLoss, lastPrice)

    def placeSellTargetOrders(self, sym, sell_range):
        print(sym)
