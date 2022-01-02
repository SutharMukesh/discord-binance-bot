from binance import Client
from .SystemUtils import warn, error
BINANCE_BTC_BASE_DIGITS = 0.00000001


class BinanceUtils(object):
    """
    This class talks with binance server.
    """

    def __init__(self, config):
        self.api_key = config.binance['api_key']
        self.api_secret = config.binance['api_secret']
        self.single_buy_order_amount_in_btc = config.binance['single_buy_order_amount_in_btc']

        self.client = Client(self.api_key, self.api_secret)
        self.oco_targets = config.oco_targets

    @staticmethod
    def adjust_signal_calls_digits(doc):
        """
            ! This function only adjust BTC based signals !
            Normally the signals tend to give only the trailing number from a price
            for eg: 0.00000633 -> 633
            So this will readjust the digits given by signal from 633 -> 0.00000633
            if the btc_price > 1, assuming here the signal will never exceed 1btc.
        """
        supported_signal_keywords = [
            'buy_range_1', 'buy_range_2', 't1', 't2', 't3', 't4', 'stop_loss']

        if doc['base_curr'] == 'BTC':
            for keyword in doc:
                if keyword in supported_signal_keywords:
                    if int(doc[keyword]) < 1:
                        warn(
                            f'cannot adjust {keyword}: {doc[keyword]} as it is < 1')
                        continue
                    doc[keyword] = BINANCE_BTC_BASE_DIGITS * int(doc[keyword])
        return doc

    @staticmethod
    def re_adjust_buy_range(doc):
        buy_range1 = doc['buy_range_1']
        buy_range2 = doc['buy_range_2']

        if buy_range1 < buy_range2:
            doc['buy_low'] = buy_range1
            doc['buy_high'] = buy_range2
        else:
            doc['buy_low'] = buy_range2
            doc['buy_high'] = buy_range1

        return doc

    def get_current_price(self, symbol):
        info = self.client.get_symbol_ticker(symbol=symbol)
        return float(info['price'])

    def can_we_buy_it(self, symbol, current_price, sell_targets, stop_loss):
        symbol_info = self.client.get_symbol_info(symbol=symbol)

        min_notional = list(filter(
            lambda x: x['filterType'] == 'MIN_NOTIONAL', symbol_info['filters']))
        min_allowed_sell_price = float(min_notional[0]['minNotional'])

        for target in self.oco_targets:
            quantity_to_be_purchased = self.single_buy_order_amount_in_btc / current_price
            target_quantity = self.oco_targets[target] * quantity_to_be_purchased

            sell_target = sell_targets[target] * target_quantity
            stop_loss_target = stop_loss * target_quantity

            if sell_target < min_allowed_sell_price:
                raise Exception(
                    f'Symbol: "{symbol}" is not bought!, '
                    f'as sell target price for target: {target} - {format(sell_targets[target], ".8f")}, '
                    f'quantity: {target_quantity}, '
                    f'sell_total_price: '
                    f'{format(sell_target, ".8f")} < min_allowed_sell_price: {min_allowed_sell_price}')

            if stop_loss_target < min_allowed_sell_price:
                raise Exception(
                    f'Symbol: "{symbol}" is not bought, '
                    f'as stop loss target price for target: {target} - {format(stop_loss, ".8f")}, '
                    f'quantity: {target_quantity}, '
                    f'stop_loss_total_price: '
                    f'{format(stop_loss_target, ".8f")} < min_allowed_sell_price: {min_allowed_sell_price}')

    def place_buy_order(self, doc):
        symbol = doc['symbol'] + doc['base_curr']

        symbol_current_price = self.get_current_price(symbol)

        self.can_we_buy_it(
            symbol=symbol, current_price=symbol_current_price, sell_targets=doc, stop_loss=doc['stop_loss'])

        if symbol_current_price <= doc['buy_low'] or symbol_current_price >= doc['buy_high']:
            raise Exception(
                f'Buy order not placed for "{symbol}" '
                f'as currentPrice: {format(symbol_current_price, ".8f")} '
                f'is out of buy range: {format(doc["buy_low"], ".8f")} - {format(doc["buy_high"], ".8f")}')

        buy_quantity = int(
            self.single_buy_order_amount_in_btc / float(symbol_current_price))

        print(
            f'[BUY] placing buy order for "{symbol}", '
            f'at currentPrice: {format(symbol_current_price, ".8f")} for quantity {buy_quantity}')

        order = self.client.create_order(
            symbol=symbol,
            side=self.client.SIDE_BUY,
            type=self.client.ORDER_TYPE_MARKET,
            quantity=buy_quantity)

        # MARKET BUY RESPONSE {'symbol': 'XLMBTC', 'orderId': 337069143, 'orderListId': -1, 'clientOrderId':
        # 'ExXyc0Pe5fxbGq2JQOiMb0', 'transactTime': 1634473285073, 'price': '0.00000000', 'origQty': '28.00000000',
        # 'executedQty': '28.00000000', 'cummulativeQuoteQty': '0.00017696', 'status': 'FILLED', 'timeInForce':
        # 'GTC', 'type': 'MARKET', 'side': 'BUY', 'fills': [{'price': '0.00000632', 'qty': '28.00000000',
        # 'commission': '0.00001721', 'commissionAsset': 'BNB', 'tradeId': 49295215}]}

        # LIMIT BUY RESPONSE {'symbol': 'XLMBTC', 'orderId': 337068806, 'orderListId': -1, 'clientOrderId':
        # 'PfRtJWgdB7Yq80vqxsxUVN', 'transactTime': 1634473116012, 'price': '0.00000630', 'origQty': '28.00000000',
        # 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC',
        # 'type': 'LIMIT', 'side': 'BUY', 'fills': []}

        # print(order)
        return order

    def place_market_sell_order(self, doc, quantity_purchased):
        symbol = doc['symbol'] + doc['base_curr']
        order = self.client.create_order(
            symbol=symbol,
            side=self.client.SIDE_SELL,
            type=self.client.ORDER_TYPE_MARKET,
            quantity=quantity_purchased)
        return order

    def place_oco_sell_orders_for_all_targets(self, doc, quantity_purchased):
        """
        Place OCO sell orders for top 3 targets given in signals
        Sell distribution is 25-50-20
        """

        symbol = doc['symbol'] + doc['base_curr']

        stop_loss = format(doc['stop_loss'], '.8f')
        oco_responses = []
        try:
            for target in self.oco_targets:
                quantity = self.oco_targets[target] * quantity_purchased
                sell_target = format(doc[target], '.8f')

                stop_price = format(float(stop_loss) +
                                    (float(stop_loss)*0.01), '.8f')
                print(
                    f'[SELL-OCO] Symbol: "{symbol}" at sell_price: {sell_target}, '
                    f'quantity: {quantity}, stop_price: {stop_price}, stop_loss: {stop_loss}')

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
                f'[SELL-MARKET] selling symbol: "{symbol}" at market price for quantity: {quantity_purchased}')
            self.place_market_sell_order(doc, quantity_purchased)

        return oco_responses
