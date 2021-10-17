from sys import stderr
from os import getcwd, path
from os import _exit as exit
from signal import SIGINT, signal
import json
import re

from .Request import DiscordRequest


def sigintEvent(sig, frame):
    print('You pressed CTRL + C')
    exit(0)


signal(SIGINT, sigintEvent)


def error(message):
    """
    Throw an error message and then halt the script.
    :param message: A string that will be printed out to STDERR before exiting the script.
    """

    # Append our message with a newline character.
    stderr.write('[ERROR]: {0}\n'.format(message))

    # Halt the script right here, do not continue running the script after this point.
    exit(1)


def warn(message):
    """
    Throw a warning message without halting the script.
    :param message: A string that will be printed out to STDERR.
    """

    # Append our message with a newline character.
    stderr.write('[WARN] {0}\n'.format(message))


class DiscordConfig(object):
    """
    This class will only serve the purpose of converting a dictionary object into a class object.
    """


class DiscordScraper(object):
    """
    This class will contain all of the important functions that will be used that works with both Python 2 and Python 3 interpreters.
    """

    def __init__(self, config, apiversion=None):
        """
        The class constructor function that is not needed for calling any of the static functions.
        :param self: A reference to the class object that will be used to call any non-static functions in this class.
        :param configfile: The configuration file that this script will rely on to function as it's supposed to, if one isn't given then it will use the default value.
        :param apiversion: The API version that Discord uses for its backend, this is currently set to "v8" as of November 2020.
        """

        # Determine if the apiversion argument is not set.
        if apiversion is None:

            # Set it to the default value of "v8"
            apiversion = 'v8'

        # Generate a direct file path to the authorization token file.
        tokenfile = path.join(getcwd(), config.token_file)

        # Throw an error if the authorization token file doesn't exist.
        if not path.exists(tokenfile):
            error('Authorization token file can not be found at the following location: {0}'.format(
                tokenfile))

        # Open the authorization token file in text-mode for reading.
        with open(tokenfile, 'r') as tokenfilestream:

            # Read the first line of the authorization token file.
            tokenfiledata = tokenfilestream.readline().rstrip()

        # Create a dictionary to store the HTTP request headers that we will be using for all requests.
        self.headers = {
            # The user-agent string that tells the server which browser, operating system, and rendering engine we're using.
            'User-Agent': config.useragent,
            'Authorization': tokenfiledata     # The authorization token that authorizes this script to carry out actions with your account, this script only requires this to access the data on the specified servers and channels for scraping purposes. NEVER UNDER ANY CIRCUMSTANCE SHARE THIS VALUE TO ANYONE YOU DO NOT TRUST!
        }

        # Create some class variables to store the configuration file data.
        # The backend Discord API version which denotes which API functions are available for use and which are deprecated.
        self.apiversion = apiversion
        # The file download buffer that will be stored in memory before offloading to the hard drive.
        self.buffersize = config.buffer
        # The experimental options portion of the configuration file that will give extra control over how the script functions.
        self.options = config.options
        # The file types that we are wanting to scrape and download to our storage device.
        self.types = config.types

        # Make the options available for quick and easy access.
        # The option that will not only check the MIME type of a file but go one step further and check the magic number (header) of the file.
        self.validateFileHeaders = config.options['validateFileHeaders']
        # The option that will generate a document listing off generated checksums for each file that was scraped for duplicate detection.
        self.generateFileChecksums = config.options['generateFileChecksums']
        # The option that will rename files and folders to avoid as many problems with filesystem and reserved file names in most operating systems.
        self.sanitizeFileNames = config.options['sanitizeFileNames']
        # The option that will enable image file compression to save on storage space when downloading data, this will likely be a generic algorithm.
        self.compressImageData = config.options['compressImageData']
        # The option that will enable textual data compression to save on storage space when downloading data, this will most likely be GZIP compression.
        self.compressTextData = config.options['compressTextData']
        # The option that will determine whether or not the script should cache the response text in JSON formatting.
        self.gatherJSONData = config.options['gatherJSONData']

        self.author_ids = config.author_ids

        self.templates = config.templates

        self.servers = config.servers if len(config.servers) > 0 else {}

        # Create a blank server name, channel name, and folder location class variable.
        self.servername = None
        self.channelname = None
        self.location = None

    @staticmethod
    def requestData(url, headers=None):
        """
        Make a simplified alias to the Discord Requests sendRequest class function.
        :param url: The URL that we want to grab data from.
        :param headers: The headers dictionary that we want to set.
        """

        # Determine if the headers are empty, if so then use an empty dictionary.
        if headers is None:
            headers = {}

        # Create a request variable.
        request = DiscordRequest()

        # Set the headers.
        request.setHeaders(headers)

        # Return the response.
        return request.sendRequest(url)

    def getLastMessageServer(self, server, channel):
        """
        Use the official Discord API to retrieve the last publicly viewable message in a channel.
        :param server: The ID for the server that we're wanting to scrape from.
        :param channel: The ID for the channel that we're wanting to scrape from.
        """

        # Generate a valid URL to the documented API function for retrieving channel messages (we don't care about the 100 message limit this time).
        lastmessage = 'https://discord.com/api/{0}/channels/{1}/messages?limit=3'.format(
            self.apiversion, channel)

        # Update the HTTP request headers to set the referer to the current server channel URL.
        self.headers.update(
            {'Referer': 'https://discord.com/channels/{0}/{1}'.format(server, channel)})

        try:
            # Execute the network query to retrieve the JSON data.
            response = self.requestData(lastmessage, self.headers)

            # If we returned nothing then return nothing.
            if response is None:
                return None

            # Read the response data and convert it into a dictionary object.
            data = json.loads(response.read())

            return data[-1]
        except Exception as ex:
            print(ex)

    def filterMessageFromAdmins(self, message):
        """
        return the same message, if its from admin or else it returns None
        :param message: object or list<object> of discord message
        """

        def isMessageFromAdmin(msg):
            author = msg['author']['id']
            if(author in self.author_ids):
                return True
            else:
                return False

        if (isinstance(message, list)):
            filtered_messages = []
            for msg in message:
                if(isMessageFromAdmin(msg)):
                    filtered_messages.append(msg)

            return None if (len(filtered_messages) == 0) else filtered_messages

        if(isMessageFromAdmin(message)):
            return message
        else:
            return None

    def matchDataUsingTemplate(self, template, message):
        pattern = re.escape(template)
        pattern = re.sub(r'\\\$(\w+)', r'(?P<\1>.*)', pattern)
        match = re.match(pattern, message)
        return match.groupdict()

    def parseSignalCalls(self, message, authorId):
        """
        Parse a message with the configured template against a admin id
        :param message: a message to be parsed
        :return: parsed json
        """

        if authorId not in self.templates.keys():
            return None

        # Supporting multiple templates, as admin/author can send a message in different formats.
        templates = self.templates[authorId]
        parsedMessage = None
        for template in templates:
            try:
                parsedMessage = self.matchDataUsingTemplate(template, message)
                break
            except Exception as e:
                warn(
                    f'Template: {json.dumps(template)} doesn\'t work for message: {json.dumps(message)}; error: {e}')

        if not parsedMessage:
            raise Exception(f'No template matched for message: {json.dumps(message)}')

        return parsedMessage
