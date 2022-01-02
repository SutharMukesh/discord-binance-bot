from sys import stderr, exit
from signal import SIGINT, signal


def sigint_event(sig, frame):
    print(f'You pressed CTRL + C, Signal: {sig}, frame: {frame}')
    exit(0)


signal(SIGINT, sigint_event)


def error(message):
    """
    Throw an error message and then halt the script.

    :param message: A string that will be printed out to STDERR before exiting the script.
    """

    # Append our message with a newline character.
    stderr.write('[ERROR]: {0}\n'.format(message))


def warn(message):
    """
    Throw a warning message without halting the script.

    :param message: A string that will be printed out to STDERR.
    """

    # Append our message with a newline character.
    stderr.write('[WARN] {0}\n'.format(message))
