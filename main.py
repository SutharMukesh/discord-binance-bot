from module import BinanceUtils, DiscordScraper, MongoUtils, SystemUtils
from os import getcwd, path
from json import loads, dumps


def get_config_file(configfile):
    # Generate a direct file path to the configuration file.
    configfile = path.join(getcwd(), configfile)

    # Throw an error if the configuration file doesn't exist.
    if not path.exists(configfile):
        SystemUtils.error('Configuration file can not be found at the following location: {0}'.format(
            configfile))

    # Open the config file in text-mode for reading.
    with open(configfile, 'r') as config_file_stream:

        # Read the entire config file.
        config_file_data = config_file_stream.read()

    # Convert the serialized JSON contents of the configuration file into a dictionary.
    config_data = loads(config_file_data)

    # Convert the configuration dictionary into a class object.
    config = type('DiscordConfig', (object, ), config_data)()
    return config


def start():
    config = get_config_file('config.json')

    # Create a variable that references the Discord Scraper class.
    discord_scraper = DiscordScraper(config)
    mongo_utils = MongoUtils(config)
    binance_utils = BinanceUtils(config)
    # Iterate through the servers to scrape.
    for server, channels in discord_scraper.servers.items():

        # Iterate through the channels to scrape in the server.
        for channel in channels:
            try:
                '''
                Get "bought=False and is_placed=True" records from mongo.
                Check if these records are bought on binance
                if Bought then update as bought=True
                then put the OCO sell order with stop_loss
                update OCO_placed=True
                '''

                # GET Last message from the channel
                last_message = discord_scraper.get_last_message_server(
                    server, channel)

                # Check if that message is from admin/ or the author which gives us signals.
                admin_message = discord_scraper.filter_message_from_admins(
                    last_message)
                if not admin_message:
                    print(
                        f"Message is not from admin, ignoring {last_message['content']}")
                    continue

                # Parse the message
                message_content = admin_message['content']
                author_id = admin_message['author']['id']

                discord_scraper.send_message_to_stat_server(
                    "Message from admin: {} picked up!".format(author_id), message_content)

                doc = discord_scraper.parse_signal_calls(message_content, author_id)
                doc = binance_utils.adjust_signal_calls_digits(doc)
                doc = binance_utils.re_adjust_buy_range(doc)

                # B4 placing buy order, we insert this doc to mongo, just so we know that this signal was attempted
                doc['timestamp'] = admin_message['timestamp']
                doc['msg_id'] = admin_message['id']
                doc['is_active'] = True
                inserted_doc = mongo_utils.insert_signals(doc)

                # Place Buy order
                binance_res = binance_utils.place_buy_order(doc)

                discord_scraper.send_message_to_stat_server(
                    f"[{binance_res['symbol']}] Buy order placed!", dumps(binance_res['fills']))

                # Update the binance buy order response.
                mongo_utils.update_signal(inserted_doc['_id'], {
                    "binance_res": binance_res
                })

                if len(binance_res['fills']) > 0:
                    # Order has been placed
                    quantity_purchased = float(binance_res['executedQty'])

                    # Place OCO with stop loss
                    sell_oco_response = binance_utils.place_oco_sell_orders_for_all_targets(
                        doc, quantity_purchased)

                    discord_scraper.send_message_to_stat_server(
                        f"[{binance_res['symbol']}] OCO placed!", dumps(sell_oco_response))

                    mongo_utils.update_signal(inserted_doc['_id'], {
                        "sell_oco_response": sell_oco_response
                    })

            except Exception as e:
                discord_scraper.send_message_to_stat_server(
                    "🔴 ☠️ [ERROR] ☠️ 🔴", str(e))

                SystemUtils.error(e)


if __name__ == '__main__':
    """
    This is the entrypoint for our script since __name__ is going to be set to __main__ by default.
    """
    start()
