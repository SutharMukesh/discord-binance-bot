from binance import Client
from .SystemUtils import warn
BINANCE_BTC_BASE_DIGITS = 0.00000001


class BinanceUtils(object):
    """
    This class will contain all of the important functions that will be used that works with both Python 2 and Python 3 interpreters.
    """

    def __init__(self, config):
        self.api_key = config.binance['api_key']
        self.api_secret = config.binance['api_secret']

        self.client = Client(self.api_key, self.api_secret)

    def adjustSignalCallsDigits(self, doc):
        """
            ! This function only adjust BTC based signals !
            Normally the signals tend to give only the trailing number from a price
            for eg: 0.00000633 -> 633
            So this will readjust the digits given by signal from 633 -> 0.00000633
            if the btc_price > 1, assuming here the signal will never exceed 1btc.
        """
        supportedSignalKeywords = [
            'buy_low', 'buy_high', 't1', 't2', 't3', 't4', 'stop_loss']

        if doc['base_curr'] == 'BTC':
            for keyword in doc:
                if keyword in supportedSignalKeywords:
                    if int(doc[keyword]) < 1:
                        warn(
                            f'cannot adjust {keyword}: {doc[keyword]} as it is < 1')
                        continue
                    doc[keyword] = BINANCE_BTC_BASE_DIGITS * int(doc[keyword])
        return doc

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
