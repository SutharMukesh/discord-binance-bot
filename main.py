from module import BinanceUtils, DiscordScraper, MongoUtils
from os import getcwd, path
from json import loads


def getConfigFile(configfile):
    # Generate a direct file path to the configuration file.
    configfile = path.join(getcwd(), configfile)

    # Throw an error if the configuration file doesn't exist.
    if not path.exists(configfile):
        DiscordScraper.error('Configuration file can not be found at the following location: {0}'.format(
            configfile))

    # Open the config file in text-mode for reading.
    with open(configfile, 'r') as configfilestream:

        # Read the entire config file.
        configfiledata = configfilestream.read()

    # Convert the serialized JSON contents of the configuration file into a dictionary.
    configdata = loads(configfiledata)

    # Convert the configuration dictionary into a class object.
    config = type('DiscordConfig', (object, ), configdata)()
    return config


if __name__ == '__main__':
    """
    This is the entrypoint for our script since __name__ is going to be set to __main__ by default.
    """

    config = getConfigFile('config.json')

    # Create a variable that references the Discord Scraper class.
    discordscraper = DiscordScraper(config)
    mongoUtils = MongoUtils(config)
    binanceUtils = BinanceUtils(config)
    # Iterate through the servers to scrape.
    for server, channels in discordscraper.servers.items():

        # Iterate through the channels to scrape in the server.
        for channel in channels:
            '''
             Get "bought=False and is_placed=True" records from mongo.
             Check if these records are bought on binance
             if Bought then update as bought=True
             then put the OCO sell order with stoploss
             update OCO_placed=True
            '''

            # GET Last message from the channel
            lastMessage = discordscraper.getLastMessageServer(server, channel)

            # Check if that message is from admin/ or the author which gives us signals.
            adminMessage = discordscraper.filterMessageFromAdmins(lastMessage)
            if not adminMessage:
                print(
                    f"Message is not from admin, ignoring {lastMessage['content']}")
                continue

            # Parse the message
            messageContent = adminMessage['content']
            authorId = adminMessage['author']['id']
            doc = discordscraper.parseSignalCalls(messageContent, authorId)
            doc = binanceUtils.adjustSignalCallsDigits(doc)
            doc['timestamp'] = adminMessage['timestamp']
            doc['msg_id'] = adminMessage['id']
            doc['is_active'] = True
            doc['bought'] = False

            # B4 placing buy order, we insert this doc to mongo, just so we know that this signal was attempted
            inserted_doc = mongoUtils.insertSignals(doc)

            # Place Buy order
            binanceParams = {
                "symbol": doc['symbol'] + doc['base_curr'],
                "buy_range": {
                    "low": float(doc['buy_low']),
                    "high": float(doc['buy_high'])
                },
                "sell_targets": {
                    "t1": float(doc["t1"]),
                    "t2": float(doc["t2"]),
                    "t3": float(doc["t3"]),
                    "t4": float(doc["t4"]),
                },
                "stop_loss": float(doc['stop_loss'])
            }

            binance_res = binanceUtils.placeBuyOrder(binanceParams)

            # if order is not bought, and the order is open; then update mongo with bought=False and exit
            if not binance_res['bought']:
                mongoUtils.updateSignal(inserted_doc['_id'], {
                    "bought": False
                })
                continue

            # If order is closed and bought, then update mongo with bought=True
            doc['bought'] = True
            mongoUtils.updateSignal(inserted_doc['_id'], {
                "bought": True
            })

            # Place OCO with stop loss

            # Update mongo as oco_placed=true
