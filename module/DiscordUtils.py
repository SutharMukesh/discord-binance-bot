import json
import re
import requests

from .SystemUtils import error, warn


class DiscordUtils(object):
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

        # Create some class variables to store the configuration file data. The backend Discord API version which
        # denotes which API functions are available for use and which are deprecated.
        self.api_version = api_version

        self.signal_servers = config['discord']['signal_servers'] if len(
            config['discord']['signal_servers']) > 0 else []

        self.bot_stats_server = config['discord']['bot_stats_server']

    def get_last_message_server(self, server_id, channel_id, headers):
        """
        Use the official Discord API to retrieve the last publicly viewable message in a channel.
        :param server_id: The ID for the server that we're wanting to scrape from.
        :param channel_id: The ID for the channel that we're wanting to scrape from.
        :param headers: required Headers to make a call with discord
        """

        # Generate a valid URL to the documented API function for retrieving channel messages
        # (we don't care about the 100 message limit this time).
        last_message = 'https://discord.com/api/{0}/channels/{1}/messages?limit=2'.format(
            self.api_version, channel_id)

        if not headers:
            raise Exception(f'Cannot get last message from server {server_id} '
                            f'and channel {channel_id} as no headers were found!')

        # Update the HTTP request headers to set the referer to the current server channel URL.
        headers.update(
            {'Referer': 'https://discord.com/channels/{0}/{1}'.format(server_id, channel_id)})

        # Execute the network query to retrieve the JSON data.

        response = requests.get(
            last_message, headers=headers)

        # If we returned nothing then return nothing.
        if response is None:
            return None

        # Read the response text and convert it into a dictionary object.
        data = json.loads(response.text)

        return data[-1]

    @staticmethod
    def filter_message_from_admins(message, author_ids):
        """
        return the same message, if its from admin or else it returns None
        :param message: object or list<object> of discord message
        :param author_ids: list<object> of author objects.
        """

        def is_message_from_admin(single_message):
            author = single_message['author']['id']

            for author_obj in author_ids:
                author_id = author_obj['author_id']
                if author == author_id:
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

    def parse_signal_calls(self, message, message_templates):
        """
        Parse a message with the configured template against an admin id
        :param message: a message to be parsed
        :param message_templates: Supporting multiple templates, as admin/author can send a message in different formats.
        :return: parsed json
        """
        parsed_message = None
        for template in message_templates:
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
        if not self.bot_stats_server['enable']:
            return

        channel = self.bot_stats_server['channel_id']
        server = self.bot_stats_server['server_id']

        # Generate a valid URL to the documented API function for retrieving channel messages
        # (we don't care about the 100 message limit this time).
        post_message_url = 'https://discord.com/api/{0}/channels/{1}/messages'.format(
            self.api_version, channel)

        headers = self.bot_stats_server["headers"]
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
