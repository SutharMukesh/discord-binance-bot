from sys import stderr, exit
from signal import SIGINT, signal

from .DiscordUtils import DiscordUtils
from .CommonUtils import get_config_file
import time

import logging
from logging.handlers import TimedRotatingFileHandler


class Logger(object):
    def __init__(self, config):
        # format the log entries
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

        handler = TimedRotatingFileHandler('./logs/script.log', when='midnight')
        handler.setFormatter(formatter)
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        if not config:
            config = get_config_file('config.json')
        self.discord_utils = DiscordUtils(config, self.logger)

    def error(self, title, description):
        """
        Log an error message to file and the discord bot server.
        """

        self.logger.error(f'[ERROR]: {title}\n{description}')
        time.sleep(0.5)
        self.discord_utils.send_message_to_stat_server(f'⛔️ {title}', description)
        print(f'[ERROR]: {title} - {description}\n')

    def warn(self, title, description):
        """
        Log a warning message to file and the discord bot server.
        """

        self.logger.warning(f'[WARN] {title}\n{description}')
        time.sleep(0.5)
        self.discord_utils.send_message_to_stat_server(f'⚠️ {title}', description)
        print(f'[WARN] {title} - {description}\n')

    def info(self, title, description):
        """
        log a message to file and discord bot server.
        """

        self.logger.info(f'[INFO] {title}\n{description}')
        time.sleep(0.5)
        self.discord_utils.send_message_to_stat_server(f'ℹ️ {title}', description)
        print(f'[INFO] {title} - {description}\n')


def sigint_event(self, sig, frame):
    print(f'You pressed CTRL + C, Signal: {sig}, frame: {frame}')
    exit(0)


signal(SIGINT, sigint_event)
