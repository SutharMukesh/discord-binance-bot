from module import DiscordScraper
import json


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
