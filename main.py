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

    # Iterate through the guilds to scrape.
    for guild, channels in discordscraper.guilds.items():

        # Iterate through the channels to scrape in the guild.
        for channel in channels:

            # Retrieve the datetime object for the most recent post in the channel.
            lastMessage = discordscraper.getLastMessageGuild(guild, channel)

            adminMessage = discordscraper.filterMessageFromAdmins(lastMessage)

            if not adminMessage:
                continue

            messageContent = adminMessage['content']
            authorId = adminMessage['author']['id']

            doc = discordscraper.parseSignalCalls(messageContent, authorId)
            doc['timestamp'] = adminMessage['timestamp']
            doc['msg_id'] = adminMessage['id']

            print(doc)
