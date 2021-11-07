from binance import Client
from .SystemUtils import warn, error
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
        self.oco_targets = config.oco_targets

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
        return float(info['price'])

    def isItBuyable(self, symbol, currentPrice, sellTargets, stopLoss):
        symbolInfo = self.client.get_symbol_info(symbol=symbol)

        minNotional = list(filter(
            lambda x: x['filterType'] == 'MIN_NOTIONAL', symbolInfo['filters']))
        minAllowedSellPrice = float(minNotional[0]['minNotional'])

        for target in self.oco_targets:
            quantityToBePurchased = self.single_buy_order_amount_in_btc/currentPrice
            targetQuantity = self.oco_targets[target] * quantityToBePurchased

            sellTarget = sellTargets[target] * targetQuantity
            stopLossTarget = stopLoss * targetQuantity

            if sellTarget < minAllowedSellPrice:
                raise Exception(
                    f'Symbol: "{symbol}" is not buyable, as sell target price for target: {target} - {format(sellTargets[target], ".8f")}, quantity: {targetQuantity}, sell_total_price: {format(sellTarget, ".8f")} < min_allowed_sell_price: {minAllowedSellPrice}')

            if stopLossTarget < minAllowedSellPrice:
                raise Exception(
                    f'Symbol: "{symbol}" is not buyable, as stop loss target price for target: {target} - {format(stopLoss, ".8f")}, quantity: {targetQuantity}, stop_loss_total_price: {format(stopLossTarget, ".8f")} < min_allowed_sell_price: {minAllowedSellPrice}')

    def placeBuyOrder(self, doc):
        symbol = doc['symbol'] + doc['base_curr']

        symbolCurrentPrice = self.getCurrentPrice(symbol)

        self.isItBuyable(
            symbol=symbol, currentPrice=symbolCurrentPrice, sellTargets=doc, stopLoss=doc['stop_loss'])

        order = None
        if symbolCurrentPrice <= doc['buy_low'] or symbolCurrentPrice >= doc['buy_high']:
            raise Exception(
                f'Buy order not placed for "{symbol}" as currentPrice: {format(symbolCurrentPrice, ".8f")} is out of buy range: {format(doc["buy_low"], ".8f")} - {format(doc["buy_high"], ".8f")}')

        buy_quantity = int(
            self.single_buy_order_amount_in_btc / float(symbolCurrentPrice))

        print(
            f'[BUY] placing buy order for "{symbol}", at currentPrice: {format(symbolCurrentPrice, ".8f")} for quantity {buy_quantity}')

        order = self.client.create_order(
            symbol=symbol,
            side=self.client.SIDE_BUY,
            type=self.client.ORDER_TYPE_MARKET,
            quantity=buy_quantity)

        # MARKET BUY RESPONSE
        # {'symbol': 'XLMBTC', 'orderId': 337069143, 'orderListId': -1, 'clientOrderId': 'ExXyc0Pe5fxbGq2JQOiMb0', 'transactTime': 1634473285073, 'price': '0.00000000', 'origQty': '28.00000000', 'executedQty': '28.00000000', 'cummulativeQuoteQty': '0.00017696', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'BUY', 'fills': [{'price': '0.00000632', 'qty': '28.00000000', 'commission': '0.00001721', 'commissionAsset': 'BNB', 'tradeId': 49295215}]}

        # LIMIT BUY RESPONSE
        # {'symbol': 'XLMBTC', 'orderId': 337068806, 'orderListId': -1, 'clientOrderId': 'PfRtJWgdB7Yq80vqxsxUVN', 'transactTime': 1634473116012, 'price': '0.00000630', 'origQty': '28.00000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY', 'fills': []}

        # print(order)
        return order

    def placeMarketSellOrder(self, doc, quantityPurchased):
        symbol = doc['symbol'] + doc['base_curr']
        order = self.client.create_order(
            symbol=symbol,
            side=self.client.SIDE_SELL,
            type=self.client.ORDER_TYPE_MARKET,
            quantity=quantityPurchased)
        return order

    def placeOCOSellOrdersForAllTargets(self, doc, quantityPurchased):
        """
        Place OCO sell orders for top 3 targets given in signals
        Sell distribution is 25-50-20
        """

        symbol = doc['symbol'] + doc['base_curr']

        stop_loss = format(doc['stop_loss'], '.8f')
        try:
            oco_responses = []
            for target in self.oco_targets:
                quantity = self.oco_targets[target] * quantityPurchased
                sell_target = format(doc[target], '.8f')

                stop_price = format(float(stop_loss) +
                                    (float(stop_loss)*0.01), '.8f')
                print(
                    f'[SELL-OCO] Symbol: "{symbol}" at sell_price: {sell_target}, quantity: {quantity}, stop_price: {stop_price}, stop_loss: {stop_loss}')

                order = self.client.create_oco_order(
                    symbol=symbol,
                    side=self.client.SIDE_SELL,
                    price=sell_target,
                    quantity=quantity,
                    stopPrice=str(stop_price),
                    stopLimitPrice=stop_loss,
                    stopLimitTimeInForce=self.client.TIME_IN_FORCE_GTC)

                oco_responses.append(order)
        except Exception as e:
            error(e)
            print(
                f'[SELL-MARKET] selling symbol: "{symbol}" at market price for quantity: {quantityPurchased}')
            self.placeMarketSellOrder(doc, quantityPurchased)

        return oco_responses
