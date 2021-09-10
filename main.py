from module import DiscordScraper
from module.DiscordScraper import loads
import json


def getLastMessageGuild(scraper, guild, channel):
    """
    Use the official Discord API to retrieve the last publicly viewable message in a channel.
    :param scraper: The DiscordScraper class reference that we will be using.
    :param guild: The ID for the guild that we're wanting to scrape from.
    :param channel: The ID for the channel that we're wanting to scrape from.
    """

    # Generate a valid URL to the documented API function for retrieving channel messages (we don't care about the 100 message limit this time).
    lastmessage = 'https://discord.com/api/{0}/channels/{1}/messages?limit=1'.format(
        scraper.apiversion, channel)

    # Update the HTTP request headers to set the referer to the current guild channel URL.
    scraper.headers.update(
        {'Referer': 'https://discord.com/channels/{0}/{1}'.format(guild, channel)})

    try:
        # Execute the network query to retrieve the JSON data.
        response = DiscordScraper.requestData(lastmessage, scraper.headers)

        # If we returned nothing then return nothing.
        if response is None:
            return None

        # Read the response data and convert it into a dictionary object.
        data = loads(response.read())

        return data
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    """
    This is the entrypoint for our script since __name__ is going to be set to __main__ by default.
    """

    # Create a variable that references the Discord Scraper class.
    discordscraper = DiscordScraper()

    # Iterate through the guilds to scrape.
    for guild, channels in discordscraper.guilds.items():

        # Iterate through the channels to scrape in the guild.
        for channel in channels:

            # Retrieve the datetime object for the most recent post in the channel.
            lastMessage = getLastMessageGuild(discordscraper, guild, channel)
            print(json.dumps(lastMessage, indent=4))

            adminMessage = discordscraper.filterMessageFromAdmins(lastMessage)

            print(adminMessage)
