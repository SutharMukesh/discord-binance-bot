import json
import re
import requests

from .Request import DiscordRequest
from .SystemUtils import error, warn


class DiscordScraper(object):
    """
    This class talks with discord servers.
    """

    def __init__(self, config, api_version=None):
        """
        The class constructor function that is not needed for calling any of the static functions.
        :param self: A reference to the class object that will be used to call any non-static functions in this class.
        :param config: The configuration file that this script will rely on to function as it's supposed to,
                if one isn't given then it will use the default value.
        :param api_version: The API version that Discord uses for its backend,
                this is currently set to "v8" as of November 2020.
        """

        # Determine if the api_version argument is not set.
        if api_version is None:

            # Set it to the default value of "v8"
            api_version = 'v8'

        # Create a dictionary to store the HTTP request headers that we will be using for all requests.
        self.headers = config.discord['headers']

        # Create some class variables to store the configuration file data. The backend Discord API version which
        # denotes which API functions are available for use and which are deprecated.
        self.api_version = api_version
        # The experimental options portion of the configuration file
        # that will give extra control over how the script functions.
        self.options = config.options
        # The file types that we are wanting to scrape and download to our storage device.
        self.types = config.types

        # Make the options available for quick and easy access.
        # The option that will not only check the MIME type of file
        # but go one step further and check the magic number (header) of the file.
        self.validateFileHeaders = config.options['validateFileHeaders']
        # The option that will generate a document listing off generated checksums
        # for each file that was scraped for duplicate detection.
        self.generateFileChecksums = config.options['generateFileChecksums']
        # The option that will rename files and folders to avoid as many problems
        # with filesystem and reserved file names in most operating systems.
        self.sanitizeFileNames = config.options['sanitizeFileNames']
        # The option that will enable image file compression to save on storage space when downloading data,
        # this will likely be a generic algorithm.
        self.compressImageData = config.options['compressImageData']
        # The option that will enable textual data compression to save on storage space when downloading data,
        # this will most likely be GZIP compression.
        self.compressTextData = config.options['compressTextData']
        # The option that will determine whether the script should cache the response text in JSON formatting.
        self.gatherJSONData = config.options['gatherJSONData']

        self.author_ids = config.author_ids

        self.templates = config.templates

        self.servers = config.servers if len(config.servers) > 0 else {}

        self.stats_server = config.stats_server
        # Create a blank server name, channel name, and folder location class variable.
        self.server_name = None
        self.channel_name = None
        self.location = None

    @staticmethod
    def request_data(url, headers=None):
        """
        Make a simplified alias to the Discord Requests send_request class function.
        :param url: The URL that we want to grab data from.
        :param headers: The header's dictionary that we want to set.
        """

        # Determine if the headers are empty, if so then use an empty dictionary.
        if headers is None:
            headers = {}

        # Create a request variable.
        request = DiscordRequest()

        # Set the headers.
        request.set_headers(headers)

        # Return the response.
        return request.send_request(url)

    def get_last_message_server(self, server, channel):
        """
        Use the official Discord API to retrieve the last publicly viewable message in a channel.
        :param server: The ID for the server that we're wanting to scrape from.
        :param channel: The ID for the channel that we're wanting to scrape from.
        """

        # Generate a valid URL to the documented API function for retrieving channel messages
        # (we don't care about the 100 message limit this time).
        last_message = 'https://discord.com/api/{0}/channels/{1}/messages?limit=2'.format(
            self.api_version, channel)

        headers = self.headers["user"]
        # Update the HTTP request headers to set the referer to the current server channel URL.
        headers.update(
            {'Referer': 'https://discord.com/channels/{0}/{1}'.format(server, channel)})

        try:
            # Execute the network query to retrieve the JSON data.
            response = self.request_data(last_message, headers)

            # If we returned nothing then return nothing.
            if response is None:
                return None

            # Read the response data and convert it into a dictionary object.
            data = json.loads(response.read())

            return data[-1]
        except Exception as ex:
            error(ex)

    def filter_message_from_admins(self, message):
        """
        return the same message, if its from admin or else it returns None
        :param message: object or list<object> of discord message
        """

        def is_message_from_admin(single_message):
            author = single_message['author']['id']
            if author in self.author_ids:
                return True
            else:
                return False

        if isinstance(message, list):
            filtered_messages = []
            for msg in message:
                if is_message_from_admin(msg):
                    filtered_messages.append(msg)

            return None if (len(filtered_messages) == 0) else filtered_messages

        if is_message_from_admin(message):
            return message
        else:
            return None

    @staticmethod
    def match_data_using_template(template, message):
        pattern = re.escape(template)
        pattern = re.sub(r'\\\$(\w+)', r'(?P<\1>.*)', pattern)
        match = re.match(pattern, message)
        return match.groupdict()

    def parse_signal_calls(self, message, author_id):
        """
        Parse a message with the configured template against an admin id
        :param author_id: parse message only sent from an author_id
        :param message: a message to be parsed
        :return: parsed json
        """

        if author_id not in self.templates.keys():
            return None

        # Supporting multiple templates, as admin/author can send a message in different formats.
        templates = self.templates[author_id]
        parsed_message = None
        for template in templates:
            try:
                parsed_message = self.match_data_using_template(template, message)
                break
            except Exception as e:
                warn(
                    f'Template: {json.dumps(template)} doesn\'t work for message: {json.dumps(message)}; error: {e}')

        if not parsed_message:
            raise Exception(
                f'No template matched for message: {json.dumps(message)}')

        return parsed_message

    def send_message_to_stat_server(self, title, description):

        channel = self.stats_server['channelId']
        server = self.stats_server['guildId']

        # Generate a valid URL to the documented API function for retrieving channel messages
        # (we don't care about the 100 message limit this time).
        post_message_url = 'https://discord.com/api/{0}/channels/{1}/messages'.format(
            self.api_version, channel)

        headers = self.headers["bot"]
        # Update the HTTP request headers to set the referer to the current server channel URL.
        headers.update(
            {'Referer': 'https://discord.com/channels/{0}/{1}'.format(server, channel)})

        try:
            message_content = {
                "tts": False,
                "embeds": [{
                    "title": title,
                    "description": description
                }]
            }
            response = requests.post(
                post_message_url, json=message_content, headers=headers)

            # If we returned nothing then return nothing.
            if response is None:
                return None

            return response.text
        except Exception as ex:
            error(ex)
