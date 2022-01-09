import json

from module import BinanceUtils, DiscordUtils, MongoUtils, Logger, CommonUtils


def start():
    config = CommonUtils.get_config_file('config.json')
    logger = Logger(config)

    # Initialize all modules

    discord_utils = DiscordUtils(config, logger)
    mongo_utils = MongoUtils(config)
    binance_utils = BinanceUtils(config, logger)

    # Iterate through the signal_servers.
    for server_obj in discord_utils.signal_servers:
        server_id = server_obj['server_id']
        headers = server_obj['headers']
        channels = server_obj['channels']

        # Iterate through the channels to scrape in the server.
        for channel_obj in channels:
            channel_id = channel_obj['channel_id']
            author_ids = channel_obj['author_ids']
            oco_targets = channel_obj['oco_targets']

            try:
                '''
                Get "bought=False and is_placed=True" records from mongo.
                Check if these records are bought on binance
                if Bought then update as bought=True
                then put the OCO sell order with stop_loss
                update OCO_placed=True
                '''

                # GET Last message from the channel
                last_message = discord_utils.get_last_message_server(
                    server_id, channel_id, headers)

                # Check if that message is from admin/ or the author which gives us signals.
                admin_message = discord_utils.filter_message_from_admins(
                    last_message, author_ids)
                if not admin_message:
                    print(
                        f"Message is not from admin, ignoring {last_message['content']}")
                    continue

                # Parse the message
                message_content = admin_message['content']
                author_id = admin_message['author']['id']
                author_username = admin_message['author']['username']

                logger.info(f"[PICKED-UP] Message from author: {author_username}", message_content)

                # Filter message templates for current author id.
                message_templates = list(filter(lambda x: x['author_id'] == author_id, author_ids))[0][
                    'message_templates']

                doc = discord_utils.parse_signal_calls(message_content, message_templates)
                doc = binance_utils.adjust_signal_calls_digits(doc)
                doc = binance_utils.re_adjust_buy_range(doc)

                # B4 placing buy order, we insert this doc to mongo, just so we know that this signal was attempted
                doc['timestamp'] = admin_message['timestamp']
                doc['msg_id'] = admin_message['id']
                doc['is_active'] = True
                inserted_doc = mongo_utils.insert_signals(doc)

                # Place Buy order
                binance_res = binance_utils.place_buy_order(doc, oco_targets)

                logger.info(f"[{binance_res['symbol']}] (BOUGHT) ", json.dumps(binance_res['fills']))

                # Update the binance buy order response.
                mongo_utils.update_signal(inserted_doc['_id'], {
                    "binance_res": binance_res
                })

                if len(binance_res['fills']) > 0:
                    # Order has been placed
                    quantity_purchased = float(binance_res['executedQty'])

                    # Place OCO with stop loss
                    try:
                        sell_oco_response = binance_utils.place_oco_sell_orders_for_all_targets(
                            doc, quantity_purchased, oco_targets)

                        mongo_utils.update_signal(inserted_doc['_id'], {
                            "sell_oco_response": sell_oco_response
                        })

                        logger.info(
                            f"[{binance_res['symbol']}] (OCO-PLACED)", json.dumps(sell_oco_response))

                    except Exception as e:
                        logger.error(f"[{binance_res['symbol']}] (OCO-ERROR)", str(e))
                        logger.info(
                            f"[{binance_res['symbol']}] (SELL-MARKET)",
                            f"at market price for quantity: {quantity_purchased}")

                        sell_order = binance_utils.place_market_sell_order(doc, quantity_purchased)
                        logger.info(
                            f"[{binance_res['symbol']}] (SOLD-MARKET)",
                            f"at market price for quantity: {quantity_purchased}, order: {sell_order}")

            except Exception as e:
                logger.error("🔴 ☠️ (ERROR) ☠️ 🔴", str(e))


if __name__ == '__main__':
    """
    This is the entrypoint for our script since __name__ is going to be set to __main__ by default.
    """
    start()
