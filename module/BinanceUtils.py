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
        self.single_buy_order_amount_in_btc = config.binance['single_buy_order_amount_in_btc']

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
            'buy_range_1', 'buy_range_2', 't1', 't2', 't3', 't4', 'stop_loss']

        if doc['base_curr'] == 'BTC':
            for keyword in doc:
                if keyword in supportedSignalKeywords:
                    if int(doc[keyword]) < 1:
                        warn(
                            f'cannot adjust {keyword}: {doc[keyword]} as it is < 1')
                        continue
                    doc[keyword] = BINANCE_BTC_BASE_DIGITS * int(doc[keyword])
        return doc

    def reAdjustBuyRange(self, doc):
        buyRange1 = doc['buy_range_1']
        buyRange2 = doc['buy_range_2']

        if buyRange1 < buyRange2:
            doc['buy_low'] = buyRange1
            doc['buy_high'] = buyRange2
        else:
            doc['buy_low'] = buyRange2
            doc['buy_high'] = buyRange1

        return doc

    def getCurrentPrice(self, symbol):
        info = self.client.get_symbol_ticker(symbol=symbol)
        return info['price']

    def placeBuyOrder(self, doc):
        symbol = doc['symbol'] + doc['base_curr']

        symbolCurrentPrice = self.getCurrentPrice(symbol)
        order = None

        # if symbolCurrentPrice >= doc['buy_low'] and symbolCurrentPrice <= doc['buy_high']:
        buy_quantity = int(
            self.single_buy_order_amount_in_btc / float(symbolCurrentPrice))

        print(
            f'[BUY] placing buy order for {symbol}, at currentPrice: {symbolCurrentPrice} for quantity {buy_quantity}')

        order = self.client.create_order(
            symbol=symbol,
            side=self.client.SIDE_BUY,
            type=self.client.ORDER_TYPE_MARKET,
            quantity=buy_quantity)

        # MARKET BUY RESPONSE
        # {'symbol': 'XLMBTC', 'orderId': 337069143, 'orderListId': -1, 'clientOrderId': 'ExXyc0Pe5fxbGq2JQOiMb0', 'transactTime': 1634473285073, 'price': '0.00000000', 'origQty': '28.00000000', 'executedQty': '28.00000000', 'cummulativeQuoteQty': '0.00017696', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'BUY', 'fills': [{'price': '0.00000632', 'qty': '28.00000000', 'commission': '0.00001721', 'commissionAsset': 'BNB', 'tradeId': 49295215}]}

        # LIMIT BUY RESPONSE
        # {'symbol': 'XLMBTC', 'orderId': 337068806, 'orderListId': -1, 'clientOrderId': 'PfRtJWgdB7Yq80vqxsxUVN', 'transactTime': 1634473116012, 'price': '0.00000630', 'origQty': '28.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'fills': []}

        print(order)
        return order

    def placeSellTargetOrders(self, sym, sell_range):
        print(sym)
