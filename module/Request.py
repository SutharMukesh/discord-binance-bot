from http.client import HTTPSConnection
from sys import stderr
from time import sleep
from json import loads


def warn(message):
    """
    Throw a warning message without halting the script.
    :param message: A string that will be printed out to STDERR.
    """

    # Append our message with a newline character.
    stderr.write('[WARN] {0}\n'.format(message))


class DiscordRequest(object):
    """
    The Python 3 compatible version of the DiscordRequest class.
    """

    def __init__(self):
        """
        The class constructor.
        """

        # Create a blank dictionary to serve as our request header class variable.
        self.headers = {}

    def set_headers(self, headers):
        """
        Set the request headers for this request.
        :param headers: The dictionary that stores our header names and values.
        """

        # Create and set the class variable to store our headers.
        self.headers = headers

    def send_request(self, url):
        """
        Send a request to the target URL and return the response data.
        :param url: The URL to the target that we're wanting to grab data from.
        """

        # Split the URL into parts.
        url_parts = url.split('/')

        # Grab the URL path from the url_parts.
        urlpath = '/{0}'.format('/'.join(url_parts[3:]))

        # Create a reference to the HTTPSConnection class.
        connection = HTTPSConnection(url_parts[2], 443)

        # Request the data from the connection.
        connection.request('GET', urlpath, headers=self.headers)

        # Retrieve the response from the request.
        response = connection.getresponse()

        for header in response.getheaders():
            if header[0] == 'Retry-After':
                print(header)

        # Return the response if the connection was successful.
        if 199 < response.status < 300:
            return response

        # Recursively run this function if we hit a redirect page.
        elif 299 < response.status < 400:

            # Grab the URL that we're redirecting to.
            url = response.getheader('Location')

            # Grab the domain name for the redirected location.
            domain = url.split('/')[2].split(':')[0]

            # If the domain is a part of Discord then re-run this function.
            if domain in ['discordapp.com', 'discord.com']:
                self.send_request(url)

            # Throw a warning message to acknowledge an untrusted redirect.
            warn('Ignored unsafe redirect to {0}.'.format(url))

        # Otherwise, throw a warning message to acknowledge a failed connection.
        else:
            warn('HTTP {0} from {1}.'.format(response.status, url))

        # Handle HTTP 429 Too Many Requests
        if response.status == 429:
            retry_after = loads(response.read()).get('retry_after', None)

            if retry_after:
                # Sleep for 1 extra second as buffer
                sleep(1 + retry_after)
                return self.send_request(url)

        # Return nothing to signify a failed request.
        return None
